import test from "node:test";
import assert from "node:assert/strict";
import { createDreameClient, DreameAuthenticationError } from "./guarded-get.mjs";

// Offline response-ownership tests: no fetch stub, sockets, credentials or devices.
const API_PATH = `dreame_vacuum/${"a".repeat(32)}/${"b".repeat(32)}`;
const OTHER_PATH = `${API_PATH.slice(0, -1)}c`;
const encoder = new TextEncoder();

function deferred() {
  let resolve;
  const promise = new Promise(resolver => { resolve = resolver; });
  return { promise, resolve };
}

function openResponse(t, { status = 200, onCancel = () => {} } = {}) {
  let controller;
  const stats = { cancellations: 0 };
  const response = new Response(new ReadableStream({
    start(value) { controller = value; },
    cancel(reason) {
      stats.cancellations++;
      return onCancel(reason);
    },
  }), { status, statusText: `Fixture ${status}`, headers: { "x-fixture": "preserved" } });
  // Cleanup is intentionally not awaited: an abandoned tee branch may otherwise
  // hang cleanup in the very implementation these regressions are detecting.
  t.after(() => { void response.body.cancel().catch(() => {}); });
  return { response, controller, stats };
}

function makeHass(callApiRaw, { expired = false, refreshAccessToken } = {}) {
  const auth = {
    accessToken: "synthetic-valid-token", expired,
    async refreshAccessToken() {
      this.accessToken = "synthetic-refreshed-token";
      this.expired = false;
    },
  };
  if (refreshAccessToken) auth.refreshAccessToken = refreshAccessToken;
  return { auth, connected: true, callApiRaw };
}

async function settlesWithin(promise, message) {
  let timer;
  try {
    return await Promise.race([
      promise,
      new Promise((_, reject) => {
        timer = setTimeout(() => reject(new Error(message)), 5_000);
      }),
    ]);
  } finally {
    clearTimeout(timer);
  }
}

test("one bootstrap consumer can cancel its native response stream", async t => {
  const source = openResponse(t);
  source.controller.enqueue(encoder.encode("part of a streamed bootstrap"));
  const hass = makeHass(async () => source.response);
  const response = await createDreameClient().loadCard(hass, API_PATH);
  assert(response instanceof Response);
  await settlesWithin(response.body.cancel(), "Single-consumer cancellation did not settle");
  assert.equal(source.stats.cancellations, 1);
});

test("overlapping bootstrap consumers own every response branch and cancel the source", async t => {
  const source = openResponse(t);
  const headers = deferred();
  let requests = 0;
  const hass = makeHass(() => { requests++; return headers.promise; });
  const clients = [createDreameClient(), createDreameClient(), createDreameClient()];
  const pending = clients.map(client => client.loadCard(hass, API_PATH));
  headers.resolve(source.response);
  const responses = await Promise.all(pending);
  assert.equal(requests, 1);
  assert.equal(new Set(responses).size, 3);
  assert(responses.every(response => response instanceof Response));
  await settlesWithin(
    Promise.all(responses.map(response => response.body.cancel())),
    "Cancelling every consumer left an unowned response branch",
  );
  assert.equal(source.stats.cancellations, 1);
});

test("overlapping bootstrap consumers independently read streamed chunks", async t => {
  const source = openResponse(t);
  let requests = 0;
  const hass = makeHass(async () => { requests++; return source.response; });
  const client = createDreameClient();
  const responses = await Promise.all([
    client.loadCard(hass, API_PATH), createDreameClient().loadCard(hass, API_PATH),
  ]);
  assert.equal(new Set(responses).size, 2);
  const bodies = responses.map(response => response.text());
  source.controller.enqueue(encoder.encode("first chunk; "));
  source.controller.enqueue(encoder.encode("second chunk"));
  source.controller.close();
  assert.deepEqual(await Promise.all(bodies), [
    "first chunk; second chunk", "first chunk; second chunk",
  ]);
  assert.equal(requests, 1);
  assert.equal(source.stats.cancellations, 0);
});

