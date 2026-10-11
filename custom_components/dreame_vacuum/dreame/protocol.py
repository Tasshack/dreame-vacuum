import logging
import random
import hashlib
import json
import base64
import hmac
import requests
import zlib
import queue
import copy
import os
import socket
import struct
import errno
import gzip
from threading import Thread, Lock
from time import sleep
import time, locale
import paho.mqtt
from paho.mqtt.client import Client
from typing import Any, Dict, Final, Optional, Tuple
from Crypto.Cipher import ARC4, AES
from Crypto.Util.Padding import pad
from cryptography.hazmat.primitives.asymmetric import x25519, ec
from cryptography.hazmat.primitives.ciphers.aead import AESGCM, ChaCha20Poly1305
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from miio.miioprotocol import MiIOProtocol
from urllib.parse import urlparse, parse_qs, quote, urlsplit
import re

from .exceptions import DeviceException
from .types import RestartableTimer

DREAME_STRINGS: Final = (
    "H4sIAAAAAAAC/41U23LiOBD9FSpVQ81uLcYy4eJN8UDCMDCzCRtuAbamKCEJW4ksOZaAwNevWjYJzFN4MH36pu6jbv135XFlPJoxnDDPMBJf/XWFakGjaf9HnYNY3H3ZJOOfafPL5NWqus5xNU5wZmKVsGrgIS8sfeX/xkqymxIfjkuo5V176KY0Jliwas3z/T9s5C3WnJSW/R9i8YTEPOjtSX/xNnzpPc6TUfDYTztT1FvOZDwcdqO2DfDdzwraYLPVVkiwNiybcmrlNZe0qxLMpQVpplKWmYMVbTcDsJdTrPVeZRRSVfP+Knhr4qpyX6NeGIRiQpjWqxPM2CZjOn7H7C3lVrHiuTHiCgTDJJZm5QopUm81yyr28LwEQFBhjt4bKCwUGwyRbMcJs4Lg2swCsMuNyg3Dyd0gB8qQQkpxhhNd+DscQXSiKBOuOmLb1R8l2dMqRCXAIJP0TiUJPlW04QJC4U9a14JCiDWHFGBsj1AZEBox03WFdvOq9W/4jFqLpkBDJ2ISCgSdyvgRm3PaKo42oqSFplKch9NUcOIcq8/aeaer4nS1l0JhOs1Erhhqjeil1g1xona4AiPs5V3fW3w2qcgLvOvPTKpLZjK13dlezvJNctVFSv9zw18FpivrjNOIVWEEqo5WDjz28rv49m3yrI/bP+eD+lH29QB65dGbSF73y19N9bSc9qCne+oHz4fR63G7QY+3448LSJi7DrJr49WHNhPkA6QamJdsD9fII3clPGF2PJMU1t4P/IZfczuHrFSv13LRquo1mE/1EhuTVm2DgQemriXC9oj80ldqxb+5gmbXT2GwmIUx6Xcas2f6z9p/UJMeuaYv8e1jrddfRG1YyhuC5Q7rPtaxg3u2jsQ72nHN7QQO6EkTZbByMC7t02qXNbF738ZClFOBzUZlSbvz0B0NB92yc7TLrbbSlIFxmHPIU3aq7OBkgWX0W/KLF+DTJ1xEQUba/7Gj86UgIifiYX7r33+fNai/R5PjqH//PWzgvSOiYDG8ILFQNi6U9dOTiNw3Vu4dOK2S3eXILaGx3eiNHV4miaJcRmdOlyrJSLGb8A6ml+ZNgDBtXrN6iBsIoTVDtEX8ALFGfd0KEQlwYNWNJl6vW6TO/GbI/JAFpIVbtVoIc5e8GnP163+JjsKlZAYAAA=="
)

_LOGGER = logging.getLogger(__name__)


def _run_callback(callback, response) -> None:
    """Run an async request callback without letting it kill the worker thread."""
    if not callback:
        return
    try:
        callback(response)
    except DeviceException as ex:
        _LOGGER.debug("Async request callback failed: %s", ex)
    except Exception:
        _LOGGER.warning("Async request callback failed", exc_info=True)


class DreameVacuumDeviceProtocol(MiIOProtocol):
    def __init__(self, ip: str, token: str) -> None:
        super().__init__(ip, token, 0, 0, True, 2)
        self.ip = None
        self.token = None
        self._queue = queue.Queue()
        self._thread = None
        self.set_credentials(ip, token)

    def _api_task(self):
        while True:
            item = self._queue.get()
            if len(item) == 0:
                self._queue.task_done()
                self._thread = None
                return
            try:
                response = self.send(item[1], item[2], item[3])
            except Exception as ex:
                _LOGGER.warning("Async request %s failed: %s", item[1], ex)
                response = None
            _run_callback(item[0], response)
            self._queue.task_done()

    def send_async(self, callback, command, parameters=None, retry_count=2):
        if self._thread is None:
            self._thread = Thread(target=self._api_task, daemon=True)
            self._thread.start()

        self._queue.put((callback, command, parameters, retry_count))

    def set_credentials(self, ip: str, token: str):
        if self.ip != ip or self.token != token:
            self.ip = ip
            self.port = 54321
            self.token = token

            if token is None or token == "":
                token = 32 * "0"
            self.token = bytes.fromhex(token)
            self._discovered = False

    @property
    def connected(self) -> bool:
        return self._discovered

    def disconnect(self):
        self._discovered = False
        if self._thread:
            self._queue.put([])


