import test from "node:test";
import assert from "node:assert/strict";
import { fetchWithAuth } from "./fetch-with-auth.ts";
import { createGuardedGetClient, createDreameClient, DreameAuthenticationError } from "./guarded-get.mjs";

// Isolated fake HTTP authority. No network sockets, real users, tokens or robots.
// The official frontend helper is imported unchanged from tag 20260930.2.
const API_PATH = "dreame_vacuum/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa/bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";
const SECOND_API_PATH = `${API_PATH.slice(0, -1)}c`;
const HASS_URL = "https://fixture.invalid";
function fixture({ expired = false, token = "valid", refreshFails = false, status, responseFor, hassUrl = HASS_URL } = {}) {
  let serverToken = "valid";
  const stats = { protectedRequests: 0, refreshes: 0, invalidAuth: 0, banned: false };
  const requestedUrls = [];
  const auth = {
    data: { hassUrl, access_token: token },
    get accessToken() { return this.data.access_token; },
    expired,
    async refreshAccessToken() {
      stats.refreshes++;
      await Promise.resolve();
      if (refreshFails) throw new Error("Fixture refresh denied");
      serverToken = this.data.access_token = `refreshed-${stats.refreshes}`;
      this.expired = false;
    },
  };
  const fetchStub = async (url, options) => {
    stats.protectedRequests++;
    requestedUrls.push(url);
    if (stats.banned) return new Response("Forbidden", { status: 403 });
    const bearer = new Headers(options?.headers).get("authorization");
    if (bearer !== `Bearer ${serverToken}`) {
      stats.invalidAuth++;
      stats.banned = stats.invalidAuth >= 5;
      return new Response("Unauthorized", { status: 401 });
    }
    const responseStatus = typeof status === "function" ? status(url) : status;
    const response = responseFor
      ? responseFor(new URL(url))
      : new Response(responseStatus ? "Fixture error" : "fixture-payload", { status: responseStatus || 200 });
    if (response.status === 401) {
      stats.invalidAuth++;
      stats.banned = stats.invalidAuth >= 5;
    }
    return response;
  };
  const hass = {
    auth,
    // A pre-established WebSocket is independent of subsequent bearer expiry.
    connected: true,
    callApiRaw(method, path, parameters, headers) {
      return fetchWithAuth(this.auth, `${this.auth.data.hassUrl}/api/${path}`, { method, headers });
    },
  };
  return { auth, hass, stats, fetchStub, requestedUrls };
}

async function withFixture(options, callback) {
  const f = fixture(options);
  const oldFetch = globalThis.fetch;
  globalThis.fetch = f.fetchStub;
  try { await callback(f); } finally { globalThis.fetch = oldFetch; }
}

test("baseline: five direct stale bearer requests hit the model ban threshold", async () => {
  await withFixture({ expired: true, token: "expired" }, async ({ hass, stats }) => {
    const responses = await Promise.all(Array.from({ length: 5 }, () =>
      fetch(`${HASS_URL}/api/${API_PATH}`, {
        headers: { authorization: `Bearer ${hass.auth.data.access_token}` },
      })
    ));
    assert.deepEqual(responses.map(r => r.status), [401, 401, 401, 401, 401]);
    assert.equal(hass.connected, true);
    assert.equal(stats.refreshes, 0);
    assert.equal(stats.invalidAuth, 5);
    assert.equal(stats.banned, true);
  });
});

test("official HA helper refreshes an expired token before protected fetch", async () => {
  await withFixture({ expired: true, token: "expired" }, async ({ hass, stats }) => {
    const response = await hass.callApiRaw("GET", API_PATH);
    assert.equal(response.status, 200);
    assert.deepEqual(stats, { protectedRequests: 1, refreshes: 1, invalidAuth: 0, banned: false });
  });
});

test("official helper sends no protected request when token refresh fails", async () => {
  await withFixture({ expired: true, token: "expired", refreshFails: true }, async ({ hass, stats }) => {
    await assert.rejects(hass.callApiRaw("GET", API_PATH), /refresh denied/);
    assert.equal(stats.protectedRequests, 0);
    assert.equal(stats.refreshes, 1);
  });
});

