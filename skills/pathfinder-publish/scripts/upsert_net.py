"""Port of grafana-pathfinder-app/scripts/upsert-learning-path.sh. Works on Windows and macOS.

Uploads package directories (path + milestones, or standalone guide) as
InteractiveGuide resources on the Pathfinder Backend aggregator API.

Usage: python upsert_net.py <packages-root> [pkg ...] [--apply] [--status published|draft]

Requires GRAFANA_URL and GRAFANA_TOKEN in the environment. The token is not printed.
"""
import json, os, re, sys, urllib.error, urllib.request
sys.stdout.reconfigure(encoding="utf-8")

def _flag(name, default=None):
    if name not in sys.argv:
        return default
    i = sys.argv.index(name)
    if i + 1 >= len(sys.argv) or sys.argv[i + 1].startswith("--"):
        sys.exit(name + " needs a value")
    return sys.argv[i + 1]

APPLY = "--apply" in sys.argv
STATUS = _flag("--status", "published")
if STATUS not in ("published", "draft"):
    sys.exit("--status must be published or draft")
GRAFANA_URL = os.environ.get("GRAFANA_URL", "").rstrip("/")
TOKEN = os.environ.get("GRAFANA_TOKEN", "")
if not GRAFANA_URL.startswith("https://") or not TOKEN:
    sys.exit("Set GRAFANA_URL (https://your-stack) and GRAFANA_TOKEN. Do not commit the token.")
_consumed = set()
for _f in ("--status",):
    if _f in sys.argv:
        _consumed.add(sys.argv[sys.argv.index(_f) + 1])
_positional = [a for a in sys.argv[1:] if not a.startswith("--") and a not in _consumed]
if not _positional:
    sys.exit("usage: python upsert_net.py <packages-root> [pkg ...] [--apply] [--status published|draft]")
ROOT = _positional[0]
ONLY = _positional[1:]

MANAGED_BY_KEY = "pathfinderbackend.ext.grafana.app/managed-by"
MANAGED_BY_VALUE = "upsert-learning-path.sh"
SOURCE_PACKAGE_KEY = "pathfinderbackend.ext.grafana.app/source-package"
PORT_KEY = "pathfinderbackend.ext.grafana.app/uploader"
PORT_VALUE = "upsert_net.py"

BLOCK = set("action alt assistantEnabled assistantId assistantType authorNote autoCollapse blocks brief buttonText checkboxLabel choices code collapsed command completeEarly completionMode conditions content dataCheckBlocking dataCheckFailureMessage dataCheckQuery dataCheckTimeFrom dataCheckTimeTo datasourceFilter description display doIt end failureMessage formHint height hint hintLevels id inputType language lazyRender maxAttempts mode multiSelect objectives openGuide pattern placeholder prompt provider question reftarget required requirements screens scrollContainer setupCommands setupScript showMe shuffle skippable snippetId src start stepTimeout steps successCriteria targetstate targetvalue title tooltip type validateInput validationMessage variableName verify vmApp vmScenario vmTemplate welcome whenFalse whenFalseSectionConfig whenTrue whenTrueSectionConfig width".split())
STEP = set("action description formHint id lazyRender reftarget requirements scrollContainer skippable targetstate targetvalue tooltip validateInput".split())


def slugify(s):
    s = re.sub(r"[^a-z0-9-]+", "-", s.lower())
    s = re.sub(r"-+", "-", s)
    return s.strip("-")


def unknown_fields(blocks, depth=1, acc=None):
    acc = set() if acc is None else acc
    if depth > 2:
        return acc
    for b in blocks:
        acc |= set(b.keys()) - BLOCK
        for st in b.get("steps") or []:
            acc |= set(st.keys()) - STEP
        for key in ("blocks", "whenTrue", "whenFalse"):
            unknown_fields(b.get(key) or [], depth + 1, acc)
    return acc


def build_manifest(m):
    typed = {"id", "type", "repository", "description", "milestones", "tracks", "author", "category", "depends"}
    rest = {k: v for k, v in m.items() if k not in typed and v is not None}
    all_author = {k: v for k, v in (m.get("author") or {}).items() if v is not None}
    author = {k: all_author[k] for k in ("name", "team") if k in all_author}
    author_extra = {k: v for k, v in all_author.items() if k not in ("name", "team")}
    extra = dict(rest)
    if author_extra:
        extra["author"] = author_extra
    depends = [d if isinstance(d, list) else [d] for d in (m.get("depends") or [])]
    is_meta = m.get("type") in ("path", "journey")
    out = {"type": m["type"]}
    if m.get("repository"):
        out["repository"] = m["repository"]
    if m.get("description") is not None:
        out["description"] = m["description"]
    if m.get("category") is not None:
        out["category"] = m["category"]
    if author:
        out["author"] = author
    if is_meta and m.get("milestones"):
        out["milestones"] = m["milestones"]
    if m.get("type") == "path" and m.get("tracks"):
        out["tracks"] = m["tracks"]
    if depends:
        out["depends"] = depends
    if extra:
        out["additionalFields"] = extra
    return out


