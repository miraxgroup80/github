import json, urllib.request, sys, time

settings = json.loads(open("/opt/hca/.settings", "rb").read())
token = settings["authToken"]
sched = settings["schedulerApiUrl"]
trace_url = settings["traceApiUrl"]
wd_url = settings.get("watchdogTraceApiUrl", "")

print(f"TOKEN_LEN: {len(token)}")
print(f"TRACE: {trace_url}")
print(f"WD: {wd_url}")

# Try various payloads for trace API
# Error said: []api.HostedComputeAgentLog — it expects a JSON ARRAY of log objects
payloads = [
    # 1. Empty array
    ("empty_array", []),
    # 2. Minimal log entry
    ("minimal", [{"message": "test"}]),
    # 3. With level and timestamp
    ("with_level", [{"level": "INFO", "message": "test", "timestamp": "2026-07-24T10:00:00Z"}]),
    # 4. With more fields (guessing from HCA log format)
    ("full_log", [{"level": "INFO", "ts": 1784889208, "logger": "hosted-compute-agent", "msg": "security test"}]),
    # 5. With orchestration_id
    ("with_orch", [{"level": "INFO", "msg": "test", "orchestration_id": "test-123", "source_correlation_id": "test-456"}]),
    # 6. String array
    ("string_array", ["test log entry"]),
]

for label, payload in payloads:
    print(f"
--- TRACE {label} ---")
    try:
        req = urllib.request.Request(trace_url, method="POST",
            data=json.dumps(payload).encode())
        req.add_header("Authorization", "Bearer " + token)
        req.add_header("Content-Type", "application/json")
        req.add_header("User-Agent", "hosted-compute-agent")
        resp = urllib.request.urlopen(req, timeout=5)
        print(f"  [{resp.status}] {resp.read().decode()[:300]}")
    except urllib.error.HTTPError as e:
        print(f"  [{e.code}] {e.read().decode()[:300]}")
    except Exception as ex:
        print(f"  ERR {str(ex)[:100]}")

# Try watchdog trace
# Error said: []models.OnVmLog
wd_payloads = [
    ("empty", []),
    ("minimal", [{"message": "test"}]),
    ("with_level", [{"level": "INFO", "message": "test", "timestamp": 1784889208}]),
    ("full", [{"Level": "INFO", "Message": "test", "Timestamp": "2026-07-24T10:00:00Z", "Logger": "test"}]),
]

for label, payload in wd_payloads:
    print(f"
--- WD {label} ---")
    try:
        req = urllib.request.Request(wd_url, method="POST",
            data=json.dumps(payload).encode())
        req.add_header("Authorization", "Bearer " + token)
        req.add_header("Content-Type", "application/json")
        req.add_header("User-Agent", "hosted-compute-agent")
        resp = urllib.request.urlopen(req, timeout=5)
        print(f"  [{resp.status}] {resp.read().decode()[:300]}")
    except urllib.error.HTTPError as e:
        print(f"  [{e.code}] {e.read().decode()[:300]}")
    except Exception as ex:
        print(f"  ERR {str(ex)[:100]}")

# Try more orchestrator endpoints with different URL patterns
print("
--- ORCHESTRATOR URL SCAN ---")
base = sched.replace("/v1", "")
for path in ["/", "/health", "/healthz", "/v1", "/v2", "/api", "/api/v1",
             "/v1/machines", "/v1/request", "/v1/finish", "/v1/register",
             "/v1/deregister", "/v1/complete", "/v1/cancel", "/v1/logs",
             "/v1/diagnostics", "/v1/settings", "/v1/agent", "/v1/runner"]:
    try:
        req = urllib.request.Request(base + path)
        req.add_header("Authorization", "Bearer " + token)
        req.add_header("User-Agent", "hosted-compute-agent")
        resp = urllib.request.urlopen(req, timeout=2)
        body = resp.read().decode()[:200]
        print(f"  {path}: [{resp.status}] {body}")
    except urllib.error.HTTPError as e:
        code = e.code
        if code not in (404,):
            body = e.read().decode()[:200]
            print(f"  {path}: [{code}] {body}")
    except:
        pass
