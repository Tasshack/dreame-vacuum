import test from "node:test";
import assert from "node:assert/strict";
import { fetchWithAuth } from "./fetch-with-auth.ts";
import { createDreameClient, DreameAuthenticationError } from "./guarded-get.mjs";

// Fake authority only. Every protected call uses the unchanged pinned HA helper,
// including its supported per-request headers parameter and expiry renewal.
const PATH_A = `dreame_vacuum/${"a".repeat(32)}/${"b".repeat(32)}`;
const PATH_B = `${PATH_A.slice(0, -1)}c`;
const PATH_C = `${PATH_A.slice(0, -1)}d`;

function deferred() {
  let resolve;
  const promise = new Promise(done => { resolve = done; });
  return { promise, resolve };
}

async function settlesWithin(promise, message) {
  let timer;
  try {
    return await Promise.race([
      promise,
      new Promise((_, reject) => { timer = setTimeout(() => reject(new Error(message)), 5000); }),
    ]);
  } finally {
    clearTimeout(timer);
  }
}

async function withAuthority({
  beforeHelper = () => {},
  respond,
  refreshedToken = ({ refresh }) => `fixture-refreshed-${refresh}`,
}, callback) {
  const stats = { protectedRequests: 0, refreshes: 0 };
  const auth = {
    data: { access_token: "fixture-token-0" },
    get accessToken() { return this.data.access_token; },
    set accessToken(token) { this.data = { ...this.data, access_token: token }; },
    expired: false,
    async refreshAccessToken() {
      const refresh = ++stats.refreshes;
      const previousToken = this.accessToken;
      await Promise.resolve();
      // The pinned HA Auth replaces its data object on successful refresh,
      // including when the returned access-token string happens to be unchanged.
      this.data = { ...this.data, access_token: refreshedToken({ refresh, previousToken }) };
      this.expired = false;
    },
  };
  let rawCalls = 0;
  const hass = {
    auth,
    connected: true,
    callApiRaw(method, path, _parameters, headers) {
      assert.equal(method, "GET");
      beforeHelper({ auth, call: ++rawCalls, path });
      return fetchWithAuth(auth, `https://fixture.invalid/api/${path}`, { method, headers });
    },
  };
  const previousFetch = globalThis.fetch;
  globalThis.fetch = async (url, init) => respond({
    url: new URL(url),
    // Synthetic fixture values only; these never come from the user's HA.
    bearer: new Headers(init.headers).get("authorization"),
    call: ++stats.protectedRequests,
    auth,
  });
  try {
    await callback({ auth, hass, stats });
  } finally {
    globalThis.fetch = previousFetch;
  }
}

function assertAuthFailures(results) {
  assert(results.every(result => result.status === "rejected"));
  assert(results.every(result => result.reason instanceof DreameAuthenticationError));
  assert(results.every(result => result.reason.status === 401));
}

test("overlapping manual retries from independent clients share one same-route attempt", async () => {
  await withAuthority({ respond: () => new Response("Denied", { status: 401 }) }, async ({ hass, stats }) => {
    await assert.rejects(createDreameClient().loadCard(hass, PATH_A), { status: 401 });
    assert.deepEqual(stats, { protectedRequests: 2, refreshes: 1 });

    const results = await Promise.allSettled([
      createDreameClient().retryAuthenticatedRequest(hass, PATH_A),
      createDreameClient().retryAuthenticatedRequest(hass, PATH_A),
    ]);
    assertAuthFailures(results);
    assert.deepEqual(stats, { protectedRequests: 4, refreshes: 2 });
  });
});

