from __future__ import annotations
import base64 as b6, gzip as gz, hashlib as hl, re as rx
import aiohttp as ah
from aiohttp import web as wb
from pathlib import Path as Pt
from Crypto.Cipher import AES as AE, ChaCha20
from Crypto.Random import get_random_bytes as rb
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey as Ky
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey as Xp, X25519PublicKey as Xq
from cryptography.hazmat.primitives.serialization import Encoding as Se, PublicFormat as Sf
from homeassistant.components.http import HomeAssistantView as Hv
from homeassistant.helpers import device_registry as Dr
from homeassistant.helpers.device_registry import format_mac as Fm
from homeassistant.helpers.storage import Store as Sx
from homeassistant.const import __version__ as Hz
from .const import DOMAIN as Dn, FRONTEND as Fe, CONF_DVC_KEY as Ck, LOGGER as Lg
from .dreame import VERSION as Vn


async def setup(o) -> None:
    gvh = lambda: hl.sha256(
        bytes(
            bytes.fromhex("ab3bb92ddcfce0dd5949d5991202b1e6")[j] ^ ((j * 101 + 80) & 0xFF)
            for j in (0, 10, 11, 1, 4, 7, 3, 14, 13, 12, 5, 9, 2, 8, 6, 15)
        )
        + (
            Pt(__file__).parent
            / bytes.fromhex(b6.b64decode("NjM2ZjZmNzI2NDY5NmU2MTc0NmY3MjJlNzA3OQ==").decode()).decode()
        )
        .read_text(encoding="utf-8")
        .replace("\r\n", "\n")
        .encode("utf-8")
        + (
            Pt(__file__).parent
            / bytes.fromhex(
                b6.b64decode("NjQ3MjY1NjE2ZDY1MmY1ZjVmNjk2ZTY5NzQ1ZjVmMmU3MDc5").decode()
            ).decode()
        )
        .read_text(encoding="utf-8")
        .replace("\r\n", "\n")
        .encode("utf-8")
        + (
            Pt(__file__).parent
            / bytes.fromhex(b6.b64decode("NjQ3MjY1NjE2ZDY1MmY2NDY1NzY2OTYzNjUyZTcwNzk=").decode()).decode()
        )
        .read_text(encoding="utf-8")
        .replace("\r\n", "\n")
        .encode("utf-8")
        + (
            Pt(__file__).parent
            / bytes.fromhex(
                b6.b64decode("NjQ3MjY1NjE2ZDY1MmY3MDcyNmY3NDZmNjM2ZjZjMmU3MDc5").decode()
            ).decode()
        )
        .read_text(encoding="utf-8")
        .replace("\r\n", "\n")
        .encode("utf-8")
        + (
            Pt(__file__).parent
            / bytes.fromhex(b6.b64decode("NjU2ZTc0Njk3NDc5MmU3MDc5").decode()).decode()
        )
        .read_text(encoding="utf-8")
        .replace("\r\n", "\n")
        .encode("utf-8")
        + (
            Pt(__file__).parent
            / bytes.fromhex(b6.b64decode("NjY3MjZmNmU3NDY1NmU2NDJlNzA3OQ==").decode()).decode()
        )
        .read_text(encoding="utf-8")
        .replace("\r\n", "\n")
        .encode("utf-8")
        + (
            Pt(__file__).parent
            / bytes.fromhex(b6.b64decode("NzY2MTYzNzU3NTZkMmU3MDc5").decode()).decode()
        )
        .read_text(encoding="utf-8")
        .replace("\r\n", "\n")
        .encode("utf-8")
    ).hexdigest()[:16]
    vh = await o.async_add_executor_job(gvh)
    vh = vh + hl.sha256(Hz.encode()).hexdigest()[:16]

    class Va(Hv):
        url = f"/{Dn}/frontend.js"
        name = f"{Dn}:frontend"
        requires_auth = False

        async def get(self, z):
            if z.query.get("v") != vh:
                return wb.Response(status=404)
            return wb.Response(
                body=b6.b64decode(Fe),
                content_type="application/javascript",
                headers={"Content-Encoding": "gzip", "Cache-Control": "public, max-age=5184000, immutable"},
            )

    class Vb(Hv):
        url = f"/api/{Dn}/{{vp}}/{{b}}"
        name = f"api:{Dn}:frontend"
        requires_auth = True
        q: dict[str, list] = {}

        async def get(self, z, vp, b) -> wb.Response:
            k1, k2, k3 = 403, None, False
            kp = z.query.get("k")
            try:
                nk = b6.b64decode(kp).decode().strip().lower() if kp else ""
            except Exception:
                nk = ""
            ac = kp is not None

            c1 = Dr.async_get(o).async_get(b) if b else None
            i = next(iter(c1.config_entries), None) if c1 else None
            if not i or i not in o.data.get(Dn, {}):
                k3 = True

            if not k3:
                c2 = o.data[Dn][i]
                if not (
                    c2._device
                    and c2._device.status
                    and c2._device.status.serial_number
                    and c2._device.info
                    and c2._device.info.model
                ):
                    k1, k3 = 202, True

            if not k3:
                e = o.config_entries.async_get_entry(i)
                if not e:
                    k1, k3 = 403, True

            if not k3:
                v1, v2, v3 = (
                    c2._device.status.serial_number,
                    c2._device.info.mac_address or c2._device.mac,
                    c2._device.info.model,
                )
                hs = bytes(
                    x1 ^ x2 for x1, x2 in zip(bytes.fromhex("096ea97b63adf781"), bytes.fromhex("7984377e4075ba7a"))
                ) + bytes(
                    x1 ^ x2 for x1, x2 in zip(bytes.fromhex("592cf02330c12db7"), bytes.fromhex("43222f8331d69a23"))
                )
                a1, a2, a3 = str(v1).encode(), Fm(str(v2)).encode(), str(v3).encode()
                b1, b2, b3 = (
                    hl.sha256(a1 + hs).digest(),
                    hl.sha256(a2 + hs[::-1]).digest(),
                    hl.sha256(a3 + hs).digest(),
                )
                c3 = bytes(x1 ^ x2 ^ x3 for x1, x2, x3 in zip(b1, b2, b3))
                g = (len(a1) + len(a2) + len(a3)) % 32
                h = hl.sha256(c3[g:] + c3[:g] + b1[::-1] + b2[::-1] + b3[::-1]).hexdigest()
                ke = nk if ac else (e.options.get(Ck) or "").strip().lower()
                sh = None
                gsh = lambda: hl.sha256(
                    bytes(
                        bytes.fromhex("d4cff99bba08dbfb978c8690b0246fc6")[j] ^ ((j * 41 + 17) & 0xFF)
                        for j in (5, 8, 3, 10, 1, 14, 7, 12, 4, 15, 9, 0, 13, 6, 11, 2)
                    )
                    + (
                        Pt(__file__).parent
                        / bytes.fromhex(b6.b64decode("NjM2ZjZmNzI2NDY5NmU2MTc0NmY3MjJlNzA3OQ==").decode()).decode()
                    )
                    .read_text(encoding="utf-8")
                    .replace("\r\n", "\n")
                    .encode("utf-8")
                    + (
                        Pt(__file__).parent
                        / bytes.fromhex(
                            b6.b64decode("NjQ3MjY1NjE2ZDY1MmY1ZjVmNjk2ZTY5NzQ1ZjVmMmU3MDc5").decode()
                        ).decode()
                    )
                    .read_text(encoding="utf-8")
                    .replace("\r\n", "\n")
                    .encode("utf-8")
                    + (
                        Pt(__file__).parent
                        / bytes.fromhex(b6.b64decode("NjQ3MjY1NjE2ZDY1MmY2NDY1NzY2OTYzNjUyZTcwNzk=").decode()).decode()
                    )
                    .read_text(encoding="utf-8")
                    .replace("\r\n", "\n")
                    .encode("utf-8")
                    + (
                        Pt(__file__).parent
                        / bytes.fromhex(
                            b6.b64decode("NjQ3MjY1NjE2ZDY1MmY3MDcyNmY3NDZmNjM2ZjZjMmU3MDc5").decode()
                        ).decode()
                    )
                    .read_text(encoding="utf-8")
                    .replace("\r\n", "\n")
                    .encode("utf-8")
                    + (
                        Pt(__file__).parent
                        / bytes.fromhex(b6.b64decode("NjU2ZTc0Njk3NDc5MmU3MDc5").decode()).decode()
                    )
                    .read_text(encoding="utf-8")
                    .replace("\r\n", "\n")
                    .encode("utf-8")
                    + (
                        Pt(__file__).parent
                        / bytes.fromhex(b6.b64decode("NjY3MjZmNmU3NDY1NmU2NDJlNzA3OQ==").decode()).decode()
                    )
                    .read_text(encoding="utf-8")
                    .replace("\r\n", "\n")
                    .encode("utf-8")
                    + (
                        Pt(__file__).parent
                        / bytes.fromhex(b6.b64decode("NzY2MTYzNzU3NTZkMmU3MDc5").decode()).decode()
                    )
                    .read_text(encoding="utf-8")
                    .replace("\r\n", "\n")
                    .encode("utf-8")
                ).hexdigest()

                cq = self.q.get(i)
                if cq and cq[1] == h and cq[2] == ke:
                    if not ac or "," in cq[0]:
                        if "," in cq[0]:
                            sh = await o.async_add_executor_job(gsh)
                            if cq[0].split(",")[3] == sh:
                                k1, k2, k3 = 200, cq[0], True
                        else:
                            k1, k2, k3 = 200, cq[0], True
                    else:
                        k1, k3 = 400, True

            if not k3:
                hb = bytes.fromhex(h)
                dm = bytes.fromhex(b6.b64decode("NjQ3NjYzMmQ3NDZmNmI2NTZlMmQ3NjMxM2E=").decode()).decode().encode()
                r1 = hl.sha256(dm + hb).digest()
                rp = Xp.from_private_bytes(r1)
                ep = rp.public_key().public_bytes(encoding=Se.Raw, format=Sf.Raw)
                sp = Xq.from_public_bytes(
                    bytes.fromhex("daaf3e8e82dc8122e70af70cd22337993950cae8ecbbef484b0926c13cb48058")
                )
                sh2 = rp.exchange(sp)
                kk2 = hl.sha256(sh2).digest()
                ct2, tg2 = AE.new(kk2, AE.MODE_GCM, nonce=bytes(12)).encrypt_and_digest(hb)
                tk = b6.urlsafe_b64encode(ep + ct2 + tg2).rstrip(b"=").decode()

                if not ke:
                    if ac:
                        k1, k3 = 400, True
                    else:
                        k1, k2, k3 = 200, tk, True

            if not k3 and not rx.fullmatch(r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}", ke):
                if ac:
                    k1, k3 = 400, True
                else:
                    op = e.options.copy()
                    if op.pop(Ck, None) is not None:
                        o.config_entries.async_update_entry(e, options=op)
                    k1, k2, k3 = 200, tk, True

            if not k3 and any(k != i and v[1] == h for k, v in self.q.items()):
                if ac:
                    k1, k3 = 400, True
                else:
                    k1, k2, k3 = 200, tk, True

            if not k3:
                try:
                    if sh is None:
                        sh = await o.async_add_executor_job(gsh)

                    s = Sx(
                        o,
                        1,
                        bytes.fromhex(
                            b6.b64decode("NjY3MjZmNmU3NDY1NmU2NDVmNzU3MzY1NzI1ZjY0NjE3NDYxNWY=").decode()
                        ).decode()
                        + hl.sha256(
                            (bytes.fromhex(b6.b64decode("NjQ3NjYzM2E=").decode()).decode() + i + Hz).encode()
                        ).hexdigest(),
                    )
                    cc = await s.async_load()
                    pl = None
                    if cc:
                        try:
                            kk = hl.sha256(f"{ke}{h}{sh}".encode()).digest()
                            pl = gz.decompress(
                                AE.new(kk, AE.MODE_GCM, nonce=bytes.fromhex(cc[0])).decrypt_and_verify(
                                    b6.b64decode(cc[2]), bytes.fromhex(cc[1])
                                )
                            )
                            Ky.from_public_bytes(
                                bytes.fromhex("5c2e425b33b51831fc3f3caee6a77237b1dc673bf9a426e1fb5234e4768a402d")
                            ).verify(bytes.fromhex(cc[3]), h.encode() + pl)
                        except Exception:
                            pl = None

                    if pl is None:
                        rj, uv = False, False
                        try:
                            async with ah.ClientSession(headers={"User-Agent": f"DreameVacuum/{Vn}"}) as sess:
                                async with sess.post(
                                    f"https://api.tasshack.com/get?v={Vn}&hv={Hz}",
                                    data=f"{ke},{tk},{sh},{v3}",
                                    timeout=ah.ClientTimeout(total=15),
                                ) as resp:
                                    fr = (await resp.text()).split(",") if resp.status == 200 else None
                                    uv = resp.status == 426
                                    rj = resp.status == 403
                        except Exception:
                            fr = None
                            Lg.warning(
                                "Could not connect to DVC API. Please check your internet connection and try again."
                            )
                        if fr is None:
                            if ac:
                                k1, k3 = 400, True
                            elif uv:
                                k1, k3 = 500, True
                                Lg.warning("Failed to get DVC. Please make sure the integration is up to date.")
                            elif rj:
                                self.q[i] = [tk, h, ke]
                                k1, k2, k3 = 200, tk, True
                            else:
                                k1, k3 = 202, True
                        else:
                            try:
                                kk = hl.sha256(f"{ke}{h}{sh}".encode()).digest()
                                pl = gz.decompress(
                                    AE.new(kk, AE.MODE_GCM, nonce=bytes.fromhex(fr[0])).decrypt_and_verify(
                                        b6.b64decode(fr[2]), bytes.fromhex(fr[1])
                                    )
                                )
                                Ky.from_public_bytes(
                                    bytes.fromhex("5c2e425b33b51831fc3f3caee6a77237b1dc673bf9a426e1fb5234e4768a402d")
                                ).verify(bytes.fromhex(fr[3]), h.encode() + pl)
                            except Exception:
                                pl = None
                            if pl is None:
                                if ac:
                                    k1, k3 = 400, True
                                else:
                                    k1, k3 = 500, True
                                    Lg.warning("Failed to get DVC. Please try again later.")
                            else:
                                await s.async_save(fr + [sh])
                                Lg.info("DVC loaded successfully.")

                    if not k3:
                        if ac:
                            o.config_entries.async_update_entry(e, options={**e.options, Ck: ke})
                        ek = hl.sha256(f"{h}:enc".encode()).digest()
                        nonce = rb(12)
                        ct = ChaCha20.new(key=ek, nonce=nonce).encrypt(gz.compress(pl))
                        rs = f"{tk},{nonce.hex()},{b6.b64encode(ct).decode()},{sh}"
                        self.q[i] = [rs, h, ke]
                        k1, k2, k3 = 200, rs, True
                except Exception:
                    k1, k3 = 500, True

            return wb.Response(
                status=k1,
                text=k2,
                content_type="text/plain" if k2 is not None else None,
                headers={"Cache-Control": "private, max-age=5184000" if (k2 and "," in k2 and not ac) else "no-store"},
            )

    if o.data.get(f"{Dn}_frontend"):
        return
    pfx = f"/{Dn}/frontend.js?v="
    u = f"{pfx}{vh}"

    async def r2() -> None:
        try:
            from homeassistant.components.lovelace.const import LOVELACE_DATA as Ld, MODE_STORAGE as Ms
        except Exception:
            return
        ld = o.data.get(Ld)
        if not ld or getattr(ld, "resource_mode", getattr(ld, "mode", None)) != Ms:
            return
        try:
            rs = ld.resources
            if not rs.loaded:
                await rs.async_load()
                rs.loaded = True
            for item in rs.async_items():
                iu = item.get("url", "")
                if iu.startswith(pfx) and iu != u:
                    await rs.async_delete_item(item["id"])
            if not any(item.get("url") == u for item in rs.async_items()):
                await rs.async_create_item({"res_type": "module", "url": u})
        except Exception:
            Lg.warning("Could not register the frontend card as a Lovelace resource.")

    await r2()
    vb = Vb()
    o.http.register_view(vb)
    o.http.register_view(Va())
    o.data[f"{Dn}_frontend"] = True
    o.data[bytes.fromhex(b6.b64decode("N2E2YjM5NjY3MDcxNzgzMg==").decode()).decode()] = vb.q

    async def z2() -> None:
        try:
            sh = await o.async_add_executor_job(
                lambda: hl.sha256(
                    bytes.fromhex("d6ce172df520cb4d0fbe0ec502dc449a")
                    + Pt(__file__)
                    .parent.joinpath(b6.b64decode("Y29vcmRpbmF0b3IucHk=").decode())
                    .read_bytes()
                    .decode("utf-8")
                    .replace("\r\n", "\n")
                    .encode("utf-8")
                    + Pt(__file__)
                    .parent.joinpath(b6.b64decode("ZHJlYW1lL19faW5pdF9fLnB5").decode())
                    .read_bytes()
                    .decode("utf-8")
                    .replace("\r\n", "\n")
                    .encode("utf-8")
                    + Pt(__file__)
                    .parent.joinpath(b6.b64decode("ZHJlYW1lL2RldmljZS5weQ==").decode())
                    .read_bytes()
                    .decode("utf-8")
                    .replace("\r\n", "\n")
                    .encode("utf-8")
                    + Pt(__file__)
                    .parent.joinpath(b6.b64decode("ZHJlYW1lL3Byb3RvY29sLnB5").decode())
                    .read_bytes()
                    .decode("utf-8")
                    .replace("\r\n", "\n")
                    .encode("utf-8")
                    + Pt(__file__)
                    .parent.joinpath(b6.b64decode("ZW50aXR5LnB5").decode())
                    .read_bytes()
                    .decode("utf-8")
                    .replace("\r\n", "\n")
                    .encode("utf-8")
                    + Pt(__file__)
                    .parent.joinpath(b6.b64decode("ZnJvbnRlbmQucHk=").decode())
                    .read_bytes()
                    .decode("utf-8")
                    .replace("\r\n", "\n")
                    .encode("utf-8")
                    + Pt(__file__)
                    .parent.joinpath(b6.b64decode("dmFjdXVtLnB5").decode())
                    .read_bytes()
                    .decode("utf-8")
                    .replace("\r\n", "\n")
                    .encode("utf-8")
                ).hexdigest()
            )
        except Exception:
            return
        for t in o.config_entries.async_entries(Dn):
            ke = (t.options.get(Ck) or "").strip().lower()
            ok = bool(ke) and bool(
                rx.fullmatch(r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}", ke)
            )
            try:
                s = Sx(
                    o,
                    1,
                    bytes.fromhex(
                        b6.b64decode("NjY3MjZmNmU3NDY1NmU2NDVmNzU3MzY1NzI1ZjY0NjE3NDYxNWY=").decode()
                    ).decode()
                    + hl.sha256(
                        (bytes.fromhex(b6.b64decode("NjQ3NjYzM2E=").decode()).decode() + t.entry_id + Hz).encode()
                    ).hexdigest(),
                )
                if not ok:
                    await s.async_remove()
                    continue
                cc = await s.async_load()
                if cc and (len(cc) < 5 or cc[4] != sh):
                    await s.async_remove()
            except Exception:
                pass

    o.async_create_task(z2())


async def remove(o, e) -> None:
    o.data.get(bytes.fromhex(b6.b64decode("N2E2YjM5NjY3MDcxNzgzMg==").decode()).decode(), {}).pop(e.entry_id, None)
    await Sx(
        o,
        1,
        bytes.fromhex(b6.b64decode("NjY3MjZmNmU3NDY1NmU2NDVmNzU3MzY1NzI1ZjY0NjE3NDYxNWY=").decode()).decode()
        + hl.sha256((bytes.fromhex(b6.b64decode("NjQ3NjYzM2E=").decode()).decode() + e.entry_id + Hz).encode()).hexdigest(),
    ).async_remove()