test("partial response fanout failure rejects every consumer, cancels allocated branches and releases the queue", async t => {
  const cancelled = deferred();
  const source = openResponse(t, { onCancel: () => cancelled.resolve() });
  const cloneFailure = new Error("Synthetic second-clone failure");
  const nativeClone = source.response.clone.bind(source.response);
  const branches = [];
  let cloneCalls = 0;
  // Fault injection is restricted to cloning; source and allocated branches use
  // native Response/ReadableStream ownership and cancellation throughout.
  source.response.clone = () => {
    if (++cloneCalls === 2) throw cloneFailure;
    const branch = nativeClone();
    branches.push(branch);
    return branch;
  };
  t.after(() => { branches.forEach(branch => { void branch.body.cancel().catch(() => {}); }); });
  const requestedPaths = [];
  const hass = makeHass(async (method, path) => {
    requestedPaths.push(path);
    return requestedPaths.length === 1 ? source.response : new Response("queue progressed");
  });
  const consumers = Array.from({ length: 3 }, () => createDreameClient().loadCard(hass, API_PATH));
  const queued = createDreameClient().loadCard(hass, OTHER_PATH);
  const results = await settlesWithin(Promise.allSettled(consumers), "Fanout failure left a consumer pending");
  assert(results.every(result => result.status === "rejected" && result.reason === cloneFailure));
  assert.equal(cloneCalls, 2);
  assert.equal(branches.length, 1);
  await settlesWithin(cancelled.promise, "Fanout failure left an allocated response branch uncancelled");
  assert.equal(source.stats.cancellations, 1);
  assert.equal(await (await settlesWithin(queued, "Fanout failure blocked the queued route")).text(), "queue progressed");
  assert.equal(await (await createDreameClient().loadCard(hass, API_PATH)).text(), "queue progressed");
  assert.deepEqual(requestedPaths, [API_PATH, OTHER_PATH, API_PATH]);
});

test("licence activation returns the original native response without an unused clone", async t => {
  const source = openResponse(t, { status: 202 });
  let requests = 0;
  let refreshes = 0;
  const hass = makeHass(async (method, path) => {
    requests++;
    assert.equal(method, "GET");
    assert.equal(path, `${API_PATH}?k=${encodeURIComponent(btoa("synthetic-key"))}`);
    return source.response;
  }, {
    async refreshAccessToken() { refreshes++; },
  });
  const response = await createDreameClient().activateLicence(hass, API_PATH, "synthetic-key");
  assert.strictEqual(response, source.response);
  assert.equal(response.status, 202);
  assert.equal(response.headers.get("x-fixture"), "preserved");
  await settlesWithin(response.body.cancel(), "Activation cancellation did not settle");
  assert.equal(source.stats.cancellations, 1);
  assert.equal(requests, 1);
  assert.equal(refreshes, 0);
});

test("unexpected 401 body is cancelled before refresh and bootstrap retry", async t => {
  const events = [];
  const denied = openResponse(t, { status: 401, onCancel: () => events.push("cancel 401") });
  let requests = 0;
  const hass = makeHass(async () => {
    events.push(`request ${++requests}`);
    return requests === 1 ? denied.response : new Response("recovered payload");
  }, {
    async refreshAccessToken() {
      events.push("refresh");
      assert.equal(denied.stats.cancellations, 1);
      this.accessToken = "synthetic-new-token";
    },
  });
  const response = await createDreameClient().loadCard(hass, API_PATH);
  assert.equal(await response.text(), "recovered payload");
  assert.deepEqual(events, ["request 1", "cancel 401", "refresh", "request 2"]);
});