def req(method, path, body=None):
    data = None if body is None else json.dumps(body).encode("utf-8")
    headers = {"Authorization": "Bearer " + TOKEN, "Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(GRAFANA_URL + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request) as response:
            raw = response.read().decode("utf-8")
            return response.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as error:
        raw = error.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = {"message": raw[:500]}
        if not isinstance(parsed, dict):
            parsed = {"message": str(parsed)[:500]}
        return error.code, parsed


s, fs = req("GET", "/api/frontend/settings")
if s != 200 or "namespace" not in fs:
    sys.exit(f"could not read stack settings ({s}). Check GRAFANA_URL and that the token can call the API.")
NS = fs["namespace"]
BASE = f"/apis/pathfinderbackend.ext.grafana.app/v1alpha1/namespaces/{NS}/interactiveguides"
s, lst = req("GET", BASE + "?limit=500")
if s != 200:
    sys.exit(f"could not list guides ({s}): {lst.get('message', '')[:200]}")
existing = {it["metadata"]["name"]: (it["metadata"].get("annotations") or {}).get(MANAGED_BY_KEY, "unmanaged") for it in lst.get("items", [])}
host = GRAFANA_URL.split("//", 1)[-1].split("/")[0]
print(f"stack {host} ns {NS} | existing guides {len(existing)} | mode {'APPLY' if APPLY else 'dry run'} | status {STATUS}\n")


def load(d):
    return (json.load(open(os.path.join(d, "manifest.json"), encoding="utf-8")),
            json.load(open(os.path.join(d, "content.json"), encoding="utf-8")))


def make_spec(d, expected_id):
    m, c = load(d)
    assert c["id"] == expected_id, f"{d}: content id {c['id']} != {expected_id}"
    assert slugify(c["id"]) == c["id"], f"{d}: id not slug-safe"
    assert c["blocks"], f"{d}: empty blocks"
    unk = unknown_fields(c["blocks"])
    if unk:
        print(f"    warning: {c['id']} uses undeclared block fields: {sorted(unk)}")
    spec = dict(c)
    spec["status"] = STATUS
    spec["manifest"] = build_manifest(m)
    spec.setdefault("schemaVersion", "1.0.0")
    return spec


def write(name, spec, pkg_id):
    ann = {MANAGED_BY_KEY: MANAGED_BY_VALUE, SOURCE_PACKAGE_KEY: pkg_id, PORT_KEY: PORT_VALUE}
    s, cur = req("GET", f"{BASE}/{name}")
    if s == 200:
        owner = (cur["metadata"].get("annotations") or {}).get(MANAGED_BY_KEY, "unmanaged")
        if owner != MANAGED_BY_VALUE:
            return "REFUSED (owned by %s)" % owner
        env_ = {"apiVersion": "pathfinderbackend.ext.grafana.app/v1alpha1", "kind": "InteractiveGuide",
                "metadata": {"name": name, "namespace": NS, "resourceVersion": cur["metadata"]["resourceVersion"],
                             "annotations": {**(cur["metadata"].get("annotations") or {}), **ann}},
                "spec": spec}
        s2, body = req("PUT", f"{BASE}/{name}", env_)
        return "updated" if 200 <= s2 < 300 else f"FAILED PUT {s2}: {body.get('message', body)}"
    if s == 404:
        env_ = {"apiVersion": "pathfinderbackend.ext.grafana.app/v1alpha1", "kind": "InteractiveGuide",
                "metadata": {"name": name, "namespace": NS, "annotations": ann}, "spec": spec}
        s2, body = req("POST", BASE, env_)
        return "created" if 200 <= s2 < 300 else f"FAILED POST {s2}: {body.get('message', body)}"
    return f"FAILED GET {s}: {cur}"


totals = {"created": 0, "updated": 0, "failed": 0, "planned": 0}
pkgs = sorted(p for p in os.listdir(ROOT) if os.path.isdir(os.path.join(ROOT, p)))
if ONLY:
    pkgs = [p for p in pkgs if p in ONLY]
for pkg in pkgs:
    pdir = os.path.join(ROOT, pkg)
    m, c = load(pdir)
    pkg_id = m["id"]
    milestones = m.get("milestones") or [] if m["type"] != "guide" else []
    index = {}
    for sub in os.listdir(pdir):
        sd = os.path.join(pdir, sub)
        if os.path.isdir(sd) and os.path.exists(os.path.join(sd, "manifest.json")):
            index[json.load(open(os.path.join(sd, "manifest.json"), encoding="utf-8"))["id"]] = sd
    order = [(mid, index[mid]) for mid in milestones] + [(pkg_id, pdir)]
    print(f"{pkg_id} ({m['type']}, {len(order)} resources)")
    specs = []
    for mid, d in order:
        try:
            specs.append((mid, make_spec(d, mid)))
        except AssertionError as e:
            print("   ", e); totals["failed"] += 1
    clashes = [mid for mid, _ in specs if existing.get(mid) not in (None, MANAGED_BY_VALUE)]
    if clashes:
        print(f"    refusing: existing unmanaged guides {clashes}"); totals["failed"] += len(specs); continue
    for mid, spec in specs:
        note = "updates existing" if mid in existing else "new"
        if not APPLY:
            print(f"    plan  {mid}  ({len(spec['blocks'])} blocks, {note})"); totals["planned"] += 1
        else:
            r = write(mid, spec, pkg_id)
            print(f"    {r:8} {mid}  ({len(spec['blocks'])} blocks)")
            totals["created" if r == "created" else "updated" if r == "updated" else "failed"] += 1
print("\n", totals)