test("candidate deduplicates five simultaneous loads and one refresh", async () => {
  await withFixture({ expired: true, token: "expired" }, async ({ hass, stats }) => {
    const getResponse = createGuardedGetClient();
    const responses = await Promise.all(Array.from({ length: 5 }, () => getResponse(hass, API_PATH)));
    assert.equal(new Set(responses).size, 5);
    const payloads = await Promise.all(responses.map(response => response.text()));
    assert.deepEqual(payloads, Array(5).fill("fixture-payload"));
    assert.deepEqual(stats, { protectedRequests: 1, refreshes: 1, invalidAuth: 0, banned: false });
  });
});

test("candidate sends no request when HA session is missing or disconnected", async () => {
  await withFixture({}, async ({ hass, stats }) => {
    const getResponse = createGuardedGetClient();
    await assert.rejects(getResponse({ ...hass, auth: undefined }, API_PATH), /not ready/);
    await assert.rejects(getResponse({ ...hass, auth: { accessToken: "" } }, API_PATH), /not ready/);
    await assert.rejects(getResponse({ ...hass, connected: false }, API_PATH), /not ready/);
    assert.equal(stats.protectedRequests, 0);
  });
});

test("failed bounded recovery latches unexpected 401 across different routes and later polls", async () => {
  await withFixture({ token: "revoked-or-clock-skewed", expired: false, status: 401 }, async ({ hass, stats }) => {
    const getResponse = createGuardedGetClient();
    const results = await Promise.allSettled(Array.from({ length: 5 }, (_, i) => getResponse(hass, `${API_PATH.slice(0, -1)}${i}`)));
    assert(results.every(r => r.status === "rejected" && r.reason.status === 401));
    await assert.rejects(getResponse(hass, API_PATH), { status: 401 });
    assert.equal(stats.protectedRequests, 2);
    assert.equal(stats.refreshes, 1);
    assert.equal(stats.invalidAuth, 2);
    assert.equal(stats.banned, false);
  });
});

test("candidate resumes after HA replaces the rejected session token", async () => {
  let deny = true;
  await withFixture({ token: "revoked-or-clock-skewed", expired: false, status: () => deny ? 401 : 200 }, async ({ hass, auth, stats }) => {
    const getResponse = createGuardedGetClient();
    await assert.rejects(getResponse(hass, API_PATH), { status: 401 });
    deny = false;
    await auth.refreshAccessToken(); // Simulates HA's own successful reauthentication.
    assert.equal((await getResponse(hass, API_PATH)).status, 200);
    assert.equal(stats.invalidAuth, 2);
    assert.equal(stats.protectedRequests, 3);
  });
});

test("candidate stops repeating forbidden bootstrap requests", async () => {
  await withFixture({ status: 403 }, async ({ hass, stats }) => {
    const getResponse = createGuardedGetClient();
    assert.equal((await getResponse(hass, API_PATH)).status, 403);
    assert.equal((await getResponse(hass, API_PATH)).status, 403);
    assert.equal(stats.protectedRequests, 1);
  });
});

test("different robots and duplicate consumers keep independent payloads and headers without caching success", async () => {
  const robots = new Map([
    [`/api/${API_PATH}`, "downstairs"],
    [`/api/${SECOND_API_PATH}`, "upstairs"],
  ]);
  await withFixture({ responseFor: url => {
    const robot = robots.get(url.pathname);
    assert(robot, "Only the requested robot routes may be dispatched");
    return new Response(`${robot} bootstrap`, { headers: { "x-fixture-robot": robot } });
  } }, async ({ hass, stats, requestedUrls }) => {
    const firstClient = createDreameClient();
    const secondClient = createDreameClient();
    const pending = [
      firstClient.loadCard(hass, API_PATH),
      secondClient.loadCard(hass, SECOND_API_PATH),
      secondClient.loadCard(hass, API_PATH),
    ];
    // Each card starts reading as soon as its own response arrives.
    const results = await Promise.all(pending.map(async request => {
      const response = await request;
      return { response, robot: response.headers.get("x-fixture-robot"), body: await response.text() };
    }));
    assert.equal(new Set(results.map(result => result.response)).size, 3);
    assert(results.every(result => result.response.status === 200));
    assert.deepEqual(results.map(({ robot, body }) => ({ robot, body })), [
      { robot: "downstairs", body: "downstairs bootstrap" },
      { robot: "upstairs", body: "upstairs bootstrap" },
      { robot: "downstairs", body: "downstairs bootstrap" },
    ]);
    results[0].response.headers.set("x-fixture-robot", "caller-only change");
    assert.equal(results[1].response.headers.get("x-fixture-robot"), "upstairs");
    assert.equal(results[2].response.headers.get("x-fixture-robot"), "downstairs");
    assert.deepEqual(requestedUrls.map(url => new URL(url).pathname), [`/api/${API_PATH}`, `/api/${SECOND_API_PATH}`]);

    const later = await firstClient.loadCard(hass, API_PATH);
    assert.equal(await later.text(), "downstairs bootstrap");
    assert.equal(later.headers.get("x-fixture-robot"), "downstairs");
    assert.deepEqual(stats, { protectedRequests: 3, refreshes: 0, invalidAuth: 0, banned: false });
  });
});