test("pending 401 cancellation does not block recovery or the next queued route", async t => {
  const releaseCancellation = deferred();
  const denied = openResponse(t, { status: 401, onCancel: () => releaseCancellation.promise });
  let requests = 0;
  let refreshes = 0;
  const hass = makeHass(async () => ++requests === 1 ? denied.response : new Response("recovered payload"), {
    async refreshAccessToken() {
      refreshes++;
      this.accessToken = "synthetic-new-token";
    },
  });
  const pending = [
    createDreameClient().loadCard(hass, API_PATH),
    createDreameClient().loadCard(hass, OTHER_PATH),
  ];
  try {
    // The cancellation promise is deliberately unresolved until finally. This
    // checks progress independently of the time the underlying cleanup takes.
    const responses = await settlesWithin(Promise.all(pending), "Pending body cancellation blocked authentication recovery");
    assert.deepEqual(await Promise.all(responses.map(response => response.text())), ["recovered payload", "recovered payload"]);
    assert.equal(denied.stats.cancellations, 1);
    assert.equal(refreshes, 1);
    assert.equal(requests, 3);
  } finally {
    releaseCancellation.resolve();
    await settlesWithin(Promise.allSettled(pending), "Requests remained pending after cancellation was released");
  }
});

test("both rejected bootstrap response bodies are cancelled before terminal rejection", async t => {
  const denied = [openResponse(t, { status: 401 }), openResponse(t, { status: 401 })];
  let requests = 0;
  const hass = makeHass(async () => denied[requests++].response);
  await assert.rejects(createDreameClient().loadCard(hass, API_PATH), error => {
    assert(error instanceof DreameAuthenticationError);
    assert.equal(error.status, 401);
    assert.deepEqual(denied.map(source => source.stats.cancellations), [1, 1]);
    return true;
  });
  assert.equal(requests, 2);
});

test("rejected 401 cleanup preserves the authentication error and bounded recovery", async t => {
  const cleanupFailure = new Error("Synthetic cancellation failure");
  const denied = Array.from({ length: 2 }, () => openResponse(t, {
    status: 401, onCancel: () => Promise.reject(cleanupFailure),
  }));
  let requests = 0;
  let refreshes = 0;
  const hass = makeHass(async () => denied[requests++].response, {
    async refreshAccessToken() {
      refreshes++;
      this.accessToken = "synthetic-new-token";
    },
  });
  await assert.rejects(createDreameClient().loadCard(hass, API_PATH), error => {
    assert(error instanceof DreameAuthenticationError);
    assert.equal(error.status, 401);
    assert.notStrictEqual(error.cause, cleanupFailure);
    return true;
  });
  assert.deepEqual(denied.map(source => source.stats.cancellations), [1, 1]);
  assert.equal(requests, 2);
  assert.equal(refreshes, 1);
});

test("401 after normal expiry renewal is cancelled without a second protected request", async t => {
  const denied = openResponse(t, { status: 401 });
  let requests = 0;
  const hass = makeHass(async () => { requests++; return denied.response; }, { expired: true });
  await assert.rejects(createDreameClient().loadCard(hass, API_PATH), { status: 401 });
  assert.equal(denied.stats.cancellations, 1);
  assert.equal(requests, 1);
});

test("activation 401 is cancelled before rejection and is never replayed", async t => {
  const denied = openResponse(t, { status: 401 });
  let requests = 0;
  let refreshes = 0;
  const hass = makeHass(async () => { requests++; return denied.response; }, {
    async refreshAccessToken() { refreshes++; },
  });
  await assert.rejects(
    createDreameClient().activateLicence(hass, API_PATH, "synthetic-key"),
    { status: 401 },
  );
  assert.equal(denied.stats.cancellations, 1);
  assert.equal(requests, 1);
  assert.equal(refreshes, 0);
});