class DreameVacuumDreameHomeCloudProtocol:
    class DreameTLSSocket:
        @staticmethod
        def _expand_label(secret, label, context, length, h):
            lbl = b"tls13 " + label
            info = struct.pack("!H", length) + bytes([len(lbl)]) + lbl + bytes([len(context)]) + context
            out = b""
            t = b""
            i = 1
            while len(out) < length:
                t = hmac.new(secret, t + info + bytes([i]), h).digest()
                out += t
                i += 1
            return out[:length]

        @staticmethod
        def _prf(secret, label, seed, length, h):
            seed = label + seed
            a = seed
            out = b""
            while len(out) < length:
                a = hmac.new(secret, a, h).digest()
                out += hmac.new(secret, a + seed, h).digest()
            return out[:length]

        def __init__(self, host, port, server_name, timeout, strings):
            self._host = host
            self._port = port
            self._sni = server_name
            self._timeout = timeout
            self._strings = strings
            self._sock = None
            self._rbuf = b""
            self._appbuf = b""
            self._tls12 = False

        def __getattr__(self, name):
            return getattr(self._sock, name)

        def _read_record(self):
            while len(self._rbuf) < 5:
                d = self._sock.recv(65536)
                if not d:
                    raise ConnectionError("connection closed during handshake")
                self._rbuf += d
            ln = (self._rbuf[3] << 8) | self._rbuf[4]
            while len(self._rbuf) < 5 + ln:
                d = self._sock.recv(65536)
                if not d:
                    raise ConnectionError("connection closed during handshake")
                self._rbuf += d
            typ = self._rbuf[0]
            body = self._rbuf[5 : 5 + ln]
            self._rbuf = self._rbuf[5 + ln :]
            return typ, body

        def connect(self):
            self._sock = socket.create_connection((self._host, self._port), timeout=self._timeout)
            self._sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            try:
                self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                for opt, val in (("TCP_KEEPIDLE", 60), ("TCP_KEEPINTVL", 15), ("TCP_KEEPCNT", 4)):
                    if hasattr(socket, opt):
                        self._sock.setsockopt(socket.IPPROTO_TCP, getattr(socket, opt), val)
            except OSError:
                pass
            priv = x25519.X25519PrivateKey.generate()
            pub = priv.public_key().public_bytes_raw()
            ext = b""
            sni = self._sni.encode("idna") if self._sni else b""
            sni_list = struct.pack("!BH", 0, len(sni)) + sni
            ext += struct.pack("!HH", 0, len(sni_list) + 2) + struct.pack("!H", len(sni_list)) + sni_list
            ext += struct.pack("!HH", 23, 0)
            ext += struct.pack("!HH", 65281, 1) + b"\x00"
            g = b"".join(struct.pack("!H", x) for x in [0x001D, 0x0017, 0x0018])
            ext += struct.pack("!HH", 10, len(g) + 2) + struct.pack("!H", len(g)) + g
            ext += struct.pack("!HH", 11, 2) + b"\x01\x00"
            ext += struct.pack("!HH", 35, 0)
            sa = b"".join(
                struct.pack("!H", x) for x in [0x0403, 0x0804, 0x0401, 0x0503, 0x0805, 0x0501, 0x0806, 0x0601, 0x0201]
            )
            ext += struct.pack("!HH", 13, len(sa) + 2) + struct.pack("!H", len(sa)) + sa
            ks = struct.pack("!HH", 0x001D, len(pub)) + pub
            ext += struct.pack("!HH", 51, len(ks) + 2) + struct.pack("!H", len(ks)) + ks
            ext += struct.pack("!HH", 45, 2) + b"\x01\x01"
            ext += struct.pack("!HH", 43, 5) + b"\x04\x03\x04\x03\x03"
            chbody = b"\x03\x03" + os.urandom(32) + bytes([32]) + os.urandom(32)
            cs = b"".join(
                struct.pack("!H", c)
                for c in [
                    0x1303,
                    0x1301,
                    0x1302,
                    0xCCA9,
                    0xCCA8,
                    0xC02B,
                    0xC02F,
                    0xC02C,
                    0xC030,
                    0xC009,
                    0xC013,
                    0xC00A,
                    0xC014,
                    0x009C,
                    0x009D,
                    0x002F,
                    0x0035,
                ]
            )
            chbody += struct.pack("!H", len(cs)) + cs + b"\x01\x00"
            msg_len = 4 + len(chbody) + 2 + len(ext)
            if 256 <= msg_len < 512:
                need = 512 - msg_len - 4
                if need < 0:
                    need = 0
                ext += struct.pack("!HH", 21, need) + b"\x00" * need
            chbody += struct.pack("!H", len(ext)) + ext
            ch = struct.pack("!B", 1) + struct.pack("!I", len(chbody))[1:] + chbody
            self._client_random = ch[6:38]
            transcript = ch
            self._sock.sendall(b"\x16\x03\x01" + struct.pack("!H", len(ch)) + ch)

            typ, sh = self._read_record()
            while typ == 20:
                typ, sh = self._read_record()
            if typ != 22 or not sh or sh[0] != 2:
                raise ConnectionError("expected ServerHello")
            i = 6 + 32
            sidlen = sh[i]
            i += 1 + sidlen
            self._cipher = (sh[i] << 8) | sh[i + 1]
            i += 3
            extlen = (sh[i] << 8) | sh[i + 1]
            i += 2
            end = i + extlen
            srv_pub = None
            self._ems = False
            is_hrr = sh[6:38] == bytes.fromhex(self._strings[89])
            while i + 4 <= end:
                et = (sh[i] << 8) | sh[i + 1]
                el = (sh[i + 2] << 8) | sh[i + 3]
                ed = sh[i + 4 : i + 4 + el]
                i += 4 + el
                if et == 51 and len(ed) >= 4:
                    kl = (ed[2] << 8) | ed[3]
                    srv_pub = ed[4 : 4 + kl]
                elif et == 23:
                    self._ems = True
            if is_hrr:
                raise ConnectionError("server requested retry")
            if srv_pub is None:
                return self._handshake_tls12(transcript, sh)

            self._h = hashlib.sha384 if self._cipher == 0x1302 else hashlib.sha256
            self._hlen = 48 if self._cipher == 0x1302 else 32
            self._keylen = 16 if self._cipher == 0x1301 else 32
            h, hlen = self._h, self._hlen
            transcript += sh
            shared = priv.exchange(x25519.X25519PublicKey.from_public_bytes(srv_pub))
            zero = b"\x00" * hlen
            early = hmac.new(zero, zero, h).digest()
            derived = self._expand_label(early, b"derived", h(b"").digest(), hlen, h)
            hs_secret = hmac.new(derived, shared, h).digest()
            c_hs = self._expand_label(hs_secret, b"c hs traffic", h(transcript).digest(), hlen, h)
            s_hs = self._expand_label(hs_secret, b"s hs traffic", h(transcript).digest(), hlen, h)
            c_hs_key = self._expand_label(c_hs, b"key", b"", self._keylen, h)
            c_hs_iv = self._expand_label(c_hs, b"iv", b"", 12, h)
            s_hs_key = self._expand_label(s_hs, b"key", b"", self._keylen, h)
            s_hs_iv = self._expand_label(s_hs, b"iv", b"", 12, h)

            sseq = 0
            buf = b""
            got_fin = False
            while not got_fin:
                typ, body = self._read_record()
                if typ == 20:
                    continue
                if typ == 21:
                    raise ConnectionError("alert during handshake")
                aad = bytes([typ]) + b"\x03\x03" + struct.pack("!H", len(body))
                nonce = bytes(a ^ b for a, b in zip(s_hs_iv, b"\x00\x00\x00\x00" + struct.pack("!Q", sseq)))
                cipher = ChaCha20Poly1305(s_hs_key) if self._cipher == 0x1303 else AESGCM(s_hs_key)
                pt = cipher.decrypt(nonce, body, aad)
                sseq += 1
                pt = pt.rstrip(b"\x00")
                if not pt or pt[-1] != 22:
                    continue
                buf += pt[:-1]
                while len(buf) >= 4:
                    mlen = (buf[1] << 16) | (buf[2] << 8) | buf[3]
                    if len(buf) < 4 + mlen:
                        break
                    msg = buf[: 4 + mlen]
                    buf = buf[4 + mlen :]
                    transcript += msg
                    if msg[0] == 20:
                        got_fin = True
                        break

            fk = self._expand_label(c_hs, b"finished", b"", hlen, h)
            vd = hmac.new(fk, h(transcript).digest(), h).digest()
            fin = struct.pack("!B", 20) + struct.pack("!I", len(vd))[1:] + vd
            self._sock.sendall(b"\x14\x03\x03\x00\x01\x01")
            inner = fin + b"\x16"
            aad = b"\x17\x03\x03" + struct.pack("!H", len(inner) + 16)
            nonce = bytes(a ^ b for a, b in zip(c_hs_iv, b"\x00\x00\x00\x00" + struct.pack("!Q", 0)))
            cipher = ChaCha20Poly1305(c_hs_key) if self._cipher == 0x1303 else AESGCM(c_hs_key)
            ct = cipher.encrypt(nonce, inner, aad)
            self._sock.sendall(b"\x17\x03\x03" + struct.pack("!H", len(ct)) + ct)

            derived2 = self._expand_label(hs_secret, b"derived", h(b"").digest(), hlen, h)
            master = hmac.new(derived2, zero, h).digest()
            self._c_ap = self._expand_label(master, b"c ap traffic", h(transcript).digest(), hlen, h)
            self._s_ap = self._expand_label(master, b"s ap traffic", h(transcript).digest(), hlen, h)
            self._c_key = self._expand_label(self._c_ap, b"key", b"", self._keylen, h)
            self._c_iv = self._expand_label(self._c_ap, b"iv", b"", 12, h)
            self._s_key = self._expand_label(self._s_ap, b"key", b"", self._keylen, h)
            self._s_iv = self._expand_label(self._s_ap, b"iv", b"", 12, h)
            self._cseq = 0
            self._sseq = 0
            return self

        def _handshake_tls12(self, transcript, sh):
            self._tls12 = True
            server_random = sh[6:38]
            ske = None
            got_shd = False
            buf = sh
            while not got_shd:
                while len(buf) >= 4:
                    mlen = (buf[1] << 16) | (buf[2] << 8) | buf[3]
                    if len(buf) < 4 + mlen:
                        break
                    msg = buf[: 4 + mlen]
                    buf = buf[4 + mlen :]
                    transcript += msg
                    if msg[0] == 12:
                        ske = msg[4 : 4 + mlen]
                    elif msg[0] == 14:
                        got_shd = True
                        break
                if got_shd:
                    break
                typ, body = self._read_record()
                if typ == 21:
                    raise ConnectionError("alert during handshake")
                if typ != 22:
                    continue
                buf += body
            if ske is None:
                raise ConnectionError("no ServerKeyExchange")
            named_curve = (ske[1] << 8) | ske[2]
            pk_len = ske[3]
            server_pub = ske[4 : 4 + pk_len]
            if named_curve == 0x001D:
                my = x25519.X25519PrivateKey.generate()
                my_pub = my.public_key().public_bytes_raw()
                shared = my.exchange(x25519.X25519PublicKey.from_public_bytes(server_pub))
            else:
                curve = {0x0017: ec.SECP256R1(), 0x0018: ec.SECP384R1(), 0x0019: ec.SECP521R1()}[named_curve]
                my = ec.generate_private_key(curve)
                my_pub = my.public_key().public_bytes(Encoding.X962, PublicFormat.UncompressedPoint)
                shared = my.exchange(ec.ECDH(), ec.EllipticCurvePublicKey.from_encoded_point(curve, server_pub))
            self._h = (
                hashlib.sha384 if self._cipher in (0xC030, 0xC02C, 0xC024, 0xC028, 0x009F, 0x006B) else hashlib.sha256
            )
            ph = self._h
            self._keylen = 32 if self._cipher in (0xC030, 0xC02C, 0x009D, 0xCCA8, 0xCCA9, 0x1302, 0x1303) else 16
            keylen = self._keylen
            cke_body = bytes([len(my_pub)]) + my_pub
            cke = bytes([16]) + struct.pack("!I", len(cke_body))[1:] + cke_body
            transcript += cke
            if self._ems:
                master = self._prf(shared, b"extended master secret", ph(transcript).digest(), 48, ph)
            else:
                master = self._prf(shared, b"master secret", self._client_random + server_random, 48, ph)
            ivlen = 12 if self._cipher in (0xCCA8, 0xCCA9) else 4
            kb = self._prf(master, b"key expansion", server_random + self._client_random, 2 * keylen + 2 * ivlen, ph)
            self._c_key = kb[0:keylen]
            self._s_key = kb[keylen : 2 * keylen]
            self._c_iv = kb[2 * keylen : 2 * keylen + ivlen]
            self._s_iv = kb[2 * keylen + ivlen : 2 * keylen + 2 * ivlen]
            self._cseq = 0
            self._sseq = 0
            self._sock.sendall(b"\x16\x03\x03" + struct.pack("!H", len(cke)) + cke)
            self._sock.sendall(b"\x14\x03\x03\x00\x01\x01")
            vd = self._prf(master, b"client finished", ph(transcript).digest(), 12, ph)
            fin = bytes([20]) + struct.pack("!I", len(vd))[1:] + vd
            enc = self._encrypt12(22, fin)
            self._sock.sendall(b"\x16\x03\x03" + struct.pack("!H", len(enc)) + enc)
            ccs_seen = False
            while True:
                typ, body = self._read_record()
                if typ == 20:
                    ccs_seen = True
                    continue
                if typ == 21:
                    raise ConnectionError("alert")
                if typ == 22:
                    if ccs_seen:
                        self._decrypt12(22, body)
                        break
                    continue
            return self

        def _encrypt12(self, content_type, plaintext):
            chacha = self._cipher in (0xCCA8, 0xCCA9)
            cipher = ChaCha20Poly1305(self._c_key) if chacha else AESGCM(self._c_key)
            aad = (
                struct.pack("!Q", self._cseq) + bytes([content_type]) + b"\x03\x03" + struct.pack("!H", len(plaintext))
            )
            if chacha:
                nonce = bytes(a ^ b for a, b in zip(self._c_iv, b"\x00\x00\x00\x00" + struct.pack("!Q", self._cseq)))
                ct = cipher.encrypt(nonce, plaintext, aad)
                self._cseq += 1
                return ct
            explicit = struct.pack("!Q", self._cseq)
            ct = cipher.encrypt(self._c_iv + explicit, plaintext, aad)
            self._cseq += 1
            return explicit + ct

        def _decrypt12(self, content_type, body):
            chacha = self._cipher in (0xCCA8, 0xCCA9)
            cipher = ChaCha20Poly1305(self._s_key) if chacha else AESGCM(self._s_key)
            if chacha:
                nonce = bytes(a ^ b for a, b in zip(self._s_iv, b"\x00\x00\x00\x00" + struct.pack("!Q", self._sseq)))
                aad = (
                    struct.pack("!Q", self._sseq)
                    + bytes([content_type])
                    + b"\x03\x03"
                    + struct.pack("!H", len(body) - 16)
                )
                pt = cipher.decrypt(nonce, body, aad)
                self._sseq += 1
                return pt
            explicit = body[:8]
            ct = body[8:]
            aad = struct.pack("!Q", self._sseq) + bytes([content_type]) + b"\x03\x03" + struct.pack("!H", len(ct) - 16)
            pt = cipher.decrypt(self._s_iv + explicit, ct, aad)
            self._sseq += 1
            return pt

        def send(self, data):
            data = bytes(data)
            total = 0
            while data:
                chunk = data[:16384]
                data = data[16384:]
                if self._tls12:
                    enc = self._encrypt12(23, chunk)
                else:
                    inner = chunk + b"\x17"
                    aad = b"\x17\x03\x03" + struct.pack("!H", len(inner) + 16)
                    nonce = bytes(
                        a ^ b for a, b in zip(self._c_iv, b"\x00\x00\x00\x00" + struct.pack("!Q", self._cseq))
                    )
                    cipher = ChaCha20Poly1305(self._c_key) if self._cipher == 0x1303 else AESGCM(self._c_key)
                    enc = cipher.encrypt(nonce, inner, aad)
                    self._cseq += 1
                self._sock.sendall(b"\x17\x03\x03" + struct.pack("!H", len(enc)) + enc)
                total += len(chunk)
            return total

        sendall = send

        def _fill_once(self):
            try:
                d = self._sock.recv(65536)
            except BlockingIOError:
                return False
            except OSError as ex:
                if ex.errno in (errno.EAGAIN, errno.EWOULDBLOCK):
                    return False
                raise
            if not d:
                raise ConnectionError("connection closed")
            self._rbuf += d
            processed = False
            while len(self._rbuf) >= 5:
                ln = (self._rbuf[3] << 8) | self._rbuf[4]
                if len(self._rbuf) < 5 + ln:
                    break
                typ = self._rbuf[0]
                body = self._rbuf[5 : 5 + ln]
                self._rbuf = self._rbuf[5 + ln :]
                processed = True
                if typ == 20:
                    continue
                if typ == 21:
                    raise ConnectionError("tls alert")
                if self._tls12:
                    pt = self._decrypt12(typ, body)
                    if typ == 23:
                        self._appbuf += pt
                    continue
                aad = bytes([typ]) + b"\x03\x03" + struct.pack("!H", len(body))
                nonce = bytes(a ^ b for a, b in zip(self._s_iv, b"\x00\x00\x00\x00" + struct.pack("!Q", self._sseq)))
                cipher = ChaCha20Poly1305(self._s_key) if self._cipher == 0x1303 else AESGCM(self._s_key)
                pt = cipher.decrypt(nonce, body, aad)
                self._sseq += 1
                pt = pt.rstrip(b"\x00")
                if not pt:
                    continue
                it = pt[-1]
                payload = pt[:-1]
                if it == 23:
                    self._appbuf += payload
                elif it == 22:
                    m = payload
                    while len(m) >= 4:
                        mt = m[0]
                        mlen = (m[1] << 16) | (m[2] << 8) | m[3]
                        mbody = m[4 : 4 + mlen]
                        m = m[4 + mlen :]
                        if mt == 0x18:
                            request = mbody[0] if mbody else 0
                            self._s_ap = self._expand_label(self._s_ap, b"traffic upd", b"", self._hlen, self._h)
                            self._s_key = self._expand_label(self._s_ap, b"key", b"", self._keylen, self._h)
                            self._s_iv = self._expand_label(self._s_ap, b"iv", b"", 12, self._h)
                            self._sseq = 0
                            if request == 1:
                                upd = b"\x18\x00\x00\x01\x00" + b"\x16"
                                uaad = b"\x17\x03\x03" + struct.pack("!H", len(upd) + 16)
                                unonce = bytes(
                                    a ^ b
                                    for a, b in zip(self._c_iv, b"\x00\x00\x00\x00" + struct.pack("!Q", self._cseq))
                                )
                                ucipher = (
                                    ChaCha20Poly1305(self._c_key) if self._cipher == 0x1303 else AESGCM(self._c_key)
                                )
                                uct = ucipher.encrypt(unonce, upd, uaad)
                                self._cseq += 1
                                self._sock.sendall(b"\x17\x03\x03" + struct.pack("!H", len(uct)) + uct)
                                self._c_ap = self._expand_label(self._c_ap, b"traffic upd", b"", self._hlen, self._h)
                                self._c_key = self._expand_label(self._c_ap, b"key", b"", self._keylen, self._h)
                                self._c_iv = self._expand_label(self._c_ap, b"iv", b"", 12, self._h)
                                self._cseq = 0
                elif it == 21:
                    raise ConnectionError("tls alert")
            return processed

        def recv(self, n=4096):
            while not self._appbuf:
                got = self._fill_once()
                if not got:
                    if self._sock.gettimeout() == 0.0:
                        raise BlockingIOError(errno.EAGAIN, "no data")
                    continue
            r = self._appbuf[:n]
            self._appbuf = self._appbuf[n:]
            return r

        def pending(self):
            return len(self._appbuf)

    class DreameClient(Client):
        def _create_socket_connection(self):
            timeout = getattr(self, "_connect_timeout", 15) or 15
            return DreameVacuumDreameHomeCloudProtocol.DreameTLSSocket(
                self._host, int(self._port), self._host, timeout, self._userdata._strings
            ).connect()

        def _packet_queue(self, command, packet, *args, **kwargs):
            if command == 0x10:
                packet = bytearray(packet)
                i = 1
                while packet[i] & 0x80:
                    i += 1
                packet[i + 8] |= 0x08
            return super()._packet_queue(command, packet, *args, **kwargs)

    def __init__(
        self,
        username: str,
        password: str,
        account_type: str = "dreame",
        country: str = "cn",
        auth_key: str = None,
        did: str = None,
    ) -> None:
        self._username = username
        self._password = password
        self._account_type = account_type
        self._country = country
        self._did = did
        self._conns = {}
        self._http_lock = Lock()
        self._queue = queue.Queue()
        self._thread = None
        self._client_queue = queue.Queue()
        self._client_thread = None
        self._id = random.randint(1, 100)
        self._reconnect_timer = None
        self._host = None
        self._model = None
        self._ti = None
        self._fail_count = 0
        self._connected = False
        self._client_connected = False
        self._client_connecting = False
        self._client_established = False
        self._client = None
        self._message_callback = None
        self._connected_callback = None
        self._logged_in = False
        self._auth_failed = False
        self._stream_key = None
        self._client_key = None
        self._secondary_key = auth_key
        self._key_expire = None
        self._key = None
        self._uid = None
        self._uuid = None
        self._domain = None
        self._region = None
        self._lang = None
        self._ccode = None
        self._cid = None
        self._vid = None
        self._au = None
        self._ua = None
        self._vs = hashlib.md5(random.randbytes(16)).hexdigest()
        self._mt = False
        self._strings = None
        self.verification_url = None
        self.captcha_img = None

    def _http(self, method, url, headers, body, timeout):
        s = self._strings
        u = urlsplit(url)
        host, port = u.hostname, (u.port or 443)
        path = u.path or "/"
        if u.query:
            path += "?" + u.query
        host_hdr = host if port == 443 else ("%s:%d" % (host, port))
        data = body.encode("utf-8") if isinstance(body, str) else body
        key = (host, port)
        with self._http_lock:
            for attempt in range(2):
                sock = self._conns.get(key)
                fresh = sock is None
                if fresh:
                    sock = self.DreameTLSSocket(host, port, host, timeout, s).connect()
                    self._conns[key] = sock
                try:
                    sock.settimeout(timeout)
                    lines = ["%s %s HTTP/1.1" % (method, path)]
                    host_done = cl_done = False
                    for k, v in headers.items():
                        if v is None:
                            continue
                        lk = k.lower()
                        if lk == s[83]:
                            host_done = True
                        elif lk == s[84]:
                            cl_done = True
                        lines.append("%s: %s" % (k, v))
                        if lk == s[88] and data is not None and not cl_done:
                            lines.append("%s: %d" % (s[84], len(data)))
                            cl_done = True
                        elif lk == s[43] and not host_done:
                            lines.append("%s: %s" % (s[83], host_hdr))
                            host_done = True
                    if data is not None and not cl_done:
                        lines.append("%s: %d" % (s[84], len(data)))
                    if not host_done:
                        lines.insert(1, "%s: %s" % (s[83], host_hdr))
                    sock.send(("\r\n".join(lines) + "\r\n\r\n").encode("utf-8"))
                    if data:
                        sock.send(data)
                    buf = [b""]

                    def line():
                        while b"\r\n" not in buf[0]:
                            buf[0] += sock.recv(4096)
                        ln, _, rest = buf[0].partition(b"\r\n")
                        buf[0] = rest
                        return ln

                    def readn(n):
                        while len(buf[0]) < n:
                            buf[0] += sock.recv(65536)
                        r = buf[0][:n]
                        buf[0] = buf[0][n:]
                        return r

                    status = int(line().split(b" ", 2)[1])
                    hdrs = {}
                    while True:
                        h = line()
                        if h == b"":
                            break
                        hk, _, hv = h.partition(b":")
                        hdrs[hk.decode("latin1").strip().lower()] = hv.decode("latin1").strip()
                    if "chunked" in hdrs.get(s[85], "").lower():
                        content = b""
                        while True:
                            size = int(line().split(b";")[0], 16)
                            if size == 0:
                                line()
                                break
                            content += readn(size)
                            readn(2)
                    elif s[84] in hdrs:
                        content = readn(int(hdrs[s[84]]))
                    else:
                        content = buf[0]
                        try:
                            while True:
                                content += sock.recv(65536)
                        except (ConnectionError, OSError):
                            pass
                        self._close_conn(key)
                    enc = hdrs.get(s[86], "").lower()
                    if "gzip" in enc:
                        content = gzip.decompress(content)
                    elif "deflate" in enc:
                        content = zlib.decompress(content)
                    if hdrs.get(s[87], "").lower() == "close":
                        self._close_conn(key)
                    return status, content
                except (ConnectionError, OSError) as ex:
                    self._close_conn(key)
                    if isinstance(ex, TimeoutError):
                        raise
                    if fresh:
                        raise
            raise ConnectionError("request failed")

    def _close_conn(self, key):
        sock = self._conns.pop(key, None)
        if sock is not None:
            try:
                sock.close()
            except Exception:
                pass

    def _api_task(self):
        while True:
            item = self._queue.get()
            if len(item) == 0:
                self._queue.task_done()
                self._thread = None
                return
            try:
                response = self._api_call(item[1], item[2], item[3])
            except Exception as ex:
                _LOGGER.warning("Async api call %s failed: %s", item[1], ex)
                response = None
            _run_callback(item[0], response)
            sleep(0.1)
            self._queue.task_done()

    def _api_call_async(self, callback, url, params=None, retry_count=2):
        if self._thread is None:
            self._thread = Thread(target=self._api_task, daemon=True)
            self._thread.start()

        self._queue.put((callback, url, params, retry_count))

    def _api_call(self, url, params=None, retry_count=2, timeout=None):
        if isinstance(params, dict):
            params = self._signed(params)
        return self.request(
            f"{self.get_api_url()}/{url}",
            json.dumps(params, separators=(",", ":")) if params is not None else None,
            retry_count,
            timeout,
        )

    def get_api_url(self) -> str:
        return f"https://{self._country}{self._strings[0]}:{self._strings[1]}"

    def _s(self, base, tag) -> str:
        return hashlib.md5(f"{base}{tag}".encode("utf-8")).hexdigest()

    def _base_headers(self, content_type) -> Dict[str, str]:
        s = self._strings
        kr = self._country == "kr" and self._account_type == "dreame"
        headers = {s[42].lower(): self._ua}
        if not kr:
            meta = f"{s[59]}{self._vid}"
            if self._mt:
                meta += (
                    f"{s[71]}{self._s(self._username, 'c')[:8]}"
                    f"{s[72]}{self._s(self._username, 'w')[:8]}"
                    f"{s[73]}{self._vs}"
                )
            headers[s[58]] = meta
        headers[s[88]] = "gzip"
        if self._region and self._lang and self._ccode and not kr:
            data = pad(f"{self._region}|{self._lang}|{self._ccode}".encode("utf-8"), 16)
            headers[s[60]] = base64.b64encode(AES.new(self._cid, AES.MODE_ECB).encrypt(data)).decode()
        headers[s[44]] = self._ti if self._ti else s[5]
        headers[s[43]] = "Basic " + self._au
        if self._account_type == "mova":
            headers[s[61]] = s[62]
        headers[s[45]] = content_type
        return headers

    def _refresh_expired_key(self) -> None:
        if self._key_expire:
            remaining = self._key_expire - time.time()
            if 0 < remaining <= 600:
                self.login()

    def _auth_failure(self, text) -> int:
        try:
            code = json.loads(text).get("code")
        except:
            return 1
        return 1 if code is None or code == 401 else 2

    def _auth_headers(self, content_type) -> Dict[str, str]:
        headers = self._base_headers(content_type)
        if self._key:
            headers[self._strings[41]] = self._key
        return headers

    def _spliced(self, obj, top) -> str:
        parts = []
        for k in sorted(obj.keys()):
            v = obj[k]
            if isinstance(v, dict):
                inner = self._spliced(v, False)
                parts.append(f"{k}=[{inner}]" if inner else f"{k}=]")
            elif isinstance(v, list):
                if top:
                    parts.append(f"{k}={json.dumps(v, sort_keys=True, separators=(',', ':'), ensure_ascii=False)}")
            elif isinstance(v, bool):
                parts.append(f"{k}={'true' if v else 'false'}")
            elif v is None:
                parts.append(f"{k}=null")
            elif top:
                parts.append(f"{k}={v}")
            else:
                parts.append(f"{k}={json.dumps(v, ensure_ascii=False)}")
        return "&".join(parts)

    def _signed(self, params) -> Dict[str, Any]:
        ms = int(time.time() * 1000)
        base = self._spliced(params, True) + str(ms) + self._cid.decode("utf-8")
        result = dict(params)
        result[self._strings[63]] = hashlib.md5(base.encode("utf-8")).hexdigest()
        result[self._strings[64]] = ms
        return result

    @property
    def device_id(self) -> str:
        return self._did

    @property
    def dreame_cloud(self) -> bool:
        return True

    @property
    def object_name(self) -> str:
        return f"{self._model}/{self._uid}/{str(self._did)}/0"

    @property
    def logged_in(self) -> bool:
        return self._logged_in

    @property
    def auth_failed(self) -> bool:
        return self._auth_failed

    @property
    def connected(self) -> bool:
        return self._connected and self._client_connected

    @property
    def auth_key(self) -> str | None:
        return self._secondary_key

    def _reconnect_timer_cancel(self):
        if self._reconnect_timer is not None:
            self._reconnect_timer.cancel()

    def _reconnect_timer_task(self):
        self._reconnect_timer_cancel()
        if self._client_connecting and self._client_connected:
            self._client_connected = False
            _LOGGER.warning("Device client reconnect failed! Retrying...")

    def _set_client_key(self) -> bool:
        if self._client_key != self._key:
            self._client_key = self._key
            self._client.username_pw_set(self._uuid, self._client_key)
            return True
        return False

    def _client_task(self):
        while True:
            item = self._client_queue.get()
            if len(item) == 0:
                self._client_queue.task_done()
                self._client_thread = None
                return
            try:
                if item[1] != None:
                    item[0](item[1])
                else:
                    item[0]()
            except:
                pass
            self._client_queue.task_done()

    @staticmethod
    def _on_client_connect(client, self, flags, rc):
        self._client_connecting = False
        self._reconnect_timer_cancel()
        if rc == 0:
            self._client_established = True
            if not self._client_connected:
                self._client_connected = True
                _LOGGER.info("Connected to the device client")
            if (
                self._country == "kr"
            ):  ## Devices that are connected to KR server still use SG topic (until Dreame adds KR server to the device firmware)
                self._client.subscribe(f"/{self._strings[6]}/{self._did}/{self._uid}/{self._model}/sg/")
            client.subscribe(f"/{self._strings[6]}/{self._did}/{self._uid}/{self._model}/{self._country}/")
            if self._connected_callback:
                self._client_queue.put((self._connected_callback, None))
        else:
            _LOGGER.warning("Device client connection failed: %s", rc)
            if not self._set_client_key():
                self._client_connected = False

    @staticmethod
    def _on_client_disconnect(client, self, rc):
        if rc != 0 and not self._set_client_key():
            if rc == 5 and self._key_expire:
                if self.login():
                    self._set_client_key()
            if self._client_connected:
                if not self._client_connecting:
                    self._client_connecting = True
                    _LOGGER.info("Device Client disconnected (%s) Reconnecting...", rc)
                self._reconnect_timer_cancel()
                if self._reconnect_timer is None:
                    self._reconnect_timer = RestartableTimer()
                self._reconnect_timer.start(10, self._reconnect_timer_task)

    @staticmethod
    def _on_client_message(client, self, message):
        ## Dirty patch for devices are stuck disconnected, will be refactored later...
        if not self._client_connected or not self._connected:
            self._client_connected = True
            self._connected = True
            if self._connected_callback:
                self._client_queue.put((self._connected_callback, None))

        if self._message_callback:
            try:
                response = json.loads(message.payload.decode("utf-8"))
                if "data" in response and response["data"]:
                    self._client_queue.put((self._message_callback, response["data"]))
            except:
                pass

    def _handle_device_info(self, info):
        self._uid = info[self._strings[7]]
        self._did = info["did"]
        self._model = info[self._strings[30]]
        self._host = info[self._strings[8]]
        prop = info[self._strings[9]]
        if prop and prop != "":
            prop = json.loads(prop)
            if self._strings[10] in prop:
                self._stream_key = prop[self._strings[10]]

    def connect(self, message_callback=None, connected_callback=None):
        if self._logged_in:
            info = self.get_device_info()
            if info:
                if message_callback:
                    self._message_callback = message_callback
                    self._connected_callback = connected_callback
                    if self._client is None:
                        _LOGGER.info("Connecting to the device client")
                        if self._client_thread is None:
                            self._client_thread = Thread(target=self._client_task, daemon=True)
                            self._client_thread.start()

                        try:
                            host = self._host.split(":")
                            if self._country == "kr":  ## KR server url does not resolve by the DNS without this
                                host[0] = host[0].replace("10100", "10000")
                            key = f"{self._strings[47]}{self._s(self._did, self._strings[90] + self._vs)}"
                            if paho.mqtt.__version__[0] > "1":
                                self._client = self.DreameClient(
                                    paho.mqtt.client.CallbackAPIVersion.VERSION1,
                                    key,
                                    clean_session=True,
                                    userdata=self,
                                )
                            else:
                                self._client = self.DreameClient(
                                    key,
                                    clean_session=True,
                                    userdata=self,
                                )
                            self._client.on_connect = DreameVacuumDreameHomeCloudProtocol._on_client_connect
                            self._client.on_disconnect = DreameVacuumDreameHomeCloudProtocol._on_client_disconnect
                            self._client.on_message = DreameVacuumDreameHomeCloudProtocol._on_client_message
                            self._client.reconnect_delay_set(1, 15)
                            self._client_key = None
                            self._set_client_key()
                            self._client.connect_timeout = 10
                            self._client.disable_logger()
                            self._client.connect(host[0], port=int(host[1]), keepalive=60)
                            self._client.loop_start()
                        except Exception as ex:
                            _LOGGER.error("Connecting to the device client failed: %s", ex)
                            # Retry with a new client only if MQTT connected before, never on the first connect
                            if self._client_established:
                                self._client = None
                    elif not self._client_connected:
                        self._set_client_key()
                self._connected = True
                return info
        return None

    def login(self) -> bool:
        for k in list(self._conns):
            self._close_conn(k)

        if self._strings is None:
            self._strings = json.loads(zlib.decompress(base64.b64decode(DREAME_STRINGS), zlib.MAX_WBITS | 32))
            if self._account_type == "mova":
                self._strings[0] = self._strings[50]
                self._strings[3] = self._strings[51]
                self._strings[5] = f"{self._strings[5][:5]}2"
            elif self._account_type == "trouver":
                self._strings[0] = self._strings[52]
                self._strings[3] = self._strings[53]
                self._strings[5] = f"{self._strings[5][:5]}5"

        if self._account_type == "mova":
            self._cid = self._strings[56].encode("utf-8")
            self._vid = self._strings[66]
            self._au = self._strings[70]
            self._ua = self._strings[69]
            self._mt = True
        elif self._account_type == "trouver":
            self._cid = self._strings[57].encode("utf-8")
            self._vid = self._strings[67]
            self._au = self._strings[78]
            self._ua = self._strings[80]
            self._mt = False
        else:
            self._cid = self._strings[55].encode("utf-8")
            self._vid = self._strings[65]
            self._au = self._strings[4].split()[-1]
            self._ua = self._strings[79]
            self._mt = True

        self._auth_failed = False
        used_refresh_token = bool(self._secondary_key)
        try:
            s = self._strings
            if self._secondary_key:
                data = f"{s[77]}{self._secondary_key}"
            else:
                pw = hashlib.md5((self._password + s[2]).encode("utf-8")).hexdigest()
                data = f"{s[74]}{quote(self._username, safe='')}{s[11]}{pw}"
                if self._ccode and self._lang:
                    data = f"{data}{s[75]}{self._ccode}{s[76]}{self._lang}"

            headers = self._base_headers("application/x-www-form-urlencoded")

            status, content = self._http("POST", self.get_api_url() + self._strings[12], headers, data, 10)
            if status == 200:
                data = json.loads(content)
                if self._strings[13] in data:
                    self._key = data.get(self._strings[13])
                    self._secondary_key = data.get(self._strings[14])
                    self._key_expire = time.time() + data.get(self._strings[15])
                    self._uuid = data.get("uid")
                    self._domain = data.get("domain", self._domain)
                    self._region = data.get("region", self._region)
                    self._lang = data.get("lang", self._lang)
                    self._ccode = data.get("country", self._ccode)
                    self._ti = data.get(self._strings[17], self._ti)
                    self._logged_in = True
            elif status in (400, 401, 403):
                if used_refresh_token and self._username and self._password:
                    try:
                        data = json.loads(content)
                        if "error_description" in data and "refresh token" in data["error_description"]:
                            self._secondary_key = None
                            return self.login()
                    except:
                        pass
                self._logged_in = False
                self._auth_failed = True
                _LOGGER.error("Login failed: %s", content.decode("utf-8", "replace"))
            else:
                # Server side or rate limit errors are not credential errors, retry on next update
                self._logged_in = False
                _LOGGER.warning("Login failed (%s): %s", status, content.decode("utf-8", "replace"))
        except TimeoutError:
            self._logged_in = False
            _LOGGER.warning("Login Failed: Read timed out. (read timeout=10)")
        except Exception as ex:
            self._logged_in = False
            _LOGGER.error("Login failed: %s", str(ex))

        if self._logged_in:
            self._fail_count = 0
            self._connected = True
        return self._logged_in

    def get_supported_devices(self, models, host=None, mac=None, device_id=None) -> Any:
        response = self.get_devices()
        devices = []
        unsupported_devices = []
        if response:
            all_devices = list(response["page"]["records"])
            for device in all_devices:
                model = device["model"]
                if model in models:
                    device["name"] = (
                        device["customName"] if device["customName"] else device["deviceInfo"]["displayName"]
                    )
                    devices.append(device)
                    if (mac is not None and str(device.get("mac")).lower() == str(mac).lower()) or (
                        device_id is not None and device.get("did") == device_id
                    ):
                        devices = [device]
                        break
                elif ".vacuum." in model:
                    info = copy.deepcopy(device)
                    ## Redact user/device targeted information so it can be safely shared publicly within an issue
                    for key in [
                        "id",
                        "did",
                        "mac",
                        "masterUid",
                        "masterUid2UUID",
                        "masterName",
                        "customName",
                        "property",
                    ]:
                        if key in info:
                            del info[key]

                    ## First 5/6 characters of the serial number contains actual device firmware model name so it is required
                    if "sn" in info and isinstance(info["sn"], str):
                        sn_str = info["sn"]
                        if len(sn_str) > 6:
                            info["sn"] = sn_str[:6] + "*" * (len(sn_str) - 6)
                        else:
                            del info["sn"]

                    _LOGGER.warning("Unsupported device: %s", info)
                    unsupported_devices.append(device)
        return devices, unsupported_devices

    def get_devices(self) -> Any:
        response = self._api_call(f"{self._strings[18]}/{self._strings[19]}/{self._strings[22]}/{self._strings[23]}")
        if response and "data" in response and response["code"] == 0:
            return response["data"]
        return None

    def get_device_info(self) -> Any:
        response = self._api_call(
            f"{self._strings[18]}/{self._strings[19]}/{self._strings[22]}/{self._strings[24]}",
            {"did": self._did},
        )
        if response and "data" in response and response["code"] == 0:
            data = response["data"]
            self._handle_device_info(data)
            response = self._api_call(
                f"{self._strings[18]}/{self._strings[20]}/{self._strings[25]}",
                {"did": self._did},
            )
            if response and "data" in response and response["code"] == 0:
                if self._strings[26] in response["data"]:
                    data = {
                        **response["data"][self._strings[26]][self._strings[27]],
                        **data,
                    }
                else:
                    _LOGGER.debug("Get Device OTC Info Retrying with fallback... (%s)", response)
                    devices = self.get_devices()
                    if devices is not None:
                        found = list(
                            filter(
                                lambda d: str(d["did"]) == self._did,
                                devices[self._strings[29]][self._strings[31]],
                            )
                        )
                        if len(found) > 0:
                            self._handle_device_info(found[0])
                            return found[0]
                    _LOGGER.error("Get Device OTC Info Failed!")
                    return None
            return data
        return None

    def get_info(self, mac: str) -> Tuple[Optional[str], Optional[str]]:
        if self._did is not None:
            return " ", self._host
        devices = self.get_devices()
        if devices is not None:
            found = list(
                filter(
                    lambda d: str(d["mac"]).lower() == str(mac).lower(),
                    devices[self._strings[29]][self._strings[31]],
                )
            )
            if len(found) > 0:
                self._handle_device_info(found[0])
                return " ", self._host
        return None, None

    def send_async(self, callback, method, parameters, retry_count: int = 2):
        host = ""
        if self._host and len(self._host):
            host = f"-{self._host.split('.')[0]}"

        self._id = self._id + 1  # random.randint(0, int(self._strings[81]) - 1) + int(self._strings[82])
        self._api_call_async(
            lambda api_response: callback(
                None
                if api_response is None
                or "data" not in api_response
                or api_response["data"] is None
                or "result" not in api_response["data"]
                else api_response["data"]["result"]
            ),
            f"{self._strings[32]}{host}/{self._strings[22]}/{self._strings[33]}",
            {
                "did": str(self._did),
                "id": self._id,
                "data": {
                    "did": str(self._did),
                    "id": self._id,
                    "method": method,
                    "params": parameters,
                },
            },
            retry_count,
        )

    def send(self, method, parameters, retry_count: int = 2, timeout=None) -> Any:
        host = ""
        if self._host and len(self._host):
            host = f"-{self._host.split('.')[0]}"

        self._id = self._id + 1  # random.randint(0, int(self._strings[81]) - 1) + int(self._strings[82])
        api_response = self._api_call(
            f"{self._strings[32]}{host}/{self._strings[22]}/{self._strings[33]}",
            {
                "did": str(self._did),
                "id": self._id,
                "data": {
                    "did": str(self._did),
                    "id": self._id,
                    "method": method,
                    "params": parameters,
                },
            },
            retry_count,
            timeout,
        )
        if (
            api_response is None
            or "data" not in api_response
            or api_response["data"] is None
            or "result" not in api_response["data"]
        ):
            if api_response:
                ## Success is true but no data, retry once
                if api_response.get("success") is True and retry_count > 0:
                    return self.send(method, parameters, 0)
                _LOGGER.warning("Failed to execute api call: %s", api_response)
            return None
        return api_response["data"]["result"]

    def get_device_file(self, file_name, file_type, retried=False) -> Any:
        try:
            self._refresh_expired_key()

            body = self._signed(
                {
                    "did": str(self._did),
                    "uid": str(self._uid),
                    "fileinfo": json.dumps({"filename": file_name, "type": file_type}, separators=(",", ":")),
                }
            )
            status, content = self._http(
                "POST",
                f"{self.get_api_url()}{self._strings[54]}",
                self._auth_headers(self._strings[46]),
                json.dumps(body, separators=(",", ":")),
                15,
            )
            if status == 200:
                return content
            elif status == 401:
                if self._auth_failure(content.decode("utf-8", "replace")) == 2:
                    self._logged_in = False
                    self._auth_failed = True
                    _LOGGER.error("Get device file failed: Session invalid (%s)", content.decode("utf-8", "replace"))
                    return None
                if not retried and self.login():
                    return self.get_device_file(file_name, file_type, True)
            _LOGGER.warning("Get device file failed! (%s)", content.decode("utf-8", "replace"))

        except TimeoutError:
            _LOGGER.warning("Error while executing request: Read timed out. (timeout=15)")
        except Exception as ex:
            _LOGGER.warning("Error while executing request: %s", str(ex))
        return None

    def get_file(self, url: str, retry_count: int = 4) -> Any:
        retries = 0
        if not retry_count or retry_count < 0:
            retry_count = 0
        headers = {
            "Accept": None,
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
            self._strings[42]: self._strings[68],
        }
        while retries < retry_count + 1:
            try:
                status, content = self._http("GET", url, headers, None, 6)
                if status == 200:
                    return content
            except Exception as ex:
                _LOGGER.warning("Unable to get file at %s: %s", url, ex)
            retries = retries + 1
        return None

    def get_file_url(self, object_name: str = "") -> Any:
        api_response = self._api_call(
            f"{self._strings[18]}/{self._strings[34]}/{self._strings[49]}",
            {
                "did": str(self._did),
                "uid": str(self._uid),
                self._strings[30]: self._model,
                "filename": object_name[1:],
                self._strings[16]: self._country,
            },
        )
        if api_response is None or "data" not in api_response:
            return None

        return api_response["data"]

    def get_interim_file_url(self, object_name: str = "") -> str:
        api_response = self._api_call(
            f"{self._strings[18]}/{self._strings[34]}/{self._strings[48]}",
            {
                "did": str(self._did),
                self._strings[30]: self._model,
                self._strings[35]: object_name,
                self._strings[16]: self._country,
            },
        )
        if api_response is None or "data" not in api_response:
            return None

        return api_response["data"]

    def get_properties(self, keys):
        params = {"did": str(self._did), "keys": keys}
        api_response = self._api_call(f"{self._strings[18]}/{self._strings[20]}/{self._strings[36]}", params)
        if api_response is None or "data" not in api_response:
            return None

        return api_response["data"]

    def get_device_property(self, key, limit=1, time_start=0, time_end=9999999999):
        return self.get_device_data(key, "prop", limit, time_start, time_end)

    def get_device_event(self, key, limit=1, time_start=0, time_end=9999999999):
        return self.get_device_data(key, "event", limit, time_start, time_end)

    def get_device_data(self, key, type, limit=1, time_start=0, time_end=9999999999):
        data_keys = key.split(".")
        params = {
            "uid": str(self._uid),
            "did": str(self._did),
            "from": time_start if time_start else 1687019188,
            "limit": limit,
            "siid": data_keys[0],
            self._strings[16]: self._country,
            self._strings[37]: 3,
        }
        param_name = "piid"
        if type == "event":
            param_name = "eiid"
        elif type == "action":
            param_name = "aiid"

        params[param_name] = data_keys[1]
        api_response = self._api_call(f"{self._strings[18]}/{self._strings[20]}/{self._strings[38]}", params)
        if api_response is None or "data" not in api_response or self._strings[28] not in api_response["data"]:
            return None

        return api_response["data"][self._strings[28]]

    def get_batch_device_datas(self, props) -> Any:
        api_response = self._api_call(
            f"{self._strings[18]}/{self._strings[21]}/{self._strings[39]}",
            {"did": self._did, self._strings[30]: props},
        )
        if api_response is None or "data" not in api_response:
            return None
        return api_response["data"]

    def set_batch_device_datas(self, props) -> Any:
        api_response = self._api_call(
            f"{self._strings[18]}/{self._strings[21]}/{self._strings[40]}",
            {"did": self._did, self._strings[30]: props},
        )
        if api_response is None or "result" not in api_response:
            return None
        return api_response["result"]

    def request(self, url: str, data, retry_count=2, timeout=None, retried=False) -> Any:
        retries = 0
        if not timeout:
            timeout = 6

        self._refresh_expired_key()

        if not retry_count or retry_count < 0:
            retry_count = 0
        result = None
        while retries < retry_count + 1:
            if retries:
                # Back off before retrying so transient cloud errors are not hammered
                sleep(min(0.5 * 2 ** (retries - 1), 2))
            try:
                headers = self._auth_headers(self._strings[46])
                result = self._http("POST", url, headers, data, timeout)
            except TimeoutError:
                retries = retries + 1
                if self._connected:
                    _LOGGER.warning(f"Error while executing request: Read timed out. (timeout={timeout})")
                continue
            except Exception as ex:
                retries = retries + 1
                if self._connected:
                    _LOGGER.warning("Error while executing request: %s", str(ex))
                continue

            # Retry server side and rate limit errors
            if (result[0] == 429 or result[0] >= 500) and retries < retry_count:
                retries = retries + 1
                _LOGGER.debug("Execute api call failed with status %s, retrying", result[0])
                continue
            break

        if result is not None:
            status, content = result
            if status == 200:
                try:
                    response = json.loads(content)
                except ValueError:
                    _LOGGER.warning("Execute api call failed with invalid response: %s", content[:200])
                else:
                    self._fail_count = 0
                    self._connected = True
                    return response
            elif status == 401:
                if self._auth_failure(content.decode("utf-8", "replace")) == 2:
                    self._logged_in = False
                    self._auth_failed = True
                    _LOGGER.error("Execute api call failed: Session invalid (%s)", content.decode("utf-8", "replace"))
                elif not retried and self.login():
                    return self.request(url, data, retry_count, timeout, True)
            else:
                _LOGGER.warning("Execute api call failed with response: %s", content.decode("utf-8", "replace"))

        if self._fail_count == 5:
            self._connected = False
        else:
            self._fail_count = self._fail_count + 1
        return None

    def disconnect(self):
        for k in list(self._conns):
            self._close_conn(k)
        self._connected = False
        self._logged_in = False
        self._auth_failed = False
        if self._reconnect_timer is not None:
            self._reconnect_timer.stop()
        if self._client is not None:
            self._client.disconnect()
            self._client.loop_stop()
            self._client = None
            self._client_connected = False
            self._client_connecting = False
        if self._thread:
            self._queue.put([])
        if self._client_thread:
            self._client_queue.put([])
        self._message_callback = None
        self._connected_callback = None


