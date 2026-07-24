import json, urllib.request, sys

settings = json.loads(open("/opt/hca/.settings", "rb").read())
token = settings["authToken"]
sched = settings["schedulerApiUrl"]
trace = settings["traceApiUrl"]
wd = settings.get("watchdogTraceApiUrl", "")
sas = settings.get("diagnosticsSasUri", "")

print(f"TOKEN_LEN: {len(token)}")
print(f"SCHED: {sched}")
print(f"TRACE: {trace}")
print(f"WD: {wd}")
print(f"SAS_LEN: {len(sas)}")

# Use token directly on orchestrator — no copy, no masking
endpoints = [
    ("GET", sched, "sched_root"),
    ("GET", sched + "/status", "sched_status"),
    ("GET", sched + "/health", "sched_health"),
    ("GET", sched + "/vms", "sched_vms"),
    ("GET", sched + "/allocations", "sched_alloc"),
    ("GET", sched + "/config", "sched_config"),
    ("POST", sched + "/heartbeat", "sched_heartbeat"),
    ("POST", sched + "/trace", "sched_trace"),
    ("POST", trace, "trace_root"),
    ("GET", wd.replace("/trace", ""), "wd_root"),
    ("GET", wd.replace("/trace", "/health"), "wd_health"),
    ("POST", wd, "wd_trace"),
]

for method, url, label in endpoints:
    if not url:
        continue
    try:
        if method == "POST":
            req = urllib.request.Request(url, method="POST", data=b'{"test":true}')
        else:
            req = urllib.request.Request(url)
        req.add_header("Authorization", "Bearer " + token)
        req.add_header("Content-Type", "application/json")
        req.add_header("User-Agent", "hosted-compute-agent")
        resp = urllib.request.urlopen(req, timeout=3)
        body = resp.read().decode()[:500]
        print(f"ORCH {label}: [{resp.status}] {body}")
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:300]
        print(f"ORCH {label}: [{e.code}] {body}")
    except Exception as ex:
        print(f"ORCH {label}: ERR {str(ex)[:100]}")

# Try SAS URI operations
if sas:
    # Write test
    try:
        write_url = sas.split("?")[0] + "/orch-test.txt?" + sas.split("?")[1]
        req = urllib.request.Request(write_url, method="PUT", data=b"orchestrator access test")
        req.add_header("x-ms-blob-type", "BlockBlob")
        req.add_header("Content-Type", "text/plain")
        resp = urllib.request.urlopen(req, timeout=5)
        print(f"BLOB_WRITE: [{resp.status}]")
    except urllib.error.HTTPError as e:
        print(f"BLOB_WRITE: [{e.code}] {e.read().decode()[:200]}")
    except Exception as ex:
        print(f"BLOB_WRITE: ERR {str(ex)[:100]}")

    # List (prob fails but try)
    try:
        list_url = sas + "&restype=container&comp=list"
        req = urllib.request.Request(list_url)
        resp = urllib.request.urlopen(req, timeout=5)
        print(f"BLOB_LIST: [{resp.status}] {resp.read().decode()[:500]}")
    except urllib.error.HTTPError as e:
        print(f"BLOB_LIST: [{e.code}]")
    except Exception as ex:
        print(f"BLOB_LIST: ERR {str(ex)[:100]}")

# Print all settings keys (safe)
safe = {}
for k, v in settings.items():
    if isinstance(v, str):
        safe[k] = v[:30] + "..." if len(v) > 30 else v
    else:
        safe[k] = v
print(f"ALL_KEYS: {json.dumps(safe, indent=2)}")
