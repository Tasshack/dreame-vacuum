/**
 * Maintainer integration candidate; not a patched proprietary Dreame bundle.
 * All clients imported from this module coordinate on the same HA Auth object.
 * This state is page/module-local, not shared across tabs, devices or unrelated
 * HA request consumers. Never logs tokens, licence keys, URLs or response bodies.
 */
export class DreameAuthenticationError extends Error {
  constructor(message, { status, cause, canRetryWith } = {}) {
    super(message, { cause });
    this.name = "DreameAuthenticationError";
    this.status = status;
    this.canRetryWith = canRetryWith ?? (hass => Boolean(hass?.connected && hass.auth?.accessToken));
  }
}

const BOOTSTRAP_PATH = /^dreame_vacuum\/[a-f0-9]{32}\/[a-f0-9]{32}$/;
// Deliberately outside the factory: another card/client cannot reset the budget.
const sessions = new WeakMap();

function getSession(auth) {
  let state = sessions.get(auth);
  if (!state) {
    state = {
      pending: new Map(), forbidden: new Map(), tail: Promise.resolve(),
      observedToken: auth.accessToken, generation: 0,
      recoveryUsed: false, blocked: null,
      manualEpisode: null,
    };
    sessions.set(auth, state);
  }
  return state;
}

function openGeneration(state, token) {
  state.observedToken = token;
  state.generation++;
  state.recoveryUsed = false;
  state.blocked = null;
}

function observeExternalToken(state, auth) {
  if (auth.accessToken !== state.observedToken) openGeneration(state, auth.accessToken);
}

function blockSession(state, auth, token, message, details = {}) {
  const generation = state.generation;
  const error = new DreameAuthenticationError(message, {
    ...details,
    // Keep bearer values inside a closure rather than exposing them on errors.
    canRetryWith: current => Boolean(current?.connected && current.auth?.accessToken && (
      current.auth !== auth || current.auth.accessToken !== token || state.generation !== generation
    )),
  });
  state.blocked = { token, error };
  return error;
}

async function refresh(state, auth, { normalRenewal = false } = {}) {
  const previousToken = auth.accessToken;
  try {
    await auth.refreshAccessToken();
  } catch (cause) {
    throw blockSession(state, auth, previousToken, "Home Assistant session could not be refreshed", { cause });
  }
  // A normal expiry renewal starts a new generation. A forced 401 recovery is
  // our own replacement within the existing generation and keeps its spent budget.
  if (normalRenewal) openGeneration(state, auth.accessToken);
  else state.observedToken = auth.accessToken;
}

function discard(response) {
  // Cancellation of a tee branch can depend on another consumer. Start cleanup
  // without holding the auth queue open or replacing the original auth error.
  try { response.body?.cancel().catch(() => {}); } catch {}
}

async function snapshotDenial(response) {
  try {
    return {
      body: await response.arrayBuffer(), status: response.status,
      statusText: response.statusText, headers: [...response.headers],
    };
  } catch (error) {
    discard(response);
    throw error;
  }
}

function restoreDenial(snapshot) {
  // Cache bytes rather than a live stream branch. Each caller owns its body.
  return new Response(snapshot.body.slice(0), {
    status: snapshot.status, statusText: snapshot.statusText, headers: snapshot.headers,
  });
}

async function send(state, hass, path) {
  const auth = hass.auth;
  const initialToken = auth.accessToken;
  const initialData = auth.data;
  let token = initialToken;
  let authorization;
  let captured = false;
  let renewed = false;
  // HA's authenticated helper assigns this per-request header after any inner
  // refresh and immediately before fetch. Observe that assignment without
  // replacing fetch or mutating the shared Auth object. No bearer is exposed.
  const headers = {};
  Object.defineProperty(headers, "authorization", {
    enumerable: true,
    get: () => authorization,
    set(value) {
      authorization = value;
      if (typeof value === "string" && value.startsWith("Bearer ")) {
        captured = true;
        token = value.slice(7);
        // HA replaces Auth.data after refresh, including when the returned
        // bearer is unchanged. Capture this at dispatch, not after the response:
        // a later external renewal must not be mistaken for this request's own.
        renewed = token !== initialToken || (initialData !== undefined && auth.data !== initialData);
        if (token !== state.observedToken || renewed) openGeneration(state, token);
      }
    },
  });
  try {
    const response = await hass.callApiRaw("GET", path, undefined, headers);
    if (!captured && (auth.accessToken !== initialToken || (initialData !== undefined && auth.data !== initialData))) {
      // A transport that stops preserving the supplied header object cannot
      // attribute this rejection precisely. Conservatively bind it to current
      // credentials and require a later token change or deliberate recovery.
      token = auth.accessToken;
      renewed = true;
      openGeneration(state, token);
    }
    return { response, token, renewed };
  } catch (cause) {
    // HA can cross its expiry deadline after our preflight, then fail refreshing
    // inside callApiRaw. If that same token is still expired, stop repeated calls.
    // This condition does not prove whether the failure was auth or networking.
    if (auth.accessToken === token && auth.expired) {
      throw blockSession(state, auth, token, "Home Assistant authenticated request could not complete", { cause });
    }
    throw cause;
  }
}

