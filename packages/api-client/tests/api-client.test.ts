import test from 'node:test';
import assert from 'node:assert/strict';
import { OpportunityApiClient } from '../src/index.ts';

function jsonResponse(status, body) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

test('OpportunityApiClient sends Bearer token on canonical student profile endpoint', async () => {
  const originalFetch = globalThis.fetch;
  const calls = [];
  globalThis.fetch = async (url, init) => {
    calls.push({ url, method: init?.method ?? 'GET', headers: init?.headers });
    return jsonResponse(200, { userId: 'u1', collegeName: 'NIT Surathkal' });
  };
  try {
    const client = new OpportunityApiClient('http://api.local/api/v1', 'tok-1');
    const data = await client.getProfile();
    assert.deepEqual(data, { userId: 'u1', collegeName: 'NIT Surathkal' });
    assert.equal(calls[0].url, 'http://api.local/api/v1/users/me/student-profile');
    assert.equal(calls[0].method, 'GET');
    assert.equal(calls[0].headers.Authorization, 'Bearer tok-1');
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('OpportunityApiClient routes discover, eligibility, approval, and 204 delete cleanly', async () => {
  const originalFetch = globalThis.fetch;
  const calls = [];
  globalThis.fetch = async (url, init) => {
    calls.push({
      url,
      method: init?.method ?? 'GET',
      body: init?.body ? JSON.parse(init.body) : undefined,
    });
    if (calls.length === 5) {
      return new Response(null, { status: 204 });
    }
    return jsonResponse(200, { ok: true });
  };

  try {
    const client = new OpportunityApiClient('http://api.local/api/v1/', 'tok-1');
    await client.discoverOpportunities('backend internship');
    await client.discoverOpportunities();
    await client.checkEligibility('opp-42');
    await client.approveAction('apr-9', true);
    await client.deleteApplication('app-7');

    assert.deepEqual(calls[0], {
      url: 'http://api.local/api/v1/opportunities/discover',
      method: 'POST',
      body: { query: 'backend internship' },
    });
    assert.deepEqual(calls[1], {
      url: 'http://api.local/api/v1/opportunities',
      method: 'GET',
      body: undefined,
    });
    assert.deepEqual(calls[2], {
      url: 'http://api.local/api/v1/eligibility/evaluate',
      method: 'POST',
      body: { opportunityId: 'opp-42' },
    });
    assert.deepEqual(calls[3], {
      url: 'http://api.local/api/v1/agents/approvals/apr-9/decision',
      method: 'POST',
      body: { approved: true },
    });
    assert.deepEqual(calls[4], {
      url: 'http://api.local/api/v1/applications/app-7',
      method: 'DELETE',
      body: undefined,
    });
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('OpportunityApiClient refreshes once on 401 and surfaces RFC 7807 detail errors', async () => {
  const originalFetch = globalThis.fetch;
  const authHeaders = [];
  let calls = 0;
  let refreshCalls = 0;

  globalThis.fetch = async (_url, init) => {
    calls += 1;
    authHeaders.push(init?.headers?.Authorization);
    if (calls === 1) return jsonResponse(401, { detail: 'expired token' });
    return jsonResponse(200, { items: [{ id: 'opp-1' }], hasMore: false });
  };

  try {
    const client = new OpportunityApiClient('http://api.local/api/v1', 'old-tok', async () => {
      refreshCalls += 1;
      return 'fresh-tok';
    });
    const res = await client.discoverOpportunities('ml');
    assert.deepEqual(res, { items: [{ id: 'opp-1' }], hasMore: false });
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
    return jsonResponse(401, { detail: 'expired' });
  };

  try {
    const client = new OpportunityApiClient('http://api.local/api/v1', 'old-tok', async () => null);
    await assert.rejects(() => client.getProfile(), /expired/);
    await assert.rejects(() => client.getProfile(), /expired/);
    assert.equal(authHeaders[0], 'Bearer old-tok');
    assert.equal(authHeaders[1], undefined);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('OpportunityApiClient does not refresh on HTTP 403 and deduplicates concurrent 401 refreshes', async () => {
  const originalFetch = globalThis.fetch;
  let refreshCalls = 0;
  globalThis.fetch = async (_url, init) => {
    const auth = init?.headers?.Authorization;
    if (auth === 'Bearer forbidden-tok') {
      return jsonResponse(403, { detail: 'forbidden' });
    }
    if (auth === 'Bearer expired-tok') {
      return jsonResponse(401, { detail: 'expired' });
    }
    return jsonResponse(200, { ok: auth });
  };

  try {
    const forbiddenClient = new OpportunityApiClient(
      'http://api.local/api/v1',
      'forbidden-tok',
      async () => {
        refreshCalls += 1;
        return 'tok-2';
      }
    );
    await assert.rejects(() => forbiddenClient.getProfile(), /forbidden/);
    assert.equal(refreshCalls, 0);

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

test('OpportunityApiClient supports WS8 autonomous agent runs, commands, M11 resume, and screenshots', async () => {
  const originalFetch = globalThis.fetch;
  const calls = [];
  globalThis.fetch = async (url, init) => {
    calls.push({
      url,
      method: init?.method ?? 'GET',
      headers: init?.headers,
      body: init?.body ? JSON.parse(init.body) : undefined,
    });
    if (String(url).endsWith('/screenshot')) {
      return new Response(new Blob(['png-bytes'], { type: 'image/png' }), { status: 200 });
    }
    return jsonResponse(200, { ok: true });
  };
  try {
    const client = new OpportunityApiClient('http://api.local/api/v1', 'ws8-tok');
    await client.runAgentWorkflow({
      opportunityId: 'opp-99',
      query: 'Backend Intern',
      autoPrepareForm: true,
    });
    await client.getAgentSession('sess-1');
    await client.commandAgentSession('sess-1', { action: 'resume', command: 'Continue flow' });
    await client.approveAction('appr-1', true, undefined, true);
    const shotBlob = await client.fetchBrowserLogScreenshot('log-1');

    assert.equal(calls[0].url, 'http://api.local/api/v1/agents/runs');
    assert.equal(calls[0].method, 'POST');
    assert.deepEqual(calls[0].body, {
      opportunityId: 'opp-99',
      query: 'Backend Intern',
      autoPrepareForm: true,
    });
    assert.equal(calls[1].url, 'http://api.local/api/v1/agents/sessions/sess-1');
    assert.equal(calls[2].url, 'http://api.local/api/v1/agents/sessions/sess-1/command');
    assert.deepEqual(calls[2].body, { action: 'resume', command: 'Continue flow' });
    assert.equal(calls[3].url, 'http://api.local/api/v1/agents/approvals/appr-1/decision');
    assert.deepEqual(calls[3].body, { approved: true, executeSubmission: true });
    assert.equal(calls[4].url, 'http://api.local/api/v1/browser-logs/log-1/screenshot');
    assert.equal(calls[4].headers.Authorization, 'Bearer ws8-tok');
    assert.equal(await shotBlob.text(), 'png-bytes');
    assert.equal(
      client.getAgentSessionStreamUrl('sess-1', true),
      'http://api.local/api/v1/agents/sessions/sess-1/stream?once=true'
    );
  } finally {
    globalThis.fetch = originalFetch;
  }
});