class DreameVacuumMiHomeCloudProtocol:
    def __init__(
        self, username: str, password: str, country: str, auth_key: str = None, device_id: str = None
    ) -> None:
        self._username = username
        self._password = password
        self._country = country
        self._auth_key = auth_key
        self._session_obj = None
        self._queue = queue.Queue()
        self._thread = None
        self._sign = None
        self._ssecurity = None
        self._userId = None
        self._service_token = None
        self._pass_token = None
        self._captcha_ick = None
        self._captcha_code = None
        self._logged_in = False
        self._auth_failed = False
        self._uid = None
        self._did = device_id
        self._client_id = DreameVacuumMiHomeCloudProtocol.generate_client_id()

        if self._auth_key:
            data = self._auth_key.split(" ")
            if len(data) >= 4:
                self._service_token = data[0]
                self._ssecurity = data[1]
                self._userId = data[2]
                self._client_id = data[3]
            if len(data) >= 5:
                self._pass_token = data[4]

        self._useragent = f"Android-7.1.1-1.0.0-ONEPLUS A3010-136-{self._client_id} APP/xiaomi.smarthome APPV/62830"
        self._locale = locale.getdefaultlocale()[0]
        self._v3 = False
        self.verification_url = None
        self.verification_dest = None
        self.login_error = None
        self.captcha_img = None
        self._fail_count = 0
        self._connected = False
        try:
            offset = (time.timezone if (time.localtime().tm_isdst == 0) else time.altzone) / 60 * -1
            self._timezone = "GMT{}{:02d}:{:02d}".format(
                "+" if offset >= 0 else "-", abs(int(offset / 60)), int(offset % 60)
            )
        except:
            self._timezone = "GMT+00:00"

    def _get_session(self) -> requests.Session:
        if self._session_obj is None:
            self._session_obj = requests.session()
        return self._session_obj

    def _api_task(self):
        while True:
            item = self._queue.get()
            if len(item) == 0:
                self._queue.task_done()
                self._thread = None
                return
            try:
                response = self._api_call(item[1], item[2], item[3])
                if not self.check_login(response):
                    self._logged_in = False
                    self._auth_failed = True
                    response = None
            except Exception as ex:
                _LOGGER.warning("Async api call %s failed: %s", item[1], ex)
                response = None
            _run_callback(item[0], response)

            sleep(0.1)
            self._queue.task_done()

    def _api_call_async(self, callback, url, params=None, retry_count=2):
        if self._thread is None:
            self._thread = Thread(target=self._api_task, daemon=True)
            self._thread.start()

        self._queue.put((callback, url, params, retry_count))

    def _api_call(self, url, params, retry_count=2, timeout=None):
        response = self.request(
            f"{self.get_api_url()}/{url}", {"data": json.dumps(params, separators=(",", ":"))}, retry_count, timeout
        )

        if not self.check_login(response):
            self._logged_in = False
            self._auth_failed = True
            response = None
        return response

    @property
    def logged_in(self) -> bool:
        return self._logged_in

    @property
    def auth_failed(self) -> bool:
        return self._auth_failed

    @property
    def connected(self) -> bool:
        return self._connected

    @property
    def device_id(self) -> str:
        return self._did

    @property
    def dreame_cloud(self) -> bool:
        return False

    @property
    def auth_key(self) -> str | None:
        return self._auth_key

    @property
    def object_name(self) -> str:
        return f"{str(self._uid)}/{str(self._did)}/0"

    def check_login(self, response=None) -> bool:
        try:
            if response is None:
                url = f"{self.get_api_url()}/v2/message/v2/check_new_msg"
                params = {
                    "data": json.dumps(
                        {
                            "begin_at": int(time.time()) - 60,
                        },
                        separators=(",", ":"),
                    )
                }
                headers = {
                    "User-Agent": self._useragent,
                    "Accept-Encoding": "identity",
                    "x-xiaomi-protocal-flag-cli": "PROTOCAL-HTTP2",
                    "content-type": "application/x-www-form-urlencoded",
                    "MIOT-ENCRYPT-ALGORITHM": "ENCRYPT-RC4",
                }
                cookies = {
                    "userId": str(self._userId),
                    "yetAnotherServiceToken": self._service_token,
                    "serviceToken": self._service_token,
                    "locale": str(self._locale),
                    "timezone": str(self._timezone),
                    "is_daylight": str(time.daylight),
                    "dst_offset": str(time.localtime().tm_isdst * 60 * 60 * 1000),
                    "channel": "MI_APP_STORE",
                }
                nonce = self.generate_nonce()
                signed_nonce = self.signed_nonce(nonce)
                fields = self.generate_enc_params(url, "POST", signed_nonce, nonce, params, self._ssecurity)

                retries = 0
                http_response = None
                while retries < 2:
                    try:
                        http_response = self._get_session().post(
                            url, headers=headers, cookies=cookies, data=fields, timeout=6
                        )
                        break
                    except Exception:
                        retries += 1
                        http_response = None

                if http_response is None:
                    return True
                if http_response.status_code != 200:
                    return False

                decoded = self.decrypt_rc4(self.signed_nonce(fields["_nonce"]), http_response.text)
                response = json.loads(decoded) if decoded else None

            if response is not None:
                message = response.get("message", "")
                code = response.get("code", 0)
                if (
                    code == 2
                    or code == 3
                    or "auth err" in message
                    or "invalid signature" in message
                    or "SERVICETOKEN_EXPIRED" in message
                ):
                    return False
                return True
        except:
            pass
        return False

    def login_step_1(self) -> bool:
        try:
            response = self._get_session().get(
                "https://account.xiaomi.com/pass/serviceLogin?sid=xiaomiio&_json=true",
                headers={
                    "User-Agent": self._useragent,
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                cookies={"deviceId": self._client_id},
                timeout=10,
            )
            if response is not None:
                if response.status_code == 200:
                    data = self.to_json(response.text)
                    self._sign = data.get("_sign")
                    if data.get("code") == 0:
                        self._userId = data.get("userId", self._userId)
                        self._ssecurity = data.get("ssecurity", self._ssecurity)
                        self._location = data.get("location")
                        pass_token = data.get("passToken") or response.cookies.get("passToken")
                        if pass_token:
                            self._pass_token = pass_token
                    return True
                self._auth_failed = True
        except:
            pass
        return False

    def login_step_2(self) -> bool:
        self._auth_failed = False
        data = {
            "user": self._username,
            "hash": hashlib.md5(str.encode(self._password)).hexdigest().upper(),
            "callback": "https://sts.api.io.mi.com/sts",
            "sid": "xiaomiio",
            "qs": "%3Fsid%3Dxiaomiio%26_json%3Dtrue",
        }
        if self._sign:
            data["_sign"] = self._sign
        params = {"_json": "true"}

        self.verification_url = None
        self.captcha_img = None

        try:
            session = self._get_session()
            cookies = {}
            if self._captcha_code and self._captcha_ick:
                data["captCode"] = self._captcha_code
                params["_dc"] = int(time.time() * 1000)
                cookies["ick"] = self._captcha_ick

            response = session.post(
                "https://account.xiaomi.com/pass/serviceLoginAuth2",
                headers={
                    "User-Agent": self._useragent,
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data=data,
                params=params,
                cookies=cookies,
                timeout=10,
            )
            if response is not None:
                if response.status_code == 200:
                    data = self.to_json(response.text)
                    location = data.get("location")
                    if location:
                        self._userId = data.get("userId", self._userId)
                        self._ssecurity = data.get("ssecurity", self._ssecurity)
                        self._location = location
                        pass_token = data.get("passToken") or response.cookies.get("passToken")
                        if pass_token:
                            self._pass_token = pass_token
                        return True

                    if "notificationUrl" in data:
                        verification_url = data["notificationUrl"]
                        if verification_url[:4] != "http":
                            verification_url = f"https://account.xiaomi.com{verification_url}"
                        self.verification_url = verification_url

                    if "captchaUrl" in data:
                        url = data["captchaUrl"]
                        if url:
                            if url[:4] != "http":
                                url = f"https://account.xiaomi.com{url}"

                            response = session.get(url)
                            if ick := response.cookies.get("ick"):
                                self._captcha_ick = ick
                                self.captcha_img = base64.b64encode(response.content).decode()
                self._auth_failed = True
        except:
            pass
        return False

    def login_step_3(self) -> bool:
        try:
            response = self._get_session().get(
                self._location,
                headers={
                    "User-Agent": self._useragent,
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                timeout=10,
            )
            if response is not None:
                if response.status_code == 200 and "serviceToken" in response.cookies:
                    self._service_token = response.cookies.get("serviceToken")
                    pass_token = self._get_session().cookies.get("passToken") or response.cookies.get("passToken")
                    if pass_token:
                        self._pass_token = pass_token
                    self._auth_key = f"{self._service_token} {self._ssecurity} {self._userId} {self._client_id}"
                    if self._pass_token:
                        self._auth_key = f"{self._auth_key} {self._pass_token}"
                    return True
                else:
                    self._auth_failed = True
        except:
            pass
        return False

    def login(self) -> bool:
        self.login_error = None
        self.verification_dest = None
        if self._session_obj is not None:
            self._session_obj.close()
        session = self._session_obj = requests.session()
        for domain in ("mi.com", "xiaomi.com"):
            session.cookies.set("sdkVersion", "3.8.6", domain=domain)
            session.cookies.set("deviceId", self._client_id, domain=domain)
            if self._pass_token:
                session.cookies.set("passToken", self._pass_token, domain=domain)
            if self._userId:
                session.cookies.set("userId", str(self._userId), domain=domain)

        self._location = None
        logged_in = (self._ssecurity and self.check_login()) or (
            self.login_step_1() and (self._location or self.login_step_2()) and self.login_step_3()
        )

        if logged_in:
            self._logged_in = True
            self._auth_failed = False
            self._fail_count = 0
            self._connected = True
        else:
            self._ssecurity = None

        return self._logged_in

    def send_2fa_code(self) -> bool:
        if self.verification_url:
            path = "fe/service/identity/authStart"
            if path in self.verification_url:
                self.login_error = "2fa_send_failed"
                self.verification_dest = None
                try:
                    session = self._get_session()
                    session.get(self.verification_url, headers={"User-Agent": self._useragent}, timeout=10)
                    context = parse_qs(urlparse(self.verification_url).query).get("context", [""])[0]

                    response = session.get(
                        "https://account.xiaomi.com/identity/list",
                        params={"sid": "xiaomiio", "context": context, "_locale": str(self._locale)},
                        timeout=10,
                    )
                    if response and response.status_code == 200:
                        identity_session = response.cookies.get("identity_session")
                        if identity_session:
                            data = self.to_json(response.text)
                            options = data.get("options", [])
                            if 4 in options:
                                flag = 4
                            elif 8 in options:
                                flag = 8
                            else:
                                flag = data.get("flag", 4)

                            key = "Phone" if flag == 4 else "Email"
                            verify_response = session.get(
                                f"https://account.xiaomi.com/identity/auth/verify{key}",
                                cookies={"identity_session": identity_session},
                                params={
                                    "_flag": flag,
                                    "_json": "true",
                                    "sid": "xiaomiio",
                                    "context": context,
                                    "mask": "0",
                                    "_locale": str(self._locale),
                                },
                                timeout=10,
                            )
                            if not verify_response or verify_response.status_code != 200:
                                return False

                            verify_data = self.to_json(verify_response.text)
                            code = verify_data.get("code")
                            if code != 0:
                                desc = verify_data.get("description") or ""
                                msg = verify_data.get("message") or ""
                                if (
                                    "frequent" in desc.lower()
                                    or "frequent" in msg.lower()
                                    or "seconds" in desc.lower()
                                    or "seconds" in msg.lower()
                                ):
                                    self.login_error = "2fa_cooldown_active"
                                elif code == 70022 or "limit" in desc.lower() or "limit" in msg.lower():
                                    self.login_error = "2fa_limit_reached"
                                else:
                                    self.login_error = desc or msg or "2fa_send_failed"
                                return False

                            send_response = session.post(
                                f"https://account.xiaomi.com/identity/auth/send{key}Ticket",
                                cookies={"identity_session": identity_session},
                                params={
                                    "_dc": str(int(time.time() * 1000)),
                                    "sid": "xiaomiio",
                                    "context": context,
                                    "mask": "0",
                                    "_locale": str(self._locale),
                                },
                                data={
                                    "retry": 0,
                                    "icode": "",
                                    "_json": "true",
                                    "ick": session.cookies.get("ick", ""),
                                },
                                timeout=10,
                            )
                            if not send_response or send_response.status_code != 200:
                                return False

                            send_data = self.to_json(send_response.text)
                            code = send_data.get("code")
                            if code != 0:
                                desc = send_data.get("description") or ""
                                msg = send_data.get("message") or ""
                                if (
                                    "frequent" in desc.lower()
                                    or "frequent" in msg.lower()
                                    or "seconds" in desc.lower()
                                    or "seconds" in msg.lower()
                                ):
                                    self.login_error = "2fa_cooldown_active"
                                elif code == 70022 or "limit" in desc.lower() or "limit" in msg.lower():
                                    self.login_error = "2fa_limit_reached"
                                else:
                                    self.login_error = desc or msg or "2fa_send_failed"
                                return False

                            self.login_error = None
                            self.verification_dest = (
                                verify_data.get("maskedPhone") or verify_data.get("maskedEmail") or "*****"
                            )
                            return True
                except Exception as ex:
                    _LOGGER.warning("Failed to send 2FA code: %s", ex)
        return False

    def verify_code(self, code) -> bool:
        verification_url = self.verification_url
        session = self._get_session()
        if not (code and verification_url and session and "fe/service/identity/authStart" in verification_url):
            _LOGGER.error("2FA failed: Missing code, session, or invalid verification URL.")
            return False

        headers = {"User-Agent": self._useragent, "Content-Type": "application/x-www-form-urlencoded"}

        try:
            context = parse_qs(urlparse(verification_url).query).get("context", [""])[0]
            if not context:
                _LOGGER.error("2FA failed: 'context' parameter missing from verification_url.")
                return False

            response = session.get(
                "https://account.xiaomi.com/identity/list",
                params={"sid": "xiaomiio", "context": context, "_locale": str(self._locale)},
                headers=headers,
                timeout=10,
            )
            if response is None:
                _LOGGER.error(f"2FA failed: identity/list endpoint failed!")
                return False
            elif response.status_code != 200:
                _LOGGER.error(f"2FA failed: identity/list endpoint returned HTTP {response.status_code}!")
                return False

            try:
                data = self.to_json(response.text)
                options = data.get("options", [])
                if 4 in options:
                    flag = 4
                elif 8 in options:
                    flag = 8
                else:
                    flag = data.get("flag", 4)
            except Exception as e:
                _LOGGER.error(f"2FA failed: Could not parse identity/list JSON. Error: {e}")
                return False

            if not session.cookies.get("identity_session"):
                _LOGGER.error("2FA failed: Missing 'identity_session' cookie.")
                return False

            response = session.post(
                f"https://account.xiaomi.com/identity/auth/verify{'Phone' if flag == 4 else 'Email'}",
                headers=headers,
                params={
                    "_flag": flag,
                    "_json": "true",
                    "sid": "xiaomiio",
                    "context": context,
                    "mask": "0",
                    "_locale": str(self._locale),
                },
                data={
                    "_flag": flag,
                    "ticket": code,
                    "trust": "false",
                    "_json": "true",
                    "ick": session.cookies.get("ick", ""),
                },
                timeout=15,
            )

            location_url = None
            if response is None:
                _LOGGER.error("2FA failed: verify endpoint request failed!")
            elif response.status_code == 200:
                try:
                    verify_data_resp = self.to_json(response.text)
                    if verify_data_resp.get("code") != 0:
                        return False
                    location_url = verify_data_resp.get("location")
                except Exception:
                    location_url = response.headers.get("Location")
            elif response.status_code in (301, 302):
                location_url = response.headers.get("Location")

            if location_url:
                response = session.get(location_url, headers=headers, allow_redirects=True, timeout=10)
                if response is not None and response.status_code == 200:
                    for c in session.cookies:
                        if c.name in ("userId", "cUserId") and c.value:
                            self._userId = str(c.value)
                            break

                    if self.login_step_1() and self.login_step_3():
                        self.verification_url = None
                        self.captcha_url = None
                        self._logged_in = True
                        self._auth_failed = False
                        self._fail_count = 0
                        self._connected = True
                        return True

            response = session.get(
                "https://account.xiaomi.com/identity/result/check",
                params={"sid": "xiaomiio", "context": context, "_locale": str(self._locale)},
                headers=headers,
                allow_redirects=False,
                timeout=10,
            )

            if response is None:
                _LOGGER.error("2FA failed: result/check API failed!")
                return False

            location_url = response.headers.get("Location") if response.status_code in (301, 302) else None
            if not location_url and response.status_code == 200 and response.text:
                location_url = self.to_json(response.text).get("location")

            if not location_url:
                _LOGGER.error(f"2FA failed: 'location_url' missing from check API. HTTP {response.status_code}")
                return False

            response = session.get(location_url, headers=headers, allow_redirects=False, timeout=10)
            if response is None:
                _LOGGER.error("2FA failed: sts_init failed!")
                return False

            if response.status_code == 200 and "Xiaomi Account - Tips" in response.text:
                response = session.get(location_url, headers=headers, allow_redirects=False, timeout=10)

            extension_pragma = response.headers.get("extension-pragma")
            if extension_pragma and extension_pragma.startswith("{"):
                try:
                    self._ssecurity = json.loads(extension_pragma).get("ssecurity", self._ssecurity)
                except Exception:
                    _LOGGER.error("2FA failed: Could not parse extension-pragma JSON!")
            else:
                _LOGGER.error("2FA failed: 'extension-pragma' header is missing or invalid!")
                return False

            location_url = response.headers.get("Location")
            if not location_url and response.text:
                match = re.search(r'(https://[a-zA-Z0-9-]*\.?sts\.api\.io\.mi\.com/sts[^"\'\s]*)', response.text)
                if match:
                    location_url = match.group(1)

            if not location_url:
                _LOGGER.error("2FA failed: Could not find STS redirect URL!")
                return False

            response = session.get(location_url, headers=headers, allow_redirects=True, timeout=10)
            if response is None or response.status_code != 200:
                _LOGGER.error(f"2FA failed: Final STS connection failed!")
                return False
            elif response.status_code != 200:
                _LOGGER.error(f"2FA failed: Final STS connection returned HTTP {response.status_code}!")
                return False

            self._service_token = session.cookies.get(
                "serviceToken", domain=".sts.api.io.mi.com"
            ) or session.cookies.get("serviceToken")

            for c in session.cookies:
                if c.name in ("userId", "cUserId") and c.value:
                    self._userId = str(c.value)
                    break

            if not self._service_token or not self._userId:
                _LOGGER.error("2FA failed: Missing 'serviceToken' or 'userId' after STS connection.")
                return False

            for d in [".api.io.mi.com", ".io.mi.com", ".mi.com"]:
                session.cookies.set("serviceToken", self._service_token, domain=d)
                session.cookies.set("yetAnotherServiceToken", self._service_token, domain=d)

            self._auth_key = f"{self._service_token} {self._ssecurity} {self._userId} {self._client_id}"
            self.verification_url = None
            self.captcha_url = None
            self._logged_in = True
            self._auth_failed = False
            self._fail_count = 0
            self._connected = True
            return True

        except Exception as ex:
            _LOGGER.error(f"2FA Exception: {ex}")
            return False

    def verify_captcha(self, code) -> bool:
        self._captcha_code = code
        return self.login() or self.captcha_img is None

    def get_file(self, url: str, retry_count: int = 4) -> Any:
        retries = 0
        if not retry_count or retry_count < 0:
            retry_count = 0
        while retries < retry_count + 1:
            try:
                response = self._get_session().get(url, timeout=6)
            except Exception as ex:
                response = None
                _LOGGER.warning("Unable to get file at %s: %s", url, ex)
            if response is not None and response.status_code == 200:
                return response.content
            retries = retries + 1
        return None

    def get_file_url(self, object_name: str = "") -> Any:
        api_response = self._api_call(f'home/getfileurl{("_v3" if self._v3 else "")}', {"obj_name": object_name})
        _LOGGER.debug("Get file url result: %s = %s", object_name, api_response)
        if api_response is None or not api_response.get("result") or "url" not in api_response["result"]:
            if api_response and api_response.get("code") == -8 and self._v3:
                _LOGGER.info("get_file_url fallback to V2")
                self._v3 = False
                return self.get_file_url(object_name)
            return None

        return api_response["result"]["url"]

    def get_interim_file_url(self, object_name: str = "") -> str:
        api_response = self._api_call(
            f'v2/home/get_interim_file_url{("_pro" if self._v3 else "")}',
            {"obj_name": object_name},
        )
        _LOGGER.debug("Get interim file url result: %s = %s", object_name, api_response)
        if api_response is None or not api_response.get("result") or "url" not in api_response["result"]:
            if api_response and api_response.get("code") == -8 and self._v3:
                _LOGGER.info("get_interim_file_url fallback to V2")
                self._v3 = False
                return self.get_interim_file_url(object_name)
            return None

        return api_response["result"]["url"]

    def send_async(self, callback, method, parameters, retry_count: int = 2):
        self._api_call_async(
            lambda api_response: callback(
                None if api_response is None or "result" not in api_response else api_response["result"]
            ),
            f"v2/home/rpc/{self._did}",
            {"method": method, "params": parameters},
            retry_count,
        )

    def send(self, method, parameters, retry_count: int = 2, timeout=None) -> Any:
        api_response = self._api_call(
            f"v2/home/rpc/{self._did}", {"method": method, "params": parameters}, retry_count, timeout
        )
        if api_response is None or "result" not in api_response:
            return None
        return api_response["result"]

    def get_device_property(self, key, limit=1, time_start=0, time_end=9999999999):
        return self.get_device_data(key, "prop", limit, time_start, time_end)

    def get_device_event(self, key, limit=1, time_start=0, time_end=9999999999):
        return self.get_device_data(key, "event", limit, time_start, time_end)

    def get_device_data(self, key, type, limit=1, time_start=0, time_end=9999999999):
        api_response = self._api_call(
            "user/get_user_device_data",
            {
                "uid": str(self._uid),
                "did": str(self._did),
                "time_end": time_end,
                "time_start": time_start,
                "limit": limit,
                "key": key,
                "type": type,
            },
        )
        if api_response is None or "result" not in api_response:
            return None

        return api_response["result"]

    def get_info(self, mac: str) -> Tuple[Optional[str], Optional[str]]:
        devices = self.get_devices()
        if devices:
            found = list(filter(lambda d: str(d["mac"]).lower() == str(mac).lower(), devices))

            if len(found) > 0:
                self._uid = found[0]["uid"]
                self._did = found[0]["did"]
                self._v3 = bool("model" in found[0] and "xiaomi.vacuum." in found[0]["model"])
                return found[0]["token"], found[0]["localip"]
        return None, None

    def get_supported_devices(self, models, host=None, mac=None, device_id=None) -> Any:
        response = self.get_devices()
        devices = []
        unsupported_devices = []
        if response:
            all_devices = list(
                filter(
                    lambda d: not d.get("parent_id"),
                    response,
                )
            )
            for device in all_devices:
                model = device["model"]
                if model in models:
                    devices.append(device)
                    if (
                        (mac is not None and str(device.get("mac")).lower() == str(mac).lower())
                        or (device_id is not None and device.get("did") == device_id)
                        or (host is not None and device.get("localip") == host)
                    ):
                        devices = [device]
                        break
                elif ".vacuum." in model:
                    unsupported_devices.append(device)
        return devices, unsupported_devices

    def get_devices(self) -> Any:
        device_list = []
        response = self._api_call(
            "v2/homeroom/gethome",
            {
                "fg": True,
                "fetch_share": True,
                "fetch_share_dev": True,
                "limit": 100,
                "app_ver": 7,
            },
        )
        if response and "result" in response and response["result"]:
            homes = {}
            for home in response["result"].get("homelist"):
                homes[home["id"]] = self._userId

            response = self._api_call(
                "v2/user/get_device_cnt",
                {
                    "fetch_own": True,
                    "fetch_share": True,
                },
            )
            if (
                response
                and "result" in response
                and response["result"]
                and "share" in response["result"]
                and response["result"]["share"]
            ):
                for device in response["result"]["share"].get("share_family"):
                    homes[device["home_id"]] = device["home_owner"]

            if homes:
                for k, v in homes.items():
                    response = self._api_call(
                        "v2/home/home_device_list",
                        {
                            "home_id": int(k),
                            "home_owner": v,
                            "limit": 100,
                            "get_split_device": True,
                            "support_smart_home": True,
                        },
                    )
                    if (
                        response
                        and "result" in response
                        and response["result"]
                        and "device_info" in response["result"]
                        and response["result"]["device_info"]
                    ):
                        device_list.extend(response["result"]["device_info"])

            response = self._api_call("home/device_list", {"getVirtualModel": False, "getHuamiDevices": 0})
            if (
                response
                and "result" in response
                and response["result"]
                and "list" in response["result"]
                and response["result"]["list"]
            ):
                for device in response["result"]["list"]:
                    if (
                        len(
                            list(
                                filter(
                                    lambda d: str(d["mac"]) == device["mac"],
                                    device_list,
                                )
                            )
                        )
                        == 0
                    ):
                        device_list.append(device)

            return device_list

    def get_batch_device_datas(self, props) -> Any:
        api_response = self._api_call("device/batchdevicedatas", [{"did": self._did, "props": props}])
        if api_response is None or self._did not in api_response:
            return None
        return api_response[self._did]

    def set_batch_device_datas(self, props) -> Any:
        api_response = self._api_call("v2/device/batch_set_props", [{"did": self._did, "props": props}])
        if api_response is None or "result" not in api_response:
            return None
        return api_response["result"]

    def request(self, url: str, params: Dict[str, str], retry_count=2, timeout=None) -> Any:
        retries = 0
        if not retry_count or retry_count < 0:
            retry_count = 0
        headers = {
            "User-Agent": self._useragent,
            "Accept-Encoding": "identity",
            "x-xiaomi-protocal-flag-cli": "PROTOCAL-HTTP2",
            "content-type": "application/x-www-form-urlencoded",
            "MIOT-ENCRYPT-ALGORITHM": "ENCRYPT-RC4",
        }
        cookies = {
            "userId": str(self._userId),
            "yetAnotherServiceToken": self._service_token,
            "serviceToken": self._service_token,
            "locale": str(self._locale),
            "timezone": str(self._timezone),
            "is_daylight": str(time.daylight),
            "dst_offset": str(time.localtime().tm_isdst * 60 * 60 * 1000),
            "channel": "MI_APP_STORE",
        }

        nonce = self.generate_nonce()
        signed_nonce = self.signed_nonce(nonce)
        fields = self.generate_enc_params(url, "POST", signed_nonce, nonce, params, self._ssecurity)

        while retries < retry_count + 1:
            try:
                response = self._get_session().post(
                    url, headers=headers, cookies=cookies, data=fields, timeout=timeout if timeout else 6
                )
                break
            except Exception as ex:
                retries = retries + 1
                response = None
                if self._connected:
                    _LOGGER.warning("Error while executing request: %s %s", url, str(ex))

        if response is not None:
            if response.status_code == 200:
                self._fail_count = 0
                self._connected = True
                decoded = self.decrypt_rc4(self.signed_nonce(fields["_nonce"]), response.text)
                return json.loads(decoded) if decoded else None
            _LOGGER.warning("Execute api call failed with response: %s", response.text)

        if self._fail_count == 5:
            self._connected = False
        else:
            self._fail_count = self._fail_count + 1
        return None

    def get_api_url(self) -> str:
        return f"https://{('' if self._country == 'cn' else (self._country + '.'))}api.io.mi.com/app"

    def signed_nonce(self, nonce: str) -> str:
        hash_object = hashlib.sha256(base64.b64decode(self._ssecurity) + base64.b64decode(nonce))
        return base64.b64encode(hash_object.digest()).decode("utf-8")

    def disconnect(self):
        self._get_session().close()
        self._connected = False
        self._logged_in = False
        self._auth_failed = False
        if self._thread:
            self._queue.put([])

    @staticmethod
    def generate_nonce():
        millis = int(round(time.time() * 1000))
        b = (random.getrandbits(64) - 2**63).to_bytes(8, "big", signed=True)
        part2 = int(millis / 60000)
        b += part2.to_bytes(((part2.bit_length() + 7) // 8), "big")
        return base64.b64encode(b).decode("utf-8")

    @staticmethod
    def generate_client_id() -> str:
        return "".join((chr(random.randint(97, 122)) for _ in range(16)))

    @staticmethod
    def generate_signature(url, signed_nonce: str, nonce: str, params: Dict[str, str]) -> str:
        signature_params = [url.split("com")[1], signed_nonce, nonce]
        for k, v in params.items():
            signature_params.append(f"{k}={v}")
        signature_string = "&".join(signature_params)
        signature = hmac.new(
            base64.b64decode(signed_nonce),
            msg=signature_string.encode(),
            digestmod=hashlib.sha256,
        )
        return base64.b64encode(signature.digest()).decode()

    @staticmethod
    def generate_enc_signature(url, method: str, signed_nonce: str, params: Dict[str, str]) -> str:
        signature_params = [
            str(method).upper(),
            url.split("com")[1].replace("/app/", "/"),
        ]
        for k, v in params.items():
            signature_params.append(f"{k}={v}")
        signature_params.append(signed_nonce)
        signature_string = "&".join(signature_params)
        return base64.b64encode(hashlib.sha1(signature_string.encode("utf-8")).digest()).decode()

    @staticmethod
    def generate_enc_params(
        url: str,
        method: str,
        signed_nonce: str,
        nonce: str,
        params: Dict[str, str],
        ssecurity: str,
    ) -> Dict[str, str]:
        params["rc4_hash__"] = DreameVacuumMiHomeCloudProtocol.generate_enc_signature(
            url, method, signed_nonce, params
        )
        for k, v in params.items():
            params[k] = DreameVacuumMiHomeCloudProtocol.encrypt_rc4(signed_nonce, v)
        params.update(
            {
                "signature": DreameVacuumMiHomeCloudProtocol.generate_enc_signature(url, method, signed_nonce, params),
                "ssecurity": ssecurity,
                "_nonce": nonce,
            }
        )
        return params

    @staticmethod
    def to_json(response_text: str) -> Any:
        return json.loads(response_text.replace("&&&START&&&", ""))

    @staticmethod
    def encrypt_rc4(password: str, payload: str) -> str:
        r = ARC4.new(base64.b64decode(password))
        r.encrypt(bytes(1024))
        return base64.b64encode(r.encrypt(payload.encode())).decode()

    @staticmethod
    def decrypt_rc4(password: str, payload: str) -> bytes:
        r = ARC4.new(base64.b64decode(password))
        r.encrypt(bytes(1024))
        return r.encrypt(base64.b64decode(payload))


class DreameVacuumProtocol:
    def __init__(
        self,
        ip: str = None,
        token: str = None,
        username: str = None,
        password: str = None,
        country: str = None,
        prefer_cloud: bool = False,
        account_type: str = "mi",
        device_id: str = None,
        auth_key: str = None,
    ) -> None:
        self.prefer_cloud = prefer_cloud
        self._connected = False
        self._mac = None
        self._account_type = account_type

        if ip and token:
            self.device = DreameVacuumDeviceProtocol(ip, token)
        else:
            self.prefer_cloud = True
            self.device = None

        if username and password and country:
            if account_type == "mi":
                self.cloud = DreameVacuumMiHomeCloudProtocol(username, password, country, auth_key, device_id)
            else:
                self.cloud = DreameVacuumDreameHomeCloudProtocol(
                    username, password, account_type, country, auth_key, device_id
                )
        else:
            self.prefer_cloud = False
            self.cloud = None

        if account_type == "mi":
            self.device_cloud = (
                DreameVacuumMiHomeCloudProtocol(username, password, country, auth_key) if prefer_cloud else None
            )
        else:
            self.prefer_cloud = True
            self.device_cloud = self.cloud

    def set_credentials(self, ip: str, token: str, mac: str = None, account_type: str = "mi"):
        self._mac = mac
        self._account_type = account_type
        if ip and token and account_type == "mi":
            if self.device:
                self.device.set_credentials(ip, token)
            else:
                self.device = DreameVacuumDeviceProtocol(ip, token)
        else:
            self.device = None

    def connect(self, message_callback=None, connected_callback=None, retry_count=1) -> Any:
        if self._account_type == "mi" or self.cloud is None:
            info = self.send("miIO.info", retry_count=retry_count)
            if info and (self.prefer_cloud or not self.device) and self.device_cloud:
                self._connected = True
        else:
            info = self.cloud.connect(message_callback, connected_callback)
            if info:
                self._connected = True
        return info

    def disconnect(self):
        for obj in (self.device, self.cloud):
            if obj is not None:
                try:
                    obj.disconnect()
                except Exception:
                    _LOGGER.warning("Error while disconnecting", exc_info=True)
        if self.device_cloud is not None and self.device_cloud is not self.cloud:
            try:
                self.device_cloud.disconnect()
            except Exception:
                _LOGGER.warning("Error while disconnecting", exc_info=True)
        self._connected = False

    def send_async(self, callback, method, parameters: Any = None, retry_count: int = 2):
        if (self.prefer_cloud or not self.device) and self.device_cloud:
            if not self.device_cloud.logged_in:
                # Use different session for device cloud
                self.device_cloud.login()
                if self.device_cloud.logged_in and not self.device_cloud.device_id:
                    if self.cloud.device_id:
                        self.device_cloud._did = self.cloud.device_id
                    elif self._mac:
                        self.device_cloud.get_info(self._mac)

            if not self.device_cloud.logged_in:
                raise DeviceException("Unable to login to device over cloud") from None

            def cloud_callback(response):
                if response is None:
                    if method == "get_properties" or method == "set_properties":
                        self._connected = False
                    raise DeviceException("Unable to discover the device over cloud") from None
                self._connected = True
                if callback:
                    callback(response)

            self.device_cloud.send_async(cloud_callback, method, parameters=parameters, retry_count=retry_count)
            return

        if self.device:
            self.device.send_async(callback, method, parameters=parameters, retry_count=retry_count)

    def send(self, method, parameters: Any = None, retry_count: int = 2, timeout=None) -> Any:
        if (self.prefer_cloud or not self.device) and self.device_cloud:
            if not self.device_cloud.logged_in:
                # Use different session for device cloud
                self.device_cloud.login()
                if self.device_cloud.logged_in and not self.device_cloud.device_id:
                    if self.cloud.device_id:
                        self.device_cloud._did = self.cloud.device_id
                    elif self._mac:
                        self.device_cloud.get_info(self._mac)

            if not self.device_cloud.logged_in:
                raise DeviceException("Unable to login to device over cloud") from None

            response = self.device_cloud.send(method, parameters=parameters, retry_count=retry_count, timeout=timeout)
            if response is None:
                if method == "get_properties" or method == "set_properties":
                    self._connected = False
                raise DeviceException("Unable to discover the device over cloud") from None
            self._connected = True
            return response

        if self.device:
            return self.device.send(method, parameters=parameters, retry_count=retry_count)

    def get_properties(self, parameters: Any = None, retry_count: int = 1, timeout=None) -> Any:
        return self.send("get_properties", parameters=parameters, retry_count=retry_count, timeout=timeout)

    def set_property(self, siid: int, piid: int, value: Any = None, retry_count: int = 2) -> Any:
        return self._set_properties(
            [
                {
                    "did": f"{siid}.{piid}" if not self.dreame_cloud else str(self.cloud.device_id),
                    "siid": siid,
                    "piid": piid,
                    "value": value,
                }
            ],
            retry_count=retry_count,
        )

    def set_properties(self, properties, retry_count: int = 2) -> Any:
        return self._set_properties(
            [
                {
                    "did": f"{siid}.{piid}" if not self.dreame_cloud else str(self.cloud.device_id),
                    "siid": siid,
                    "piid": piid,
                    "value": value,
                }
                for siid, piid, value in properties
            ],
            retry_count=retry_count,
        )

    def set_property_async(self, callback, siid: int, piid: int, value: Any = None, retry_count: int = 2) -> Any:
        return self._set_properties_async(
            callback,
            [
                {
                    "did": f"{siid}.{piid}" if not self.dreame_cloud else str(self.cloud.device_id),
                    "siid": siid,
                    "piid": piid,
                    "value": value,
                }
            ],
            retry_count=retry_count,
        )

    def _set_properties(self, parameters: Any = None, retry_count: int = 2) -> Any:
        return self.send("set_properties", parameters=parameters, retry_count=retry_count)

    def _set_properties_async(self, callback, parameters: Any = None, retry_count: int = 2) -> Any:
        return self.send_async(callback, "set_properties", parameters=parameters, retry_count=retry_count)

    def action_async(self, callback, siid: int, aiid: int, parameters=None, retry_count: int = 2):
        if parameters is None:
            parameters = []

        _LOGGER.debug("Send Action Async: %s.%s %s", siid, aiid, parameters)
        self.send_async(
            callback,
            "action",
            parameters={
                "did": f"{siid}.{aiid}" if not self.dreame_cloud else str(self.cloud.device_id),
                "siid": siid,
                "aiid": aiid,
                "in": parameters,
            },
            retry_count=retry_count,
        )

    def action(self, siid: int, aiid: int, parameters=None, retry_count: int = 2) -> Any:
        if parameters is None:
            parameters = []

        _LOGGER.debug("Send Action: %s.%s %s", siid, aiid, parameters)
        return self.send(
            "action",
            parameters={
                "did": f"{siid}.{aiid}" if not self.dreame_cloud else str(self.cloud.device_id),
                "siid": siid,
                "aiid": aiid,
                "in": parameters,
            },
            retry_count=retry_count,
        )

    @property
    def connected(self) -> bool:
        if (self.prefer_cloud or not self.device) and self.device_cloud:
            return self.device_cloud.logged_in and self.device_cloud.connected and self._connected

        if self.device:
            return self.device.connected

        return False

    @property
    def dreame_cloud(self) -> bool:
        if self.cloud:
            return self.cloud.dreame_cloud
        return False
