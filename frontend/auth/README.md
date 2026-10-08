# Proposed Dreame authentication coordinator

This fixture makes no network requests and changes no Home Assistant or tablet state. It is an integration candidate plus a model of the reported failure, not a patched or fully executed copy of the Dreame card.

This draft proposes shared authentication recovery for all Dreame cards using the same HA Auth object on one page. The code is not imported by the packaged frontend. The suite contains 74 passing tests, all authored for this proposal. Eighteen selected deliberately introduced faults were detected during review. Sanitized results are recorded in `validation/regression-review.json` and `validation/loader-feasibility.json`; the latter describes 13 separate exploratory scenarios, not additional runnable tests in this directory.

Run using Node 24:

```sh
cd frontend/auth
node --test *.test.mjs
```

## What the tests establish

The baseline reads `hass.auth.data.access_token` and sends it directly in a bearer header. Five synthetic expired-token requests trigger a model ban threshold of five, even while `hass.connected` remains true. This models the confirmed installed loader pattern; it does not recover the historical request header or prove the incident token's expiry time.

The correction invokes Home Assistant's existing `callApiRaw` path. The test calls the unchanged, pinned `fetchWithAuth` function from frontend tag `20260930.2`: it refreshes an expired access token before sending the protected request, and does not send that request if refresh fails. The test's Auth and HTTP server are fake, not a running Home Assistant instance.

The candidate shares one module-level queue, failure circuit and recovery budget per HA Auth object across every card and every `createDreameClient()` consumer in the same loaded page/module. Overlapping bootstrap GETs to the same endpoint are deduplicated. Each caller owns an independent Response body: the helper creates clones only for additional waiting consumers and gives the original to the last consumer. Activation returns its original response directly. Different Auth objects are isolated. This does not coordinate unrelated Home Assistant requests or other browser tabs/devices.

An unexpected bootstrap 401 has one bounded recovery opportunity per session generation. If HA supplied a newer token while the request was pending, the request retries once with that token. Otherwise it refreshes once and retries. A token just refreshed during this operation's normal expiry preflight is not refreshed again when immediately rejected. Failed recovery closes the session circuit for all queued/later cards, including newly constructed clients. A successful forced-recovery token retains the spent budget, so a later rejection on another card cannot trigger a refresh chain. Even a refresh returning the same token string spends the budget.

An external token replacement, a later successful normal expiry renewal, or a deliberate user recovery starts a new generation. Overlapping explicit recovery calls share one pending recovery episode across routes and reset the budget once; same-route calls share their pending request. A later deliberate retry after that episode finishes can start another bounded attempt. A blocked unchanged token cannot automatically renew itself out of the failure circuit. Ordinary successful expiry preflight does not permanently consume a later unexpected-401 recovery opportunity.

For the pinned HA transport, the helper records the token assigned to each request's Authorization header after any internal refresh. It also observes whether HA replaced its Auth data object before that assignment. The pinned Auth implementation replaces this object when refreshing, allowing the coordinator to recognise renewal even when the bearer string is unchanged. It observes the per-request headers object passed through `callApiRaw`; it does not replace native/global fetch or mutate HA's shared Auth object. This makes failures refer to the credential actually dispatched, while a later external renewal is not attributed to the earlier request. A rejection immediately after an internal expiry refresh stops without another refresh; a successful normal renewal opens a new recovery generation even with the same bearer.

If a future transport no longer writes the supplied headers object and the token or Auth data object changes during dispatch, the helper conservatively binds a rejection to the current credentials. That fallback may require deliberate recovery even if the new token is valid. A copied-headers fixture verifies the conservative same-bearer renewal case. Exact late-token attribution is established for the pinned HA helper, not for an unobserved transport.

HTTP 202/500 status and response body remain available to the existing card logic. A bootstrap 403 is consumed once and cached as body bytes, status, status text and headers, then reconstructed with an independent body for each caller. Native URL/type/redirect metadata is not retained for these reconstructed denials. Failed body reads are not cached. The denial remains endpoint-specific; explicit retry, successful licence submission, or a changed token can clear it. Dreame can itself return 403, so it must not automatically be called an authentication or licence failure. Discarded 401 bodies are cancelled before refreshing, retrying or throwing. Licence submission is never automatically replayed, including after HTTP 401.

The fixture also models the confirmed wrapper lifecycle: unsuccessful bootstrap returns numeric state 1, releases the loading guard and clears the shared promise; another hass update retries. Five successive updates cause five 401s with the original direct-token pattern. With the candidate, the first update refreshes once and loads; the next four do not refetch. The investigation separately executed the original installed wrapper in an isolated VM; that evidence is not duplicated in this fixture.

## Integration boundaries