test("candidate preserves card-specific HTTP 202 and 500 status/body handling", async () => {
  for (const status of [202, 500]) {
    await withFixture({ status }, async ({ hass, stats }) => {
      const getResponse = createGuardedGetClient();
      const response = await getResponse(hass, API_PATH);
      assert.equal(response.status, status);
      assert.equal(await response.text(), "Fixture error");
      assert.deepEqual(stats, { protectedRequests: 1, refreshes: 0, invalidAuth: 0, banned: false });
    });
  }
});

// This is an original model of the inspected wrapper lifecycle, not copied
// proprietary source. The parent investigation confirmed these state decisions.
function wrapperModel(load, hass, apiPath = API_PATH) {
  const shared = new Map();
  let loading = false;
  let failed = false;
  let warning = false;
  let child = false;
  let authError = null;
  return {
    async hassUpdate(currentHass = hass) {
      hass = currentHass;
      if (authError?.canRetryWith(hass)) {
        authError = null;
        shared.delete(apiPath);
      }
      if (child || authError || loading || !(warning || !failed)) return;
      loading = true;
      try {
        let task = shared.get(apiPath);
        if (!task) {
          task = load(hass).then(response => {
            const result = response.status === 500 ? 2
              : response.status === 202 ? 3 : !response.ok ? 1 : response;
            if (typeof result === "number") shared.delete(apiPath);
            return result;
          });
          shared.set(apiPath, task);
        }
        const result = await task;
        if (typeof result === "number") {
          loading = false;
          failed = result === 2;
          warning = true;
        } else {
          child = true;
          loading = false;
          warning = false;
        }
      } catch (error) {
        loading = false;
        if (error instanceof DreameAuthenticationError) authError = error;
        else throw error;
      }
    },
    get loaded() { return child; },
    get authError() { return authError; },
  };
}

test("observed wrapper lifecycle: five successive hass updates repeat stale bearer and ban", async () => {
  await withFixture({ expired: true, token: "expired" }, async ({ hass, stats }) => {
    const wrapper = wrapperModel(() => fetch(`${HASS_URL}/api/${API_PATH}`, {
      headers: { authorization: `Bearer ${hass.auth.data.access_token}` },
    }));
    for (let i = 0; i < 5; i++) await wrapper.hassUpdate();
    assert.equal(wrapper.loaded, false);
    assert.deepEqual(stats, { protectedRequests: 5, refreshes: 0, invalidAuth: 5, banned: true });
  });
});

test("corrected wrapper lifecycle: first hass update refreshes and loads, next four do not refetch", async () => {
  await withFixture({ expired: true, token: "expired" }, async ({ hass, stats }) => {
    const client = createDreameClient();
    const wrapper = wrapperModel(() => client.loadCard(hass, API_PATH), hass);
    for (let i = 0; i < 5; i++) await wrapper.hassUpdate();
    assert.equal(wrapper.loaded, true);
    assert.deepEqual(stats, { protectedRequests: 1, refreshes: 1, invalidAuth: 0, banned: false });
  });
});

test("failed session refresh is terminal and is not retried on five hass updates", async () => {
  await withFixture({ expired: true, token: "expired", refreshFails: true }, async ({ hass, stats }) => {
    const client = createDreameClient();
    const wrapper = wrapperModel(() => client.loadCard(hass, API_PATH), hass);
    for (let i = 0; i < 5; i++) await wrapper.hassUpdate();
    assert(wrapper.authError instanceof DreameAuthenticationError);
    assert.equal(stats.refreshes, 1);
    assert.equal(stats.protectedRequests, 0);
  });
});

