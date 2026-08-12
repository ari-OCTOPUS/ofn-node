# 05-SSE-REPORT — SSE Trial (2026-08-12)

## TDR-SSE

```yaml
candidate: SSE (Server-Sent Events)
observed_problem: model path (DeepSeek) 20-40s blocking → client_timeout
baseline_evidence: runtime baseline p50=0.6ms (deterministic), model=20-40s
existing_component: ThreadingHTTPServer (blocking POST)
existing_limit: no streaming; client waits full response
trial_scope: GET /api/runs/{run_id}/events → text/event-stream
success_threshold: first event < 1s for deterministic; no regression
rollback: endpoint را حذف کن؛ مسیر قدیمی سالم
decision: TRIAL
```

## پیاده‌سازی

### Endpoint
```
GET /api/runs/{run_id}/events?after=<sequence>
Content-Type: text/event-stream; charset=utf-8
```

### SSE Format
```
id: 0
event: RUN_CREATED
data: {"sequence":0,"event_type":"RUN_CREATED",...}

id: 1
event: USER_MESSAGE_ACCEPTED
data: {"sequence":1,...}
```

### UI Client
XHR sync fetch در `buildSourcesPanel` (app.js) — eventهای کامل‌شده را می‌خواند.
پیشرفته‌تر: EventSource API برای streaming زنده (موج بعد).

## نتایج Trial

| معیار | نتیجه |
|-------|-------|
| endpoint موجود | ✅ `GET /api/runs/{id}/events` |
| content-type | `text/event-stream` ✅ |
| auth | owner-initdata ✅ |
| reconnect (after=N) | ✅ پشتیبانی می‌شود |
| cross-user leak | ✅ صفر (sanitize run_id) |
| gateway regression | 49/49 ✅ |

## تصمیم نهایی

**TRIAL → معتبر برای ادامه.** در نسخهٔ بعدی، SSE برای model path (DeepSeek stream:true) اجرا می‌شود.
الان events قبلاً نوشته شده‌اند قبل از response؛ SSE فقط read-back است.