test("401 body is already cancelled when the attempted refresh fails", async t => {
  const denied = openResponse(t, { status: 401 });
  const failure = new Error("Synthetic refresh failure");
  let requests = 0;
  const hass = makeHass(async () => { requests++; return denied.response; }, {
    async refreshAccessToken() {
      assert.equal(denied.stats.cancellations, 1);
      throw failure;
    },
  });
  await assert.rejects(createDreameClient().loadCard(hass, API_PATH), error => {
    assert(error instanceof DreameAuthenticationError);
    assert.strictEqual(error.cause, failure);
    return true;
  });
  assert.equal(denied.stats.cancellations, 1);
  assert.equal(requests, 1);
});

test("403 cache consumes the source once and returns independent status, headers and bodies", async t => {
  const denied = openResponse(t, { status: 403 });
  const dispatched = deferred();
  let requests = 0;
  const hass = makeHass(async () => {
    requests++;
    dispatched.resolve();
    return denied.response;
  });
  const client = createDreameClient();
  const pending = [client.loadCard(hass, API_PATH), createDreameClient().loadCard(hass, API_PATH)];
  await dispatched.promise;
  denied.controller.enqueue(encoder.encode("device-specific "));
  denied.controller.enqueue(encoder.encode("denial"));
  denied.controller.close();
  const responses = await Promise.all(pending);
  assert.equal(denied.response.bodyUsed, true, "Cache must not retain an unread live source");
  responses.push(await client.loadCard(hass, API_PATH));
  assert.equal(new Set(responses).size, 3);
  assert(responses.every(response => response instanceof Response));
  assert(responses.every(response => response.status === 403 && response.statusText === "Fixture 403"));
  assert(responses.every(response => response.headers.get("x-fixture") === "preserved"));
  assert.deepEqual(await Promise.all(responses.map(response => response.text())), [
    "device-specific denial", "device-specific denial", "device-specific denial",
  ]);
  assert.equal(requests, 1);
});

for (const recovery of ["explicit retry", "token replacement", "successful activation"]) {
  test(`consumed 403 cache is invalidated by ${recovery}`, async t => {
    const denied = openResponse(t, { status: 403 });
    denied.controller.enqueue(encoder.encode("initial denial"));
    denied.controller.close();
    let requests = 0;
    const hass = makeHass(async () => {
      requests++;
      return requests === 1 ? denied.response : new Response("recovered");
    });
    const client = createDreameClient();
    const first = await client.loadCard(hass, API_PATH);
    assert.equal(await first.text(), "initial denial");
    assert.equal(denied.response.bodyUsed, true);
    assert.equal(await (await client.loadCard(hass, API_PATH)).text(), "initial denial");
    assert.equal(requests, 1);
    let recovered;
    if (recovery === "explicit retry") {
      recovered = await client.retryAuthenticatedRequest(hass, API_PATH);
    } else if (recovery === "token replacement") {
      hass.auth.accessToken = "synthetic-replacement-token";
      recovered = await client.loadCard(hass, API_PATH);
    } else {
      const activation = await client.activateLicence(hass, API_PATH, "synthetic-key");
      assert.equal(await activation.text(), "recovered");
      recovered = await client.loadCard(hass, API_PATH);
    }
    assert.equal(recovered.status, 200);
    assert.equal(await recovered.text(), "recovered");
    assert.equal(requests, recovery === "successful activation" ? 3 : 2);
  });
}

for (const status of [403, 500]) {
  test(`activation HTTP ${status} preserves the existing bootstrap denial`, async () => {
    let bootstrapRequests = 0;
    let activationRequests = 0;
    let refreshes = 0;
    const activationPath = `${API_PATH}?k=${encodeURIComponent(btoa("synthetic-key"))}`;
    const hass = makeHass(async (method, path) => {
      assert.equal(method, "GET");
      if (path === activationPath) {
        activationRequests++;
        return new Response("activation failure", { status });
      }
      assert.equal(path, API_PATH);
      return new Response(`bootstrap denial ${++bootstrapRequests}`, { status: 403 });
    }, {
      async refreshAccessToken() { refreshes++; },
    });
    const client = createDreameClient();
    assert.equal(await (await client.loadCard(hass, API_PATH)).text(), "bootstrap denial 1");
    const activation = await client.activateLicence(hass, API_PATH, "synthetic-key");
    assert.equal(activation.status, status);
    assert.equal(await activation.text(), "activation failure");
    const cached = await createDreameClient().loadCard(hass, API_PATH);
    assert.equal(cached.status, 403);
    assert.equal(await cached.text(), "bootstrap denial 1");
    assert.equal(bootstrapRequests, 1);
    assert.equal(activationRequests, 1);
    assert.equal(refreshes, 0);
  });
}