test("licence submission preserves GET key encoding without application deduplication or caching", async () => {
  await withFixture({ expired: true, token: "expired" }, async ({ hass, stats, requestedUrls }) => {
    const client = createDreameClient();
    const fixtureKey = "fixture-key-only";
    await Promise.all([client.activateLicence(hass, API_PATH, fixtureKey), client.activateLicence(hass, API_PATH, fixtureKey)]);
    await client.activateLicence(hass, API_PATH, fixtureKey);
    assert.equal(stats.refreshes, 1);
    assert.equal(stats.protectedRequests, 3);
    assert(requestedUrls.every(url => new URL(url).searchParams.get("k") === btoa(fixtureKey)));
  });
});

test("licence auth rejection remains a session error and never becomes invalid licence", async () => {
  await withFixture({ token: "rejected", expired: false }, async ({ hass, stats }) => {
    const client = createDreameClient();
    await assert.rejects(client.activateLicence(hass, API_PATH, "fixture-key-only"), error => {
      assert(error instanceof DreameAuthenticationError);
      assert.equal(error.status, 401);
      return true;
    });
    assert.equal(stats.protectedRequests, 1);
  });
});

test("old in-flight 401 retries once with a newer token without refreshing", async () => {
  let resolveResponse;
  let signalDispatch;
  const dispatched = new Promise(resolve => { signalDispatch = resolve; });
  let calls = 0;
  const auth = { expired: false, accessToken: "old", refreshAccessToken() { assert.fail("Newer token must be reused"); } };
  const hass = {
    auth, connected: true,
    callApiRaw(method, path, parameters, headers) {
      // Match HA's assignment immediately before dispatch, before a later
      // external token can arrive while this response is pending.
      headers.authorization = `Bearer ${auth.accessToken}`;
      calls++;
      if (calls > 1) return Promise.resolve(new Response("fresh-token-payload"));
      signalDispatch();
      return new Promise(resolve => { resolveResponse = resolve; });
    },
  };
  const client = createDreameClient();
  const pending = client.loadCard(hass, API_PATH);
  await dispatched;
  auth.accessToken = "fresh";
  resolveResponse(new Response("Unauthorized", { status: 401 }));
  assert.equal(await (await pending).text(), "fresh-token-payload");
  assert.equal(calls, 2);
});

test("403 suppresses only its bootstrap route and explicit retry can recover", async () => {
  let denyRoute = true;
  await withFixture({ status: url => denyRoute && new URL(url).pathname.endsWith(API_PATH) ? 403 : 200 }, async ({ hass, stats }) => {
    const client = createDreameClient();
    assert.equal((await client.loadCard(hass, API_PATH)).status, 403);
    assert.equal((await client.loadCard(hass, API_PATH)).status, 403);
    assert.equal(stats.protectedRequests, 1);
    assert.equal((await client.loadCard(hass, `${API_PATH.slice(0, -1)}c`)).status, 200);
    denyRoute = false;
    assert.equal((await client.retryAuthenticatedRequest(hass, API_PATH)).status, 200);
    assert.equal(stats.protectedRequests, 3);
  });
});

test("a bootstrap 403 does not block licence submission and successful activation clears it", async () => {
  let activated = false;
  await withFixture({ status: url => {
    if (new URL(url).searchParams.has("k")) activated = true;
    return activated ? 200 : 403;
  } }, async ({ hass, stats }) => {
    const client = createDreameClient();
    assert.equal((await client.loadCard(hass, API_PATH)).status, 403);
    assert.equal((await client.activateLicence(hass, API_PATH, "fixture-key-only")).status, 200);
    assert.equal((await client.loadCard(hass, API_PATH)).status, 200);
    assert.equal(stats.protectedRequests, 3);
  });
});

test("bootstrap path validation rejects activation query and external route without sending", async () => {
  await withFixture({}, async ({ hass, stats }) => {
    const client = createDreameClient();
    for (const path of [`${API_PATH}?k=fixture`, `/${API_PATH}`, "states", `${API_PATH}/../x`, "https://fixture.invalid"]) {
      await assert.rejects(client.loadCard(hass, path), /Invalid Dreame bootstrap/);
    }
    assert.equal(stats.protectedRequests, 0);
  });
});

