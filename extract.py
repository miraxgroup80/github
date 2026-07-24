import json, base64, urllib.request, sys

settings = json.loads(open("/opt/hca/.settings", "rb").read())
token = settings.get("authToken", "")
print(f"TOKEN_LEN: {len(token)}")
parts = token.split(".")
print(f"JWT_PARTS: {len(parts)}")
if len(parts) >= 2:
    header = json.loads(base64.urlsafe_b64decode(parts[0] + "=="))
    print(f"HEADER: {json.dumps(header)}")
    payload = json.loads(base64.urlsafe_b64decode(parts[1] + "=="))
    print(f"PAYLOAD: {json.dumps(payload, indent=2)}")

sched = settings.get("schedulerApiUrl", "")
print(f"SCHED: {sched}")

for path in ["", "/status", "/health", "/vms"][:3]:
    url = sched + path
    try:
        req = urllib.request.Request(url, method="GET")
        req.add_header("Authorization", "Bearer " + token)
        req.add_header("Content-Type", "application/json")
        resp = urllib.request.urlopen(req, timeout=3)
        print(f"ORCH {path}: [{resp.status}] {resp.read().decode()[:300]}")
    except urllib.error.HTTPError as e:
        print(f"ORCH {path}: [{e.code}] {e.read().decode()[:200]}")
    except Exception as ex:
        print(f"ORCH {path}: ERR {str(ex)[:100]}")

safe = {k: (v[:20]+"..." if k=="authToken" else v) for k,v in settings.items() if isinstance(v,str)}
print(f"SETTINGS: {json.dumps(safe, indent=2)}")
