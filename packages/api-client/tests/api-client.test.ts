import test from 'node:test';
import assert from 'node:assert/strict';
import { OpportunityApiClient } from '../src/index.ts';

function jsonResponse(status, body) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

test('OpportunityApiClient sends Bearer token on normal authenticated request', async () => {
  const originalFetch = globalThis.fetch;
  const seenHeaders = [];
  globalThis.fetch = async (_url, init) => {
    seenHeaders.push(init?.headers);
    return jsonResponse(200, { studentId: 'u1' });
  };
  try {
    const client = new OpportunityApiClient('http://api.local/api/v1', 'tok-1');
    const data = await client.getProfile();
    assert.deepEqual(data, { studentId: 'u1' });
    assert.equal(seenHeaders[0].Authorization, 'Bearer tok-1');
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('OpportunityApiClient refreshes once on 401 and retries with new token', async () => {
  const originalFetch = globalThis.fetch;
  const authHeaders = [];
  let calls = 0;
  let refreshCalls = 0;

  globalThis.fetch = async (_url, init) => {
    calls += 1;
    authHeaders.push(init?.headers?.Authorization);
    if (calls === 1) return jsonResponse(401, { message: 'expired' });
    return jsonResponse(200, [{ id: 'opp-1' }]);
  };

  try {
    const client = new OpportunityApiClient('http://api.local/api/v1', 'old-tok', async () => {
      refreshCalls += 1;
      return 'fresh-tok';
    });
    const res = await client.discoverOpportunities('ml');
    assert.deepEqual(res, [{ id: 'opp-1' }]);
    assert.equal(refreshCalls, 1);
    assert.deepEqual(authHeaders, ['Bearer old-tok', 'Bearer fresh-tok']);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('OpportunityApiClient clears token when refresh fails', async () => {
  const originalFetch = globalThis.fetch;
  const authHeaders = [];
  globalThis.fetch = async (_url, init) => {
    authHeaders.push(init?.headers?.Authorization);
    return jsonResponse(401, { message: 'expired' });
  };

  try {
    const client = new OpportunityApiClient('http://api.local/api/v1', 'old-tok', async () => null);
    await assert.rejects(() => client.getProfile(), /expired|401/);
    // Subsequent request must not carry cleared stale token
    await assert.rejects(() => client.getProfile(), /expired|401/);
    assert.equal(authHeaders[0], 'Bearer old-tok');
    assert.equal(authHeaders[1], undefined);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('OpportunityApiClient retries only once when second request also returns 401', async () => {
  const originalFetch = globalThis.fetch;
  let fetchCalls = 0;
  let refreshCalls = 0;
  globalThis.fetch = async () => {
    fetchCalls += 1;
    return jsonResponse(401, { message: 'still unauthorized' });
  };

  try {
    const client = new OpportunityApiClient('http://api.local/api/v1', 'tok-1', async () => {
      refreshCalls += 1;
      return 'tok-2';
    });
    await assert.rejects(() => client.getProfile(), /still unauthorized/);
    assert.equal(fetchCalls, 2);
    assert.equal(refreshCalls, 1);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('OpportunityApiClient does not refresh on HTTP 403', async () => {
  const originalFetch = globalThis.fetch;
  let refreshCalls = 0;
  globalThis.fetch = async () => jsonResponse(403, { message: 'forbidden' });

  try {
    const client = new OpportunityApiClient('http://api.local/api/v1', 'tok-1', async () => {
      refreshCalls += 1;
      return 'tok-2';
    });
    await assert.rejects(() => client.getProfile(), /forbidden/);
    assert.equal(refreshCalls, 0);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('OpportunityApiClient deduplicates concurrent 401 refresh calls', async () => {
  const originalFetch = globalThis.fetch;
  let refreshCalls = 0;
  globalThis.fetch = async (_url, init) => {
    const auth = init?.headers?.Authorization;
    if (auth === 'Bearer expired-tok') {
      return jsonResponse(401, { message: 'expired' });
    }
    return jsonResponse(200, { ok: auth });
  };

  try {
    const client = new OpportunityApiClient(
      'http://api.local/api/v1',
      'expired-tok',
      async () => {
        refreshCalls += 1;
        await new Promise((r) => setTimeout(r, 20));
        return 'new-tok';
      }
    );
    const [r1, r2, r3] = await Promise.all([
      client.getProfile(),
      client.discoverOpportunities('python'),
      client.checkEligibility('opp-1'),
    ]);
    assert.equal(refreshCalls, 1);
    assert.deepEqual(r1, { ok: 'Bearer new-tok' });
    assert.deepEqual(r2, { ok: 'Bearer new-tok' });
    assert.deepEqual(r3, { ok: 'Bearer new-tok' });
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('OpportunityApiClient clears Authorization header on logout setToken("")', async () => {
  const originalFetch = globalThis.fetch;
  const seenHeaders = [];
  globalThis.fetch = async (_url, init) => {
    seenHeaders.push(init?.headers);
    return jsonResponse(200, []);
  };

  try {
    const client = new OpportunityApiClient('http://api.local/api/v1', 'tok-1');
    await client.discoverOpportunities();
    client.setToken('');
    await client.discoverOpportunities();
    assert.equal(seenHeaders[0].Authorization, 'Bearer tok-1');
    assert.equal(seenHeaders[1].Authorization, undefined);
  } finally {
    globalThis.fetch = originalFetch;
  }
});