test("wrapper resumes after an ordinary reconnect using the same valid token", async () => {
  await withFixture({}, async ({ hass, stats }) => {
    const client = createDreameClient();
    const wrapper = wrapperModel(() => client.loadCard(hass, API_PATH), hass);
    hass.connected = false;
    await wrapper.hassUpdate();
    const savedError = wrapper.authError;
    assert(savedError instanceof DreameAuthenticationError);
    assert.equal(savedError.canRetryWith(hass), false);
    assert.equal(wrapper.loaded, false);
    assert.equal(stats.protectedRequests, 0);
    hass.connected = true;
    assert.equal(savedError.canRetryWith(hass), true);
    await wrapper.hassUpdate();
    assert.equal(wrapper.loaded, true);
    assert.equal(wrapper.authError, null);
    assert.equal(stats.protectedRequests, 1);
  });
});

test("wrapper resumes after rejected auth when HA supplies a new valid token", async () => {
  let deny = true;
  await withFixture({ token: "rejected", status: () => deny ? 401 : 200 }, async ({ hass, auth, stats }) => {
    const client = createDreameClient();
    const wrapper = wrapperModel(() => client.loadCard(hass, API_PATH), hass);
    await wrapper.hassUpdate();
    assert.equal(wrapper.authError.status, 401);
    await wrapper.hassUpdate();
    assert.equal(stats.protectedRequests, 2);
    deny = false;
    await auth.refreshAccessToken();
    await wrapper.hassUpdate();
    assert.equal(wrapper.loaded, true);
    assert.equal(stats.protectedRequests, 3);
  });
});

test("saved errors let both failed wrappers resume after another client deliberately recovers with the same token", async () => {
  let denied = true;
  await withFixture({ status: () => denied ? 401 : undefined }, async ({ hass, auth, stats }) => {
    auth.refreshAccessToken = async () => { stats.refreshes++; };
    const firstClient = createDreameClient();
    const secondClient = createDreameClient();
    const wrappers = [
      wrapperModel(current => firstClient.loadCard(current, API_PATH), hass),
      wrapperModel(current => secondClient.loadCard(current, SECOND_API_PATH), hass, SECOND_API_PATH),
    ];
    await Promise.all(wrappers.map(wrapper => wrapper.hassUpdate()));
    const savedErrors = wrappers.map(wrapper => wrapper.authError);
    assert(savedErrors.every(error => error instanceof DreameAuthenticationError && error.status === 401));
    assert(savedErrors.every(error => error.canRetryWith(hass) === false));
    assert(wrappers.every(wrapper => wrapper.loaded === false));
    assert.deepEqual(stats, { protectedRequests: 2, refreshes: 1, invalidAuth: 2, banned: false });

    denied = false;
    const tokenBeforeRecovery = auth.accessToken;
    const response = await createDreameClient().retryAuthenticatedRequest(hass, API_PATH);
    assert.equal(await response.text(), "fixture-payload");
    assert.equal(auth.accessToken, tokenBeforeRecovery);
    assert.equal(stats.protectedRequests, 3);

    hass.connected = false;
    assert(savedErrors.every(error => error.canRetryWith(hass) === false));
    await Promise.all(wrappers.map(wrapper => wrapper.hassUpdate()));
    assert(wrappers.every(wrapper => wrapper.loaded === false));
    assert.equal(stats.protectedRequests, 3);

    hass.connected = true;
    assert(savedErrors.every(error => error.canRetryWith(hass) === true));
    await Promise.all(wrappers.map(wrapper => wrapper.hassUpdate()));
    assert(wrappers.every(wrapper => wrapper.loaded && wrapper.authError === null));
    await Promise.all(wrappers.map(wrapper => wrapper.hassUpdate()));
    assert.deepEqual(stats, { protectedRequests: 5, refreshes: 1, invalidAuth: 2, banned: false });
  });
});

