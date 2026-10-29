"""Compare local InteractiveGuide block fields with the copies on a stack.

Usage: python readback.py <packages-root> [pkg ...]

Requires GRAFANA_URL and GRAFANA_TOKEN. The token is not printed.
"""
import json, os, sys, urllib.error, urllib.request
sys.stdout.reconfigure(encoding="utf-8")


GRAFANA_URL = os.environ.get("GRAFANA_URL", "").rstrip("/")
TOKEN = os.environ.get("GRAFANA_TOKEN", "")
if not GRAFANA_URL.startswith("https://") or not TOKEN:
    sys.exit("Set GRAFANA_URL (https://your-stack) and GRAFANA_TOKEN. Do not commit the token.")
positional = [a for a in sys.argv[1:] if not a.startswith("--")]
if not positional:
    sys.exit("usage: python readback.py <packages-root> [pkg ...]")
ROOT = positional[0]
ONLY = positional[1:]


def get(path):
    request = urllib.request.Request(
        GRAFANA_URL + path,
        headers={"Authorization": "Bearer " + TOKEN, "Accept": "application/json"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        raw = error.read().decode("utf-8", errors="replace")
        sys.exit(f"GET {path} failed ({error.code}): {raw[:200]}")


def fields(blocks, acc):
    for b in blocks or []:
        if not isinstance(b, dict):
            continue
        t = b.get("type", "?")
        for k in b:
            acc.add(t + "." + k)
        for key in ("blocks", "whenTrue", "whenFalse"):
            if b.get(key):
                fields(b[key], acc)
    return acc


ns = get("/api/frontend/settings")["namespace"]
base = f"/apis/pathfinderbackend.ext.grafana.app/v1alpha1/namespaces/{ns}/interactiveguides"
items = {it["metadata"]["name"]: it for it in get(base + "?limit=500").get("items", [])}
host = GRAFANA_URL.split("//", 1)[-1].split("/")[0]
print(f"stack {host} ns {ns} guides {len(items)}")

pkgs = ONLY or sorted(p for p in os.listdir(ROOT) if os.path.isdir(os.path.join(ROOT, p)))
missing = dropped = checked = 0
for pkg in pkgs:
    pdir = os.path.join(ROOT, pkg)
    dirs = [pdir] + [os.path.join(pdir, s) for s in sorted(os.listdir(pdir)) if os.path.isdir(os.path.join(pdir, s))]
    for d in dirs:
        man_p = os.path.join(d, "manifest.json")
        con_p = os.path.join(d, "content.json")
        if not (os.path.exists(man_p) and os.path.exists(con_p)):
            continue
        name = json.load(open(man_p, encoding="utf-8"))["id"]
        local = json.load(open(con_p, encoding="utf-8"))["blocks"]
        it = items.get(name)
        rel = os.path.relpath(d, ROOT)
        if not it:
            print(f"MISSING {rel} ({name})")
            missing += 1
            continue
        remote = it.get("spec", {}).get("blocks") or []
        gone = sorted(fields(local, set()) - fields(remote, set()))
        checked += 1
        if gone:
            dropped += 1
            print(f"DROPPED {rel}: {gone}")
print(f"checked {checked} missing {missing} with-drops {dropped}")
sys.exit(1 if missing or dropped else 0)