export function createDreameClient() {
  function subscribe(job) {
    return new Promise((resolve, reject) => job.consumers.push({ resolve, reject }));
  }

  function request(hass, apiPath, { activate = false, key, explicitRetry = false } = {}) {
    if (!hass?.auth || !hass.auth.accessToken || !hass.connected) {
      return Promise.reject(new DreameAuthenticationError("Home Assistant authentication is not ready"));
    }
    if (typeof hass.callApiRaw !== "function") {
      return Promise.reject(new Error("Home Assistant callApiRaw is required"));
    }
    if (!BOOTSTRAP_PATH.test(apiPath)) {
      return Promise.reject(new Error("Invalid Dreame bootstrap API path"));
    }
    if (activate && typeof key !== "string") {
      return Promise.reject(new Error("A licence key is required"));
    }
    // Keep existing key normalization in the caller. callApiRaw adds /api/.
    const path = activate ? `${apiPath}?k=${encodeURIComponent(btoa(key))}` : apiPath;
    const auth = hass.auth;
    const state = getSession(auth);
    let episode;
    if (explicitRetry) {
      episode = state.manualEpisode ??= { reset: false, pending: 0, routes: new Map() };
      if (episode.routes.has(apiPath)) return subscribe(episode.routes.get(apiPath));
    } else if (!activate && state.pending.has(apiPath)) {
      return subscribe(state.pending.get(apiPath));
    }

    const job = { consumers: [] };
    const result = subscribe(job);
    if (!activate) state.pending.set(apiPath, job);
    if (episode) {
      episode.pending++;
      episode.routes.set(apiPath, job);
    }

    function finish() {
      // Remove the job before resolving callers; a caller can immediately make
      // another request after consuming its result.
      if (!activate && state.pending.get(apiPath) === job) state.pending.delete(apiPath);
      if (episode) {
        episode.routes.delete(apiPath);
        if (--episode.pending === 0 && state.manualEpisode === episode) state.manualEpisode = null;
      }
    }

    const requestTask = state.tail.then(async () => {
      observeExternalToken(state, auth);
      // Reset inside the queue, after older requests finish. Only a user action
      // may invoke this; constructing a new card/client cannot reopen a session.
      if (episode) {
        if (!episode.reset) {
          episode.reset = true;
          openGeneration(state, auth.accessToken);
        }
        state.forbidden.delete(apiPath);
      }
      if (state.blocked?.token === auth.accessToken) throw state.blocked.error;
      const forbidden = state.forbidden.get(apiPath);
      if (!activate && forbidden?.token === auth.accessToken) return restoreDenial(forbidden.snapshot);
      if (forbidden?.token !== auth.accessToken) state.forbidden.delete(apiPath);

      let freshPreflight = false;
      if (auth.expired) {
        await refresh(state, auth, { normalRenewal: true });
        freshPreflight = true;
      }
      let { response, token: requestToken, renewed } = await send(state, hass, path);
      if (response.status === 401 && !activate) {
        const newerToken = auth.accessToken !== requestToken;
        if (newerToken) observeExternalToken(state, auth);
        if ((!(freshPreflight || renewed) || newerToken) && !state.recoveryUsed) {
          // Spend the session generation's budget before awaiting any work,
          // including when a refresh returns the same access-token string.
          state.recoveryUsed = true;
          discard(response);
          if (!newerToken) await refresh(state, auth);
          ({ response, token: requestToken } = await send(state, hass, path));
        }
      }
      if (response.status === 401) {
        // Activation is never automatically replayed. A failed bootstrap retry
        // or freshly acquired token closes this generation for every card.
        discard(response);
        throw blockSession(state, auth, requestToken, "Home Assistant rejected the Dreame request with HTTP 401", { status: 401 });
      }
      if (!activate && response.status === 403) {
        // Preserve route-specific denial; it does not prove an invalid session.
        const snapshot = await snapshotDenial(response);
        state.forbidden.set(apiPath, { token: requestToken, snapshot });
        return restoreDenial(snapshot);
      }
      if (activate && response.ok) state.forbidden.delete(apiPath);
      return response;
    });
    const complete = requestTask.then(response => {
      finish();
      const consumers = job.consumers.splice(0);
      const responses = [];
      try {
        // Only actual consumers receive branches; the last owns the original.
        // Activation has one consumer and therefore never needs a clone.
        for (let i = 1; i < consumers.length; i++) responses.push(response.clone());
        responses.push(response);
      } catch (error) {
        responses.forEach(discard);
        discard(response);
        consumers.forEach(consumer => consumer.reject(error));
        return;
      }
      consumers.forEach((consumer, i) => consumer.resolve(responses[i]));
    }, error => {
      finish();
      job.consumers.splice(0).forEach(consumer => consumer.reject(error));
    });
    state.tail = complete.then(() => undefined, () => undefined);
    return result;
  }

  return {
    loadCard: (hass, apiPath) => request(hass, apiPath),
    retryAuthenticatedRequest: (hass, apiPath) => request(hass, apiPath, { explicitRetry: true }),
    // Explicit submission only: no application cache, deduplication or replay.
    activateLicence: (hass, apiPath, key) => request(hass, apiPath, { activate: true, key }),
  };
}

export const createGuardedGetClient = () => createDreameClient().loadCard;