test("overlapping manual retries on different routes share the failure circuit and permit a later deliberate retry", async () => {
  await withAuthority({ respond: () => new Response("Denied", { status: 401 }) }, async ({ hass, stats }) => {
    await assert.rejects(createDreameClient().loadCard(hass, PATH_A), { status: 401 });
    const results = await Promise.allSettled([
      createDreameClient().retryAuthenticatedRequest(hass, PATH_A),
      createDreameClient().retryAuthenticatedRequest(hass, PATH_B),
    ]);
    assertAuthFailures(results);
    assert.deepEqual(stats, { protectedRequests: 4, refreshes: 2 });
    await assert.rejects(createDreameClient().loadCard(hass, PATH_C), { status: 401 });
    assert.deepEqual(stats, { protectedRequests: 4, refreshes: 2 });

    await assert.rejects(createDreameClient().retryAuthenticatedRequest(hass, PATH_C), { status: 401 });
    assert.deepEqual(stats, { protectedRequests: 6, refreshes: 3 });
  });
});

test("the first manual retry waits for older automatic work and overlapping callers receive independent bodies", async () => {
  const firstStarted = deferred();
  const firstResponse = deferred();
  await withAuthority({ respond: ({ call }) => {
    if (call === 1) {
      firstStarted.resolve();
      return firstResponse.promise;
    }
    return call === 2
      ? new Response("Denied", { status: 401 })
      : new Response("Recovered card");
  } }, async ({ hass, stats }) => {
    const oldRequest = createDreameClient().loadCard(hass, PATH_A);
    await firstStarted.promise;
    const manualA = createDreameClient().retryAuthenticatedRequest(hass, PATH_A);
    const manualB = createDreameClient().retryAuthenticatedRequest(hass, PATH_A);
    firstResponse.resolve(new Response("Denied", { status: 401 }));
    const results = await Promise.allSettled([oldRequest, manualA, manualB]);
    assert.equal(results[0].status, "rejected");
    assert.equal(results[1].status, "fulfilled");
    assert.equal(results[2].status, "fulfilled");
    assert.notEqual(results[1].value, results[2].value);
    assert.deepEqual(await Promise.all([results[1].value.text(), results[2].value.text()]), ["Recovered card", "Recovered card"]);
    assert.deepEqual(stats, { protectedRequests: 3, refreshes: 1 });
  });
});

test("successful recovery on one manually retried route spends the overlapping other route's recovery budget", async () => {
  await withAuthority({ respond: ({ call }) => call === 4
    ? new Response("Recovered first card")
    : new Response("Denied", { status: 401 }) }, async ({ hass, stats }) => {
    await assert.rejects(createDreameClient().loadCard(hass, PATH_A), { status: 401 });
    const results = await Promise.allSettled([
      createDreameClient().retryAuthenticatedRequest(hass, PATH_A),
      createDreameClient().retryAuthenticatedRequest(hass, PATH_B),
    ]);
    assert.equal(results[0].status, "fulfilled");
    assert.equal(await results[0].value.text(), "Recovered first card");
    assert.equal(results[1].status, "rejected");
    assert.equal(results[1].reason.status, 401);
    assert.deepEqual(stats, { protectedRequests: 5, refreshes: 2 });
  });
});

test("a deadline renewal inside HA followed by activation 401 blocks the credential actually sent", async () => {
  await withAuthority({
    beforeHelper: ({ auth, call }) => { if (call === 1) auth.expired = true; },
    respond: ({ bearer, call }) => {
      if (call === 1) assert.equal(bearer, "Bearer fixture-refreshed-1");
      return new Response("Denied", { status: 401 });
    },
  }, async ({ hass, stats }) => {
    const activation = createDreameClient().activateLicence(hass, PATH_A, "fixture-key");
    const queuedBootstrap = createDreameClient().loadCard(hass, PATH_B);
    const results = await Promise.allSettled([activation, queuedBootstrap]);
    assertAuthFailures(results);
    assert.equal(results[0].reason.canRetryWith(hass), false);
    await assert.rejects(createDreameClient().loadCard(hass, PATH_C), { status: 401 });
    assert.deepEqual(stats, { protectedRequests: 1, refreshes: 1 });
  });
});

