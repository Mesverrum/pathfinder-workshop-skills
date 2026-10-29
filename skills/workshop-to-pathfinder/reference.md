# Workshop conversion reference

Proven while converting the Observability Workshop Breakouts on Grafana 13.3.0 and Pathfinder 2.24.0. Re-check hooks when a plugin version changes.

## Disk layout

```
<packages>/<path-id>/manifest.json
<packages>/<path-id>/content.json
<packages>/<path-id>/<milestone-id>/manifest.json
<packages>/<path-id>/<milestone-id>/content.json
```

Path manifest `milestones` is the bar order. `content.json` `id` equals the folder id. `schemaVersion` is `1.1.0`.

Publisher annotation `pathfinderbackend.ext.grafana.app/managed-by` must be `upsert-learning-path.sh`. The uploader will not touch a guide with any other value.

API: `/apis/pathfinderbackend.ext.grafana.app/v1alpha1/namespaces/<ns>/interactiveguides/<id>`. Namespace comes from `GET /api/frontend/settings`. Get and list need Viewer. Create and update need Editor. A dry-run 201 does not prove the real write is allowed.

## Question block

```python
opener = {
    "id": f"{guide}-{slug}-open",
    "type": "interactive",
    "action": "navigate",
    "doIt": True,
    "showMe": True,
    "reftarget": "/a/grafana-app-observability-app/services/service/ecommerce-prod---productcatalogservice",
    "requirements": ["has-plugin:grafana-app-observability-app"],
    "content": "Open **productcatalogservice**. Set the time picker to **Last 1 hour**.",
    "tooltip": "Do it opens this page.",
    "skippable": True,
    # verify only when this path is not a prefix of another page in the same lab
    "verify": "on-page:/a/grafana-app-observability-app/services/service/ecommerce-prod---productcatalogservice",
}
guided = {
    "id": f"{guide}-{slug}",
    "type": "guided",
    "content": "**Question:** What error is the service throwing?\n\nShow me outlines the control. Click the outline to continue.",
    "requirements": ["has-plugin:grafana-app-observability-app"],
    "skippable": True,
    "steps": [{
        "id": f"{guide}-{slug}-step-1",
        "action": "highlight",
        "reftarget": "a[href$='/traces'], [data-cy='traces-table-container']",
        "description": "Open **Traces** for this service.",
        "tooltip": "Show me outlines this. Click the outlined control to continue.",
        "requirements": [
            "has-plugin:grafana-app-observability-app",
            "on-page:/a/grafana-app-observability-app/services/service/ecommerce-prod---productcatalogservice",
            "exists-reftarget",
        ],
        "skippable": True,
    }],
}
```

Wrap `[opener, prompt markdown, guided, answer callout]` in `section()`. Import `section`, `md`, `callout`, `quiz`, and `validate` from `pathfinder-author/scripts/pf.py`. Call `validate(blocks, where)` before writing.

`build.py` is the only file you edit. A second run with no spec change should rewrite the same JSON.

## Selector dialect that outlined on a real page

Comma-separated CSS plus jQuery-style `:contains('...')`.

| Need | Target |
|---|---|
| App card | `[data-testid='app-card']:contains('ecommerce')` |
| Stat or chart header | `[data-testid='data-testid Panel header Page Loads']` |
| Column of icons | `[data-cy^='servicetechnology-']` |
| Exact service, not the europe twin | `a[href$='ecommerce-prod---productcatalogservice']` |
| Trace id link | `a[href*='traceId']` |
| Span in a trace | `[data-testid='SpanBar--wrapper']` |
| Pod section | `h3:contains('Pod information')` |
| Column | `th:contains('Image Spec'), [role='columnheader']:contains('Image Spec')` |
| Knowledge Graph card | `[data-testid='catalog-entity-name-btn']` |
| Composer, when you have not found a better hook | `textarea` |

`button` action is only for a label you have seen on a `<button>`. `button:contains('...')` as a highlight selector is the safer form when you are not sure the runtime treats the string as a label.

## Plugin ids to confirm on the target stack

Confirm with `GET /api/plugins` before reusing.

| App | Plugin id | Start |
|---|---|---|
| Frontend Observability | `grafana-kowalski-app` | `/a/grafana-kowalski-app` |
| Application Observability | `grafana-app-observability-app` | `/a/grafana-app-observability-app/services` |
| Kubernetes Monitoring | `grafana-k8s-app` | `/a/grafana-k8s-app/home` |
| Knowledge Graph | `grafana-asserts-app` | `/a/grafana-asserts-app/catalog` |
| RCA Workbench | same plugin | `/a/grafana-asserts-app/assertions` |
| Assistant | `grafana-assistant-app` | `/a/grafana-assistant-app` |

Kubernetes workload detail is `/a/grafana-k8s-app/navigation/namespace/{cluster}/{namespace}/{workloadType}/{workload}`. Do not hardcode a cluster name you have not read from the stack. Link from the workload list: `a[href*='/navigation/namespace/'][href*='productcatalogservice']:not([href*='europe'])`.

## Check before you call it done

```
python skills/workshop-to-pathfinder/scripts/check.py <packages-root>
```

The script rejects a guided `reftarget` that does not start with `[`, `#`, `.`, `a[`, `a:`, `button`, `input`, `textarea`, `th`, `h1`, `h3`, or `span`. A real button is `button:contains('Save')`, not the bare word `Save`. It also rejects an `on-page` path that is a strict prefix of another page in the same guide, a guided id reused as a section id, a guided question with no `Answer to compare` callout, and a guide without exactly one quiz.

That script does not click. The click sample in `SKILL.md` is the pass rule: Show me outlines the named control. Skip is a fail.

## Upload

Set `GRAFANA_URL` and `GRAFANA_TOKEN` in the environment. Do not commit the token.

```
python <skills>/pathfinder-publish/scripts/upsert_net.py <packages-root>
python <skills>/pathfinder-publish/scripts/upsert_net.py <packages-root> --apply --status published
python <skills>/pathfinder-publish/scripts/readback.py <packages-root>
```

The first command is the dry run. Stop there until the user confirms. `--status published` is what learners see. Default status in the uploader is already `published`. Use `draft` only when the user wants the editor library.

Readback catches fields the API stripped (`verify`, conditional configs). A stripped `verify` leaves a navigate step that completes without the page being open.