for (const recovery of ["explicit retry", "successful activation"]) {
  test(`${recovery} clears only its own route's cached 403`, async () => {
    const requestedPaths = [];
    let routeRecovered = false;
    const activationPath = `${API_PATH}?k=${encodeURIComponent(btoa("synthetic-key"))}`;
    const hass = makeHass(async (method, path) => {
      assert.equal(method, "GET");
      requestedPaths.push(path);
      if (path === activationPath) return new Response("activated");
      if (path === API_PATH) return routeRecovered
        ? new Response("recovered A") : new Response("denial A", { status: 403 });
      assert.equal(path, OTHER_PATH);
      return new Response("denial B", { status: 403 });
    });
    const client = createDreameClient();
    assert.equal(await (await client.loadCard(hass, API_PATH)).text(), "denial A");
    assert.equal(await (await client.loadCard(hass, OTHER_PATH)).text(), "denial B");
    routeRecovered = true;
    let recovered;
    if (recovery === "explicit retry") {
      recovered = await client.retryAuthenticatedRequest(hass, API_PATH);
    } else {
      assert.equal(await (await client.activateLicence(hass, API_PATH, "synthetic-key")).text(), "activated");
      recovered = await client.loadCard(hass, API_PATH);
    }
    assert.equal(recovered.status, 200);
    assert.equal(await recovered.text(), "recovered A");
    const untouched = await createDreameClient().loadCard(hass, OTHER_PATH);
    assert.equal(untouched.status, 403);
    assert.equal(await untouched.text(), "denial B");
    assert.deepEqual(requestedPaths, recovery === "explicit retry"
      ? [API_PATH, OTHER_PATH, API_PATH]
      : [API_PATH, OTHER_PATH, activationPath, API_PATH]);
  });
}

test("loading a healthy route does not evict another route's cached denial", async () => {
  const requestedPaths = [];
  const hass = makeHass(async (method, path) => {
    assert.equal(method, "GET");
    requestedPaths.push(path);
    if (path === API_PATH) return new Response("cached denial", { status: 403 });
    assert.equal(path, OTHER_PATH);
    return new Response("healthy route");
  });
  const client = createDreameClient();
  assert.equal(await (await client.loadCard(hass, API_PATH)).text(), "cached denial");
  const healthy = await client.loadCard(hass, OTHER_PATH);
  assert.equal(healthy.status, 200);
  assert.equal(await healthy.text(), "healthy route");
  const cached = await createDreameClient().loadCard(hass, API_PATH);
  assert.equal(cached.status, 403);
  assert.equal(await cached.text(), "cached denial");
  assert.deepEqual(requestedPaths, [API_PATH, OTHER_PATH]);
});

test("a failed 403 body read is not installed as a permanent cached response", async t => {
  const denied = openResponse(t, { status: 403 });
  const dispatched = deferred();
  const bodyFailure = new Error("Synthetic interrupted denial body");
  let requests = 0;
  const hass = makeHass(async () => {
    requests++;
    dispatched.resolve();
    return requests === 1 ? denied.response : new Response("fresh response");
  });
  const client = createDreameClient();
  const pending = client.loadCard(hass, API_PATH);
  await dispatched.promise;
  denied.controller.error(bodyFailure);
  await assert.rejects(pending, error => error === bodyFailure);
  assert.equal(await (await client.loadCard(hass, API_PATH)).text(), "fresh response");
  assert.equal(requests, 2);
});
