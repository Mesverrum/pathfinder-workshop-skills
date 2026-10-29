# Pathfinder author reference

Schema source is `grafana/grafana-pathfinder-app` (InteractiveGuide CRD and the guide JSON schema). This file is the subset these skills actually emit, plus the constraints found by publishing to a Cloud stack.

## Block types these skills emit

`markdown`, `callout`, `section` (`autoCollapse`), `interactive`, `quiz`, `challenge`, `conditional` (`display: "section"`, `whenTrue` / `whenFalse`, section configs), `terminal`, `terminal-connect`.

`interactive.action` is one of `highlight`, `button`, `navigate`. (`formfill`, `hover`, `noop`, `popout` parse, and we do not use them.)

Other types the publisher allowlist accepts but these builders do not emit: `divider`, `html`, `image`, `video`, `multistep`, `guided`, `input`, `code-block`, `grot-guide`, `snippet-ref`, `collapsible`, `assistant`. Workshop click-throughs use `guided` (see `workshop-to-pathfinder`). Do not add a JSON field the publisher does not list in `BLOCK` inside `pathfinder-publish/scripts/upsert_net.py`; it warns, and an unknown field the API rejects fails the whole write.

## Requirement tokens

All of these are accepted by `validate()` in `scripts/pf.py`. Every token in `requirements`, `conditions`, `verify`, `objectives`, and challenge `successCriteria` must match.

| Token | Use |
|---|---|
| `on-page:/explore` | Prefix match. Also `/d` (covers `/d/<uid>`, `/dashboard/new`, `/dashboards`), `/dashboard/new`, `/a/<plugin>` |
| `has-datasource:<type>` | `prometheus`, `loki`, `tempo` |
| `has-plugin:<id>` | App plugin installed, e.g. `grafana-k8s-app` |
| `has-dashboard-named:<title>` | Exact dashboard title. Challenge success check |
| `min-version:x.y.z` | Grafana version |
| `is-editor` / `is-admin` | Role gates. Put writes inside a conditional, do not only hide them |
| `exists-reftarget` | Pair with a visible-text button |
| `is-terminal-active` | After `terminal-connect` |

Also parsed, rarely needed: `navmenu-open`, `datasource-configured:`, `has-permission:`, `has-role:`, `section-completed:`, `has-feature:`, `in-environment:`, `var-<name>:`, `renderer:`, `coda-exit-zero:`, `is-logged-in`, `dashboard-exists`, `has-datasources`, `form-valid`.

## Selectors

Written as `grafana:<export from @grafana/e2e-selectors>`. Resolved by the plugin, not by CSS. Pinned to the 13.2.2 selector package against Grafana 13.3.0. Re-check when the stack upgrades.

| Constant in pf.py | Selector | Step |
|---|---|---|
| `PROM_FIELD` | `components.DataSource.Prometheus.queryEditor.code.queryField` | PromQL query box |
| `LOKI_FIELD` | `components.QueryField.container` | Loki query box |
| `TEMPO_FIELD` | `components.CodeEditor.container` | TraceQL editor |
| `RUN` | `components.RefreshPicker.runButtonV2` | Run query |
| `ADDQ` | `pages.Explore.General.addQueryRow` | Add query (13.2+) |
| `INSPECT` | `components.QueryTab.queryInspectorButton` | Query inspector. Set `targetstate` to `"true"` |
| `DSPICK` | `components.DataSourcePicker.container` | Datasource picker |
| `TOGGLE` | `components.DataSource.Prometheus.queryEditor.editorToggle` | Builder / Code |
| `ADD_DASH` | `pages.Explore.toolbar.addToDashboardButton` | Add to dashboard |
| `DASH_SAVE` | `components.NavToolbar.editDashboard.saveButton` | Save dashboard |
| `SAVE_TITLE` | `components.DashboardSaveDrawer.saveAsTitleInput` | Title in the save drawer (13.2+) |
| `VIZ_PICKER` | `components.PanelEditor.toggleVizPicker` | Visualization picker |
| `VAR_NEW` | `pages.Dashboard.Settings.Variables.List.newButton` | New variable |
| `SHARE` / `EXPORT` | `pages.Dashboard.DashNav.newShareButton` / `NewExportButton` | Share and export menus |

### Panels on a dashboard (lesson boards)

`reftarget: "panel:<Panel title>"` resolves to the whole panel container (`[data-viz-panel-key]:has([data-testid*="Panel header <title>"])`), plugin 2.5.0+. `panel:<title> > <css>` scopes a child selector inside that panel. The match is a substring on the header test id, so no panel title on the board may be a substring of another. Pair with `on-page:/d` and a `navigate` to `/d/<uid>`. The equivalent parameterized form is `grafana:components.Panels.Panel.title:<title>` (header only, not the container). Source: `src/lib/dom/selector-resolver-core.ts` in grafana-pathfinder-app.

## Guide shape on disk

```
<packages>/<pkg>/manifest.json
<packages>/<pkg>/content.json          # path landing, type path
<packages>/<pkg>/<milestone>/manifest.json
<packages>/<pkg>/<milestone>/content.json
```

The path manifest `milestones` array is the order of the bar. Resource name equals the manifest `id` (slug-safe). `content.json` `id` must equal that id.

## API behavior worth remembering

- Guides are `InteractiveGuide` resources: `/apis/pathfinderbackend.ext.grafana.app/v1alpha1/namespaces/<ns>/interactiveguides/<id>`.
- Namespace comes from `GET /api/frontend/settings` (`namespace`), not from a guess.
- A dry-run write can return 201 on a stack that then 403s the real POST. A 403 means the token's role cannot create or update guides. Editor can. Viewer cannot. Read the error from the real write.
- Opening a milestone id renders that guide alone, with no bar.
