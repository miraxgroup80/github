import json, urllib.request

settings = json.loads(open("/opt/hca/.settings", "rb").read())
token = settings["authToken"]
trace = settings["traceApiUrl"]
wd = settings.get("watchdogTraceApiUrl", "")

print(f"TRACE: {trace}")

payloads = [
    ("empty", []),
    ("min", [{"message": "test"}]),
    ("hca_log", [{"level": "INFO", "ts": 1784889208.0, "logger": "hosted-compute-agent", "msg": "security test"}]),
    ("with_fields", [{"level": "INFO", "msg": "test", "orchestration_id": "test-123", "source_correlation_id": "test-456", "traceparent": "00-test-test-01"}]),
]

for label, payload in payloads:
    try:
        req = urllib.request.Request(trace, method="POST", data=json.dumps(payload).encode())
        req.add_header("Authorization", "Bearer " + token)
        req.add_header("Content-Type", "application/json")
        resp = urllib.request.urlopen(req, timeout=3)
        print(f"TRACE {label}: [{resp.status}] {resp.read().decode()[:200]}")
    except urllib.error.HTTPError as e:
        print(f"TRACE {label}: [{e.code}] {e.read().decode()[:200]}")
    except Exception as ex:
        print(f"TRACE {label}: ERR {str(ex)[:80]}")

# Watchdog
for label, payload in [("empty", []), ("min", [{"message": "test"}])]:
    try:
        req = urllib.request.Request(wd, method="POST", data=json.dumps(payload).encode())
        req.add_header("Authorization", "Bearer " + token)
        req.add_header("Content-Type", "application/json")
        resp = urllib.request.urlopen(req, timeout=3)
        print(f"WD {label}: [{resp.status}] {resp.read().decode()[:200]}")
    except urllib.error.HTTPError as e:
        print(f"WD {label}: [{e.code}] {e.read().decode()[:200]}")
    except Exception as ex:
        print(f"WD {label}: ERR {str(ex)[:80]}")

print("DONE")