test("a deadline renewal inside HA followed by bootstrap 403 suppresses the actual credential and route", async () => {
  await withAuthority({
    beforeHelper: ({ auth, call }) => { if (call === 1) auth.expired = true; },
    respond: ({ bearer }) => {
      assert.equal(bearer, "Bearer fixture-refreshed-1");
      return new Response("Route denied", { status: 403 });
    },
  }, async ({ hass, stats }) => {
    const first = await createDreameClient().loadCard(hass, PATH_A);
    assert.equal(first.status, 403);
    assert.equal(await first.text(), "Route denied");
    const repeated = await createDreameClient().loadCard(hass, PATH_A);
    assert.equal(repeated.status, 403);
    assert.equal(await repeated.text(), "Route denied");
    assert.deepEqual(stats, { protectedRequests: 1, refreshes: 1 });
  });
});

test("late activation rejection after HA's internal renewal does not poison a subsequently external token", async () => {
  const firstStarted = deferred();
  const firstResponse = deferred();
  await withAuthority({
    beforeHelper: ({ auth, call }) => { if (call === 1) auth.expired = true; },
    respond: ({ bearer, call }) => {
      if (call === 1) {
        assert.equal(bearer, "Bearer fixture-refreshed-1");
        firstStarted.resolve();
        return firstResponse.promise;
      }
      assert.equal(bearer, "Bearer fixture-external-newer");
      return new Response("New credential accepted");
    },
  }, async ({ auth, hass, stats }) => {
    const activation = createDreameClient().activateLicence(hass, PATH_A, "fixture-key");
    await firstStarted.promise;
    auth.accessToken = "fixture-external-newer";
    firstResponse.resolve(new Response("Denied", { status: 401 }));
    await assert.rejects(activation, error => error.status === 401 && error.canRetryWith(hass));
    assert.equal(await (await createDreameClient().loadCard(hass, PATH_A)).text(), "New credential accepted");
    assert.deepEqual(stats, { protectedRequests: 2, refreshes: 1 });
  });
});

test("late route denial after HA's internal renewal does not cache a subsequently external token", async () => {
  const firstStarted = deferred();
  const firstResponse = deferred();
  await withAuthority({
    beforeHelper: ({ auth, call }) => { if (call === 1) auth.expired = true; },
    respond: ({ bearer, call }) => {
      if (call === 1) {
        assert.equal(bearer, "Bearer fixture-refreshed-1");
        firstStarted.resolve();
        return firstResponse.promise;
      }
      assert.equal(bearer, "Bearer fixture-external-newer");
      return new Response("Route accepted");
    },
  }, async ({ auth, hass, stats }) => {
    const first = createDreameClient().loadCard(hass, PATH_A);
    await firstStarted.promise;
    auth.accessToken = "fixture-external-newer";
    firstResponse.resolve(new Response("Route denied", { status: 403 }));
    assert.equal((await first).status, 403);
    assert.equal(await (await createDreameClient().loadCard(hass, PATH_A)).text(), "Route accepted");
    assert.deepEqual(stats, { protectedRequests: 2, refreshes: 1 });
  });
});