test("a saved wrapper error accepts a replacement Auth with the same token once it is connected", async () => {
  let denied = true;
  await withFixture({ status: () => denied ? 401 : undefined }, async ({ hass, auth, stats }) => {
    auth.refreshAccessToken = async () => { stats.refreshes++; };
    const client = createDreameClient();
    const wrapper = wrapperModel(current => client.loadCard(current, API_PATH), hass);
    await wrapper.hassUpdate();
    const savedError = wrapper.authError;
    assert(savedError instanceof DreameAuthenticationError);
    assert.equal(savedError.status, 401);
    assert.equal(savedError.canRetryWith(hass), false);

    denied = false;
    const replacementAuth = {
      ...auth,
      data: { ...auth.data },
      get accessToken() { return this.data.access_token; },
    };
    const replacementHass = { ...hass, auth: replacementAuth, connected: false };
    assert.notEqual(replacementAuth, auth);
    assert.equal(replacementAuth.accessToken, auth.accessToken);
    assert.equal(savedError.canRetryWith(replacementHass), false);
    await wrapper.hassUpdate(replacementHass);
    assert.equal(wrapper.authError, savedError);
    assert.equal(wrapper.loaded, false);
    assert.equal(stats.protectedRequests, 2);

    replacementHass.connected = true;
    assert.equal(savedError.canRetryWith(replacementHass), true);
    await wrapper.hassUpdate(replacementHass);
    assert.equal(wrapper.loaded, true);
    assert.equal(wrapper.authError, null);
    assert.deepEqual(stats, { protectedRequests: 3, refreshes: 1, invalidAuth: 2, banned: false });
  });
});

test("explicit retry can recover a failed refresh with the same original token", async () => {
  await withFixture({ expired: true, token: "expired", refreshFails: true }, async ({ hass, auth, stats }) => {
    const client = createDreameClient();
    await assert.rejects(client.loadCard(hass, API_PATH), /could not be refreshed/);
    await assert.rejects(client.loadCard(hass, API_PATH), /could not be refreshed/);
    assert.equal(stats.refreshes, 1);
    auth.refreshAccessToken = async () => {
      stats.refreshes++;
      auth.data.access_token = "valid";
      auth.expired = false;
    };
    assert.equal((await client.retryAuthenticatedRequest(hass, API_PATH)).status, 200);
    assert.equal(stats.refreshes, 2);
    assert.equal(stats.protectedRequests, 1);
  });
});

test("independent client factories share expiry refresh and same-route deduplication", async () => {
  await withFixture({ expired: true, token: "expired" }, async ({ hass, stats }) => {
    const a = createDreameClient();
    const b = createDreameClient();
    const responses = await Promise.all([
      a.loadCard(hass, API_PATH), b.loadCard(hass, API_PATH),
      b.loadCard(hass, `${API_PATH.slice(0, -1)}c`),
    ]);
    assert(responses.every(response => response.status === 200));
    assert.equal(new Set(responses).size, 3);
    assert.deepEqual(stats, { protectedRequests: 2, refreshes: 1, invalidAuth: 0, banned: false });
  });
});

test("unexpected 401 recovers once and queued other-factory robot uses that token", async () => {
  await withFixture({ token: "unexpectedly-rejected" }, async ({ hass, stats }) => {
    const responses = await Promise.all([
      createDreameClient().loadCard(hass, API_PATH),
      createDreameClient().loadCard(hass, `${API_PATH.slice(0, -1)}c`),
    ]);
    assert(responses.every(response => response.status === 200));
    assert.deepEqual(stats, { protectedRequests: 3, refreshes: 1, invalidAuth: 1, banned: false });
  });
});

test("failed recovery blocks queued factories, later new cards and repeated state updates", async () => {
  await withFixture({ token: "unexpectedly-rejected", status: 401 }, async ({ hass, stats }) => {
    const results = await Promise.allSettled([
      createDreameClient().loadCard(hass, API_PATH),
      createDreameClient().loadCard(hass, `${API_PATH.slice(0, -1)}c`),
    ]);
    assert(results.every(result => result.status === "rejected" && result.reason.status === 401));
    for (let i = 0; i < 5; i++) {
      const client = createDreameClient();
      const wrapper = wrapperModel(() => client.loadCard(hass, `${API_PATH.slice(0, -1)}d`), hass);
      await wrapper.hassUpdate();
      await wrapper.hassUpdate();
      assert.equal(wrapper.authError.status, 401);
    }
    assert.deepEqual(stats, { protectedRequests: 2, refreshes: 1, invalidAuth: 2, banned: false });
  });
});