- Import the helper from one shared module. Replace bootstrap fetch with `client.loadCard(hass, apiPath)` and preserve the existing payload decoder. A shared client instance is convenient, but independent factories still use the module-level WeakMap keyed by HA Auth; never copy the module's session state into each card instance.
- `callApiRaw` takes the path without `/api/`; retain the existing version suffix and device ID construction.
- Keep the current 202/500 handling and payload transformation/evaluation unchanged.
- In the card's lifecycle, catch `DreameAuthenticationError` separately from numeric loader results. Store the exception, stop the current initialization and show a session readiness/recovery message. On a later hass update, consult `error.canRetryWith(hass)` before clearing the error, removing the rejected shared initialization promise for this card, and restarting initialization: disconnected/not-ready errors recover when the same session connects; terminal HTTP 401/refresh failures require a changed token/Auth object or a deliberate generation reset. This also handles an old request's rejection after a fresh token was already supplied. Never expose or log bearer values. A refresh exception may be a network problem, so do not claim the user logged out solely from that exception; reload/sign-in remains a recovery path if HA has not refreshed itself.
- Preserve typed authentication errors through the bootstrap's numeric-result catch. Handle rejection in both the shared initialization promise's bookkeeping and its asynchronous preview continuation, and remove only the matching rejected promise. Otherwise a typed failure can be swallowed or leave an unhandled rejection outside the wrapper's outer catch.
- `client.retryAuthenticatedRequest(hass, apiPath)` provides the plumbing for an explicit, user-triggered recovery attempt, including token refresh when required. No retry control or other UI/UX is implemented here; the maintainer can decide whether and how to expose this capability. If exposed, clear the card's displayed error and rejected shared initialization promise as part of that same user action. The first pending manual recovery resets the budget inside the queue after older requests; overlapping manual calls across routes share that reset. After the episode finishes, a later deliberate retry can start a new bounded attempt even with the same token. Never invoke this reset from each hass update or card construction, and never use it to replay licence activation. Preserve response body/status so the integration can explain a device-specific denial separately from HA's already-banned response.
- Invoke `client.activateLicence(hass, apiPath, normalizedKey)` only from the existing user-submit handler. It preserves the inspected GET plus `?k=encodeURIComponent(btoa(key))` shape; leave existing key normalization in the caller. The helper has no application cache, deduplication or automatic replay for submissions. The investigation verified that the installed integration sends `Cache-Control: no-store` for activation responses; preserve that behaviour. Do not classify HTTP 401 as a bad key. Other activation statuses remain available to the existing handler.
- Keep the existing per-card loading/shared-promise guard through the entire response-body read, payload transformation/evaluation, and child creation. Successful request deduplication ends at response distribution; 403 responses additionally finish the denial-body snapshot before leaving the queue. Neither replaces the card's complete initialization guard.
- HTTP transport failures with a still-valid token are passed to the caller's existing failure/backoff handling; a spent recovery budget is not refunded. Refresh failures are latched because retrying them can hammer `/auth/token`. If the unchanged token is expired after `callApiRaw` itself throws, that ambiguous request/refresh failure is also latched to cover a deadline crossing inside HA's helper; the message does not claim whether networking or authentication caused it.
- This candidate does not monkeypatch `fetch`, change HTTP ban settings, alter accounts, install long-lived tokens, or bypass licence checks. The test alone stubs global fetch inside its own Node process.
- Thirteen separate offline feasibility scenarios passed using adapted copies of the installed wrapper and activation methods with simulated HA, HTTP and browser dependencies. The wrapper probes preserved the resource-version guard and cryptographic/payload section unchanged; the activation probes preserved existing response handling without replaying submissions or classifying HA authentication failures as invalid keys. These are exploratory probes, not additional tests in this suite.
- Full module packaging, licensed card rendering and Android/WebView acceptance remain unverified. The compressed JavaScript in `const.py` carries a `PROPRIETARY AND CONFIDENTIAL` notice, so an installed modified fork has not been tested pending maintainer guidance. Integration can follow the maintainer's source/build process or an approved version-pinned loader build; this proposal does not modify the packaged frontend.

## Maintainer acceptance scenarios

There are 74 passing offline tests. The key synthetic results are:

| Scenario in one Auth session | Refreshes | Protected requests | Result |
| --- | ---: | ---: | --- |
| Expired token; two devices, separate factories, overlapping duplicate | 1 | 2 | One successful GET per device; duplicate shares its request. |
| Unexpected 401 on A; queued B uses recovered token | 1 | 3 | A original plus one successful retry; B succeeds. |
| A recovery also returns 401; B queued and new C constructed later | 1 | 2 | Session blocked; B/C/repeated updates send nothing. |
| A recovery succeeds; its token then rejected by B | 1 | 3 | B stops without another refresh; later cards send nothing. |
| Expiry preflight's fresh token immediately rejected | 1 | 1 | No second refresh or protected request. |
| A old-token request gets 401 after an external fresh token arrives | 0 | 2 | Retry uses the newer token and succeeds. |
| Two overlapping explicit retries after an initial failed recovery | 1 additional | 2 additional | One manual recovery, including across separate client factories. |
| Different-route explicit retries overlap and the first fails | 1 | 2 | The other route remains blocked without its own recovery reset. |
| HA refreshes internally just before a rejected activation request | 1 | 1 | Failure is bound to the dispatched token; later loads remain blocked. |
| HA refreshes internally just before bootstrap 403 | 1 | 1 | The next load reuses the denial snapshot without another request. |
| HA refreshes internally, returning the same bearer, then bootstrap gets 401 | 1 | 1 | The renewed credential is rejected once; queued and later cards send nothing. |
| A manual retry finishes while B remains pending, then another retry joins | 1 additional | 3 additional | The joining retry retains the active episode's spent budget and cannot reopen recovery. |

Response regressions cover cancellation by one or all shared consumers, independent streamed-body reads, original activation ownership, cleanup of discarded 401s, and 403 snapshot invalidation and read failure. The strengthened cases also prove that pending cancellation cannot hold recovery open, failed partial cloning releases all allocated branches, failed activation retains cached denials, and recovery of one route preserves another route's denial.

Cross-card cases use different robot bodies and headers and consume them immediately. Other cases prove saved card errors become retryable after deliberate recovery or Auth replacement, separate sessions make independent progress, and valid-token HTTP 202/500 responses do not cause a refresh. Controlled promises establish ordering; five-second deadlines detect missing progress and are not assertions about normal response speed.

At the earlier functional-review checkpoint, 19 of 22 new regressions failed against the pre-fix coordinator. The later test review added 17 cases and strengthened existing assertions. Two same-token renewal cases failed before the Auth-data observation correction; both now pass. All 18 selected deliberate faults are detected by the final suite. These targeted checks do not constitute exhaustive mutation testing.

In the real built card, verify an idle dashboard across the 30-minute access-token lifetime, then open both robot cards. The protected bootstrap must follow any necessary token refresh, and the cards must render. Verify repeated hass updates, separate card factories, ordinary disconnect/reconnect, denied refresh and explicit recovery, old requests resolving after token changes, device-specific 403, licence submission statuses, and reload after successful activation. Confirm there is no IP-ban burst with the configured threshold unchanged. Test on the Galaxy tablet's WebView and an ordinary browser; preserve existing access controls. Offline tests do not establish rebuilt-card or physical-tablet acceptance.

## Source provenance

Inspected on 8 October 2026. HA core `2026.10.0` declares `home-assistant-frontend==20260930.2`; that frontend declares `home-assistant-js-websocket` `9.7.1`.

| Source | Finding |
| --- | --- |
| [HA core frontend manifest](https://github.com/home-assistant/core/blob/2026.10.0/homeassistant/components/frontend/manifest.json) | Exact frontend dependency version. |
| [Frontend package.json](https://github.com/home-assistant/frontend/blob/20260930.2/package.json) | Exact js-websocket dependency version. |
| [fetch-with-auth.ts](https://github.com/home-assistant/frontend/blob/20260930.2/src/util/fetch-with-auth.ts) | Refresh expired auth, then read current accessToken for HTTP. |
| [hass-call-api.ts](https://github.com/home-assistant/frontend/blob/20260930.2/src/util/hass-call-api.ts) | callApiRaw preserves Response and delegates authentication to fetchWithAuth. |
| [Auth class](https://github.com/home-assistant/home-assistant-js-websocket/blob/9.7.1/lib/auth.ts) | accessToken is a plain getter; refresh is explicit. No ensureValidAccessToken API in this version. |
| [WebSocket authentication](https://github.com/home-assistant/core/blob/2026.10.0/homeassistant/components/websocket_api/auth.py) | Initial bearer validation creates ActiveConnection; refresh-token revocation closes the connection. |
| [HTTP ban middleware](https://github.com/home-assistant/core/blob/2026.10.0/homeassistant/components/http/ban.py) | Unauthorized requests increment the IP counter; banned IPs receive Forbidden. |
| [Authentication API documentation](https://developers.home-assistant.io/docs/auth_api/) | Short-lived bearer tokens require refresh; HTTP and WebSocket authentication are separate request paths. |

`fetch-with-auth.ts` is copied unchanged for a deterministic offline test. Its SHA-256 is `0a046f030835437beb6caafa0a6b3ac94be72277c14ceb61d9cf442b31158fb8`. The upstream Apache 2.0 licence is retained in `HA-frontend-LICENSE`.