for (const retainToken of [false, true]) {
  test(`a rejected bootstrap token just renewed inside HA (${retainToken ? "same" : "distinct"} token) blocks queued and later cards without another refresh`, async () => {
    const firstStarted = deferred();
    const firstResponse = deferred();
    const dispatched = [];
    const bearer = retainToken ? "Bearer fixture-token-0" : "Bearer fixture-refreshed-1";
    await withAuthority({
      refreshedToken: retainToken ? ({ previousToken }) => previousToken : undefined,
      beforeHelper: ({ auth, call }) => { if (call === 1) auth.expired = true; },
      respond: ({ url, bearer }) => {
        dispatched.push({ path: url.pathname, bearer });
        if (dispatched.length === 1) {
          firstStarted.resolve();
          return firstResponse.promise;
        }
        return new Response("Renewed credential denied", { status: 401 });
      },
    }, async ({ hass, stats }) => {
      const results = Promise.allSettled([
        createDreameClient().loadCard(hass, PATH_A),
        createDreameClient().loadCard(hass, PATH_B),
      ]);
      try {
        await settlesWithin(firstStarted.promise, "The internally renewed bootstrap did not dispatch");
        assert.deepEqual(dispatched, [{ path: `/api/${PATH_A}`, bearer }]);
        firstResponse.resolve(new Response("Renewed credential denied", { status: 401 }));
        const failures = await settlesWithin(results, "Queued cards did not settle after the renewed token was rejected");
        assertAuthFailures(failures);
        assert(failures.every(result => result.reason.canRetryWith(hass) === false));
        await settlesWithin(
          assert.rejects(createDreameClient().loadCard(hass, PATH_C), { status: 401 }),
          "A later card did not receive the session failure",
        );
        assert.deepEqual(dispatched, [{ path: `/api/${PATH_A}`, bearer }]);
        assert.deepEqual(stats, { protectedRequests: 1, refreshes: 1 });
      } finally {
        firstResponse.resolve(new Response("Renewed credential denied", { status: 401 }));
        await settlesWithin(results, "Bootstrap requests did not settle after releasing their response");
      }
    });
  });
}

test("a transport copying headers conservatively latches a rejected same-token internal renewal", async () => {
  await withAuthority({
    refreshedToken: ({ previousToken }) => previousToken,
    beforeHelper: ({ auth, call }) => { if (call === 1) auth.expired = true; },
    respond: ({ bearer }) => {
      assert.equal(bearer, "Bearer fixture-token-0");
      return new Response("Renewed credential denied", { status: 401 });
    },
  }, async ({ hass, stats }) => {
    const originalCallApiRaw = hass.callApiRaw;
    // Deliberate alternate transport: HA writes to a copied headers object,
    // so the coordinator must use its conservative attribution fallback.
    hass.callApiRaw = (method, path, parameters, headers) =>
      originalCallApiRaw(method, path, parameters, { ...headers });
    const failures = await Promise.allSettled([
      createDreameClient().loadCard(hass, PATH_A),
      createDreameClient().loadCard(hass, PATH_B),
    ]);
    assertAuthFailures(failures);
    assert(failures.every(result => result.reason.canRetryWith(hass) === false));
    await assert.rejects(createDreameClient().loadCard(hass, PATH_C), { status: 401 });
    assert.deepEqual(stats, { protectedRequests: 1, refreshes: 1 });
  });
});

test("successful internal expiry renewal with an unchanged token restores one later recovery opportunity", async () => {
  const dispatched = [];
  await withAuthority({
    refreshedToken: ({ refresh, previousToken }) => refresh === 2 ? previousToken : `fixture-refreshed-${refresh}`,
    beforeHelper: ({ auth, path }) => { if (path === PATH_B) auth.expired = true; },
    respond: ({ url, bearer }) => {
      dispatched.push({ path: url.pathname, bearer });
      if (url.pathname === `/api/${PATH_A}`) {
        return bearer === "Bearer fixture-token-0"
          ? new Response("Initial credential denied", { status: 401 })
          : new Response("First route recovered");
      }
      if (url.pathname === `/api/${PATH_B}`) {
        assert.equal(bearer, "Bearer fixture-refreshed-1");
        return new Response("Same-token expiry renewal accepted");
      }
      assert.equal(url.pathname, `/api/${PATH_C}`);
      return bearer === "Bearer fixture-refreshed-3"
        ? new Response("Later recovery accepted")
        : new Response("Later credential rejection", { status: 401 });
    },
  }, async ({ hass, stats }) => {
    assert.equal(await (await createDreameClient().loadCard(hass, PATH_A)).text(), "First route recovered");
    assert.equal(await (await createDreameClient().loadCard(hass, PATH_B)).text(), "Same-token expiry renewal accepted");
    assert.equal(await (await createDreameClient().loadCard(hass, PATH_C)).text(), "Later recovery accepted");
    assert.deepEqual(dispatched, [
      { path: `/api/${PATH_A}`, bearer: "Bearer fixture-token-0" },
      { path: `/api/${PATH_A}`, bearer: "Bearer fixture-refreshed-1" },
      { path: `/api/${PATH_B}`, bearer: "Bearer fixture-refreshed-1" },
      { path: `/api/${PATH_C}`, bearer: "Bearer fixture-refreshed-1" },
      { path: `/api/${PATH_C}`, bearer: "Bearer fixture-refreshed-3" },
    ]);
    assert.deepEqual(stats, { protectedRequests: 5, refreshes: 3 });
  });
});