test("later rejection of successful recovery token cannot start another refresh chain", async () => {
  const secondPath = `${API_PATH.slice(0, -1)}c`;
  await withFixture({ token: "unexpectedly-rejected", status: url => url.endsWith(secondPath) ? 401 : 200 }, async ({ hass, stats }) => {
    const results = await Promise.allSettled([
      createDreameClient().loadCard(hass, API_PATH),
      createDreameClient().loadCard(hass, secondPath),
    ]);
    assert.equal(results[0].status, "fulfilled");
    assert.equal(results[1].status, "rejected");
    assert.equal(results[1].reason.status, 401);
    await assert.rejects(createDreameClient().loadCard(hass, `${API_PATH.slice(0, -1)}d`), { status: 401 });
    assert.deepEqual(stats, { protectedRequests: 3, refreshes: 1, invalidAuth: 2, banned: false });
  });
});

test("fresh preflight token rejection stops after one GET without a second refresh", async () => {
  await withFixture({ expired: true, token: "expired", status: 401 }, async ({ hass, stats }) => {
    const results = await Promise.allSettled([
      createDreameClient().loadCard(hass, API_PATH),
      createDreameClient().loadCard(hass, `${API_PATH.slice(0, -1)}c`),
    ]);
    assert(results.every(result => result.status === "rejected" && result.reason.status === 401));
    await assert.rejects(createDreameClient().loadCard(hass, API_PATH), { status: 401 });
    assert.deepEqual(stats, { protectedRequests: 1, refreshes: 1, invalidAuth: 1, banned: false });
  });
});

test("successful ordinary preflight does not spend a later unexpected-401 recovery budget", async () => {
  let rejectNext = false;
  await withFixture({ expired: true, token: "expired", status: () => {
    if (rejectNext) { rejectNext = false; return 401; }
    return 200;
  } }, async ({ hass, stats }) => {
    assert.equal((await createDreameClient().loadCard(hass, API_PATH)).status, 200);
    rejectNext = true;
    assert.equal((await createDreameClient().loadCard(hass, `${API_PATH.slice(0, -1)}c`)).status, 200);
    assert.deepEqual(stats, { protectedRequests: 3, refreshes: 2, invalidAuth: 1, banned: false });
  });
});

test("a refresh returning the same token string still spends the shared recovery budget", async () => {
  await withFixture({ token: "rejected" }, async ({ hass, auth, stats }) => {
    auth.refreshAccessToken = async () => { stats.refreshes++; };
    await assert.rejects(createDreameClient().loadCard(hass, API_PATH), { status: 401 });
    await assert.rejects(createDreameClient().loadCard(hass, `${API_PATH.slice(0, -1)}c`), { status: 401 });
    assert.deepEqual(stats, { protectedRequests: 2, refreshes: 1, invalidAuth: 2, banned: false });
  });
});

test("separate HA Auth objects retain independent queues and failure circuits", async () => {
  const a = fixture({ token: "rejected", status: 401, hassUrl: "https://first.fixture.invalid" });
  const b = fixture({ token: "expired", expired: true, hassUrl: "https://second.fixture.invalid" });
  const previousFetch = globalThis.fetch;
  globalThis.fetch = (url, options) => url.startsWith(a.auth.data.hassUrl) ? a.fetchStub(url, options) : b.fetchStub(url, options);
  try {
    const client = createDreameClient();
    const results = await Promise.allSettled([client.loadCard(a.hass, API_PATH), client.loadCard(b.hass, API_PATH)]);
    assert.equal(results[0].status, "rejected");
    assert.equal(results[1].status, "fulfilled");
    assert.equal((await createDreameClient().loadCard(b.hass, `${API_PATH.slice(0, -1)}c`)).status, 200);
    await assert.rejects(createDreameClient().loadCard(a.hass, API_PATH), { status: 401 });
    assert.deepEqual(a.stats, { protectedRequests: 2, refreshes: 1, invalidAuth: 2, banned: false });
    assert.deepEqual(b.stats, { protectedRequests: 2, refreshes: 1, invalidAuth: 0, banned: false });
  } finally { globalThis.fetch = previousFetch; }
});

test("late retry rejection cannot poison a third externally supplied token", async () => {
  const responses = [];
  const starts = [];
  const started = [0, 1].map(i => new Promise(resolve => { starts[i] = resolve; }));
  let calls = 0;
  const auth = { expired: false, accessToken: "token-0", refreshAccessToken() { assert.fail("External tokens must be reused"); } };
  const hass = {
    auth, connected: true,
    callApiRaw(method, path, parameters, headers) {
      headers.authorization = `Bearer ${auth.accessToken}`;
      const call = calls++;
      if (call >= 2) return Promise.resolve(new Response("third-token-payload"));
      starts[call]();
      return new Promise(resolve => { responses[call] = resolve; });
    },
  };
  const pending = createDreameClient().loadCard(hass, API_PATH);
  await started[0];
  auth.accessToken = "token-1";
  responses[0](new Response("Unauthorized", { status: 401 }));
  await started[1];
  auth.accessToken = "token-2";
  responses[1](new Response("Unauthorized", { status: 401 }));
  await assert.rejects(pending, error => error.status === 401 && error.canRetryWith(hass));
  assert.equal(await (await createDreameClient().loadCard(hass, API_PATH)).text(), "third-token-payload");
  assert.equal(calls, 3);
});

test("network failure after recovery does not refund the session recovery budget", async () => {
  let calls = 0;
  let refreshes = 0;
  const auth = {
    expired: false, accessToken: "token-0",
    async refreshAccessToken() { refreshes++; this.accessToken = "token-1"; },
  };
  const hass = {
    auth, connected: true,
    async callApiRaw() {
      calls++;
      if (calls === 2) throw new Error("Fixture transport failed");
      return new Response("Unauthorized", { status: 401 });
    },
  };
  await assert.rejects(createDreameClient().loadCard(hass, API_PATH), /transport failed/);
  await assert.rejects(createDreameClient().loadCard(hass, `${API_PATH.slice(0, -1)}c`), { status: 401 });
  await assert.rejects(createDreameClient().loadCard(hass, `${API_PATH.slice(0, -1)}d`), { status: 401 });
  assert.equal(calls, 3);
  assert.equal(refreshes, 1);
});

test("explicit retry reset is queued behind the prior failed recovery", async () => {
  let requests = 0;
  await withFixture({ status: () => ++requests <= 2 ? 401 : 200 }, async ({ hass, stats }) => {
    const oldRequest = createDreameClient().loadCard(hass, API_PATH);
    const retry = createDreameClient().retryAuthenticatedRequest(hass, API_PATH);
    const results = await Promise.allSettled([oldRequest, retry]);
    assert.equal(results[0].status, "rejected");
    assert.equal(results[1].status, "fulfilled");
    assert.equal(results[1].value.status, 200);
    assert.deepEqual(stats, { protectedRequests: 3, refreshes: 1, invalidAuth: 2, banned: false });
  });
});

test("ordinary expiry renewal starts a new budget after an earlier successful 401 recovery", async () => {
  let rejectNext = false;
  await withFixture({ token: "unexpectedly-rejected", status: () => {
    if (rejectNext) { rejectNext = false; return 401; }
    return 200;
  } }, async ({ hass, auth, stats }) => {
    // T0 rejection -> forced T1 recovery succeeds and spends generation budget.
    assert.equal((await createDreameClient().loadCard(hass, API_PATH)).status, 200);
    assert.equal(stats.refreshes, 1);
    // Later normal expiry renews T1 -> T2 and starts a new generation.
    auth.expired = true;
    assert.equal((await createDreameClient().loadCard(hass, `${API_PATH.slice(0, -1)}c`)).status, 200);
    assert.equal(stats.refreshes, 2);
    // A later unexpected T2 rejection has one recovery available: T2 -> T3.
    rejectNext = true;
    assert.equal((await createDreameClient().loadCard(hass, `${API_PATH.slice(0, -1)}d`)).status, 200);
    assert.deepEqual(stats, { protectedRequests: 5, refreshes: 3, invalidAuth: 2, banned: false });
  });
});

test("exact-deadline refresh failure inside HA helper is latched across factories", async () => {
  let calls = 0;
  let refreshes = 0;
  const auth = {
    expired: false, accessToken: "deadline-token",
    async refreshAccessToken() { refreshes++; throw new Error("Fixture refresh transport failed"); },
  };
  const hass = {
    auth, connected: true,
    async callApiRaw() {
      calls++;
      auth.expired = true; // Deadline crossed after our preflight.
      await auth.refreshAccessToken();
      assert.fail("Rejected refresh must not send the protected request");
    },
  };
  await assert.rejects(createDreameClient().loadCard(hass, API_PATH), /authenticated request could not complete/);
  await assert.rejects(createDreameClient().loadCard(hass, `${API_PATH.slice(0, -1)}c`), /authenticated request could not complete/);
  assert.equal(calls, 1);
  assert.equal(refreshes, 1);
});