test("same-token Auth data replacement after dispatch does not mark the pending request freshly renewed", async () => {
  const firstStarted = deferred();
  const firstResponse = deferred();
  const dispatched = [];
  await withAuthority({
    refreshedToken: ({ refresh, previousToken }) => refresh === 1 ? previousToken : `fixture-refreshed-${refresh}`,
    respond: ({ url, bearer }) => {
      assert.equal(url.pathname, `/api/${PATH_A}`);
      dispatched.push(bearer);
      if (bearer === "Bearer fixture-token-0") {
        firstStarted.resolve();
        return firstResponse.promise;
      }
      assert.equal(bearer, "Bearer fixture-refreshed-2");
      return new Response("Bounded recovery accepted");
    },
  }, async ({ auth, hass, stats }) => {
    const pending = createDreameClient().loadCard(hass, PATH_A);
    const settled = Promise.allSettled([pending]);
    try {
      await settlesWithin(firstStarted.promise, "The old bootstrap request did not dispatch");
      const dispatchedData = auth.data;
      await auth.refreshAccessToken(); // HA renews separately while the old request is pending.
      assert.notEqual(auth.data, dispatchedData);
      assert.equal(auth.accessToken, "fixture-token-0");
      firstResponse.resolve(new Response("Old request denied", { status: 401 }));
      const response = await settlesWithin(pending, "The old request did not finish its bounded recovery");
      assert.equal(await response.text(), "Bounded recovery accepted");
      assert.deepEqual(dispatched, ["Bearer fixture-token-0", "Bearer fixture-refreshed-2"]);
      assert.deepEqual(stats, { protectedRequests: 2, refreshes: 2 });
    } finally {
      firstResponse.resolve(new Response("Old request denied", { status: 401 }));
      await settlesWithin(settled, "The old request did not settle after releasing its response");
    }
  });
});

test("a manual retry joining after one route completes shares the episode still pending on another route", async () => {
  const secondStarted = deferred();
  const secondResponse = deferred();
  const dispatched = [];
  let recoveredTokenAccepted = false;
  await withAuthority({ respond: ({ url, bearer }) => {
    dispatched.push({ path: url.pathname, bearer });
    if (url.pathname === `/api/${PATH_A}`) {
      return recoveredTokenAccepted && bearer === "Bearer fixture-refreshed-2"
        ? new Response("Recovered first card")
        : new Response("Credential denied", { status: 401 });
    }
    assert.equal(url.pathname, `/api/${PATH_B}`);
    assert.equal(bearer, "Bearer fixture-refreshed-2");
    secondStarted.resolve();
    return secondResponse.promise;
  } }, async ({ hass, stats }) => {
    await assert.rejects(createDreameClient().loadCard(hass, PATH_A), { status: 401 });
    recoveredTokenAccepted = true;
    const manualA = createDreameClient().retryAuthenticatedRequest(hass, PATH_A);
    const manualB = createDreameClient().retryAuthenticatedRequest(hass, PATH_B);
    const initialResults = Promise.allSettled([manualA, manualB]);
    let staggeredResults = Promise.resolve([]);
    try {
      const firstResponse = await settlesWithin(manualA, "The first manually retried route did not finish");
      assert.equal(await firstResponse.text(), "Recovered first card");
      await settlesWithin(secondStarted.promise, "The second manually retried route did not dispatch");
      staggeredResults = Promise.allSettled([
        createDreameClient().retryAuthenticatedRequest(hass, PATH_A),
      ]);
      // The recovered credential has now been rejected while B's response is
      // pending. A joining caller must not reset the still-active episode.
      recoveredTokenAccepted = false;
      secondResponse.resolve(new Response("Recovered credential denied", { status: 401 }));
      const [firstResults, laterResults] = await settlesWithin(
        Promise.all([initialResults, staggeredResults]),
        "The overlapping manual episode did not settle",
      );
      assert.equal(firstResults[0].status, "fulfilled");
      assertAuthFailures([firstResults[1], ...laterResults]);
      await settlesWithin(
        assert.rejects(createDreameClient().loadCard(hass, PATH_C), { status: 401 }),
        "A later card did not receive the shared manual-recovery failure",
      );
      assert.deepEqual(dispatched, [
        { path: `/api/${PATH_A}`, bearer: "Bearer fixture-token-0" },
        { path: `/api/${PATH_A}`, bearer: "Bearer fixture-refreshed-1" },
        { path: `/api/${PATH_A}`, bearer: "Bearer fixture-refreshed-1" },
        { path: `/api/${PATH_A}`, bearer: "Bearer fixture-refreshed-2" },
        { path: `/api/${PATH_B}`, bearer: "Bearer fixture-refreshed-2" },
      ]);
      assert.deepEqual(stats, { protectedRequests: 5, refreshes: 2 });
    } finally {
      secondResponse.resolve(new Response("Recovered credential denied", { status: 401 }));
      await settlesWithin(
        Promise.all([initialResults, staggeredResults]),
        "Manual requests did not settle after releasing the second route",
      );
    }
  });
});

test("a separate Auth session completes while another session's same-route request is still pending", async () => {
  const firstStarted = deferred();
  const firstResponse = deferred();
  const dispatched = [];
  await withAuthority({ respond: ({ url, bearer }) => {
    assert.equal(url.pathname, `/api/${PATH_A}`);
    dispatched.push(bearer);
    if (bearer === "Bearer fixture-token-0") {
      firstStarted.resolve();
      return firstResponse.promise;
    }
    assert.equal(bearer, "Bearer fixture-independent-session");
    return new Response("Independent session completed");
  } }, async ({ hass, stats }) => {
    const otherAuth = {
      accessToken: "fixture-independent-session", expired: false,
      refreshAccessToken() { assert.fail("The independent valid session must not refresh"); },
    };
    const otherHass = {
      auth: otherAuth, connected: true,
      callApiRaw(method, path, _parameters, headers) {
        assert.equal(method, "GET");
        return fetchWithAuth(otherAuth, `https://fixture.invalid/api/${path}`, { method, headers });
      },
    };
    const firstResults = Promise.allSettled([createDreameClient().loadCard(hass, PATH_A)]);
    let secondResults = Promise.resolve([]);
    try {
      await settlesWithin(firstStarted.promise, "The first session did not dispatch");
      const independent = createDreameClient().loadCard(otherHass, PATH_A);
      secondResults = Promise.allSettled([independent]);
      const response = await settlesWithin(independent, "The independent Auth session waited for the held session");
      assert.equal(await response.text(), "Independent session completed");
      assert.deepEqual(dispatched, ["Bearer fixture-token-0", "Bearer fixture-independent-session"]);
      assert.deepEqual(stats, { protectedRequests: 2, refreshes: 0 });
    } finally {
      firstResponse.resolve(new Response("First session released"));
      await settlesWithin(
        Promise.all([firstResults, secondResults]),
        "Session requests did not settle after releasing the first session",
      );
    }
  });
});
