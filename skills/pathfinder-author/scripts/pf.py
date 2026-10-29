"""Block builders for Pathfinder InteractiveGuide JSON."""
import json, re, urllib.parse

PROM = "grafanacloud-prom"
LOKI = "grafanacloud-logs"
TEMPO = "grafanacloud-traces"

# --- selectors (grafana-e2e-selectors 13.2.2, stack is 13.3.0) ---
PROM_FIELD = "grafana:components.DataSource.Prometheus.queryEditor.code.queryField"
LOKI_FIELD = "grafana:components.QueryField.container"            # Loki Monaco wrapper
TEMPO_FIELD = "grafana:components.CodeEditor.container"           # Tempo TraceQL editor (@grafana/ui CodeEditor)
RUN = "grafana:components.RefreshPicker.runButtonV2"
ADDQ = "grafana:pages.Explore.General.addQueryRow"                # 13.2+
INSPECT = "grafana:components.QueryTab.queryInspectorButton"
DSPICK = "grafana:components.DataSourcePicker.container"
TOGGLE = "grafana:components.DataSource.Prometheus.queryEditor.editorToggle"
ADD_DASH = "grafana:pages.Explore.toolbar.addToDashboardButton"    # 13.2+
SPLIT = "grafana:pages.Explore.toolbar.split"                      # 12.4+
# dashboards
DASH_SAVE = "grafana:components.NavToolbar.editDashboard.saveButton"
DASH_SETTINGS = "grafana:components.NavToolbar.editDashboard.settingsButton"
DASH_EDIT = "grafana:components.NavToolbar.editDashboard.editButton"
SAVE_TITLE = "grafana:components.DashboardSaveDrawer.saveAsTitleInput"
SAVE_CONFIRM = "grafana:components.DashboardSaveDrawer.saveButton"
SIDEBAR_ADD = "grafana:pages.Dashboard.Sidebar.addButton"          # 12.4+
SIDEBAR_OPTIONS = "grafana:pages.Dashboard.Sidebar.optionsButton"  # 12.4+
PANEL_ADD_QUERY = "grafana:components.QueryTab.addQuery"
ADD_TRANSFORM = "grafana:components.Transforms.addTransformationButton"
VIZ_PICKER = "grafana:components.PanelEditor.toggleVizPicker"
OPTIONS_PANE = "grafana:components.PanelEditor.OptionsPane.content"
VAR_NEW = "grafana:pages.Dashboard.Settings.Variables.List.newButton"
SHARE = "grafana:pages.Dashboard.DashNav.newShareButton.container"
SHARE_MENU = "grafana:pages.Dashboard.DashNav.newShareButton.arrowMenu"
SHARE_INTERNAL = "grafana:pages.Dashboard.DashNav.newShareButton.menu.shareInternally"
SHARE_EXTERNAL = "grafana:pages.Dashboard.DashNav.newShareButton.menu.shareExternally"
SHARE_SNAPSHOT = "grafana:pages.Dashboard.DashNav.newShareButton.menu.shareSnapshot"
LOCK_RANGE = "grafana:pages.ShareDashboardDrawer.ShareInternally.lockTimeRangeSwitch"
SHORTEN = "grafana:pages.ShareDashboardDrawer.ShareInternally.shortenUrlSwitch"
COPY_URL = "grafana:pages.ShareDashboardDrawer.ShareInternally.copyUrlButton"
EXPORT = "grafana:pages.Dashboard.DashNav.NewExportButton.container"
EXPORT_MENU = "grafana:pages.Dashboard.DashNav.NewExportButton.arrowMenu"
EXPORT_IMAGE = "grafana:pages.Dashboard.DashNav.NewExportButton.Menu.exportAsImage"

ON_EXPLORE = ["on-page:/explore"]
ON_DASH = ["on-page:/d"]          # /d/<uid>, /dashboard/new, /dashboards
ON_NEW_DASH = ["on-page:/dashboard/new"]


def blank_explore(ds):
    if ds == "tempo":
        q = {"refId": "A", "queryType": "traceql", "query": "", "limit": 20, "datasource": {"type": "tempo", "uid": TEMPO}}
        pane = {"datasource": TEMPO, "queries": [q], "range": {"from": "now-1h", "to": "now"}}
    elif ds == "loki":
        q = {"refId": "A", "expr": "", "editorMode": "code", "queryType": "range", "datasource": {"type": "loki", "uid": LOKI}}
        pane = {"datasource": LOKI, "queries": [q], "range": {"from": "now-1h", "to": "now"}}
    else:
        q = {"refId": "A", "expr": "", "editorMode": "code", "datasource": {"type": "prometheus", "uid": PROM}}
        pane = {"datasource": PROM, "queries": [q], "range": {"from": "now-1h", "to": "now"}}
    return "/explore?" + urllib.parse.urlencode({"orgId": "1", "schemaVersion": "1", "panes": json.dumps({"q": pane}, separators=(",", ":"))})


FIELD = {"prom": PROM_FIELD, "loki": LOKI_FIELD, "tempo": TEMPO_FIELD}
DSNAME = {"prom": "Prometheus", "loki": "Loki", "tempo": "Tempo"}
LANG = {"prom": "promql", "loki": "logql", "tempo": "traceql"}


def fence(code, lang):
    return "\n\n```" + lang + "\n" + code + "\n```"


def navigate(ds, extra=""):
    name = DSNAME[ds]
    mode = " in **Code** mode" if ds != "tempo" else " on the **TraceQL** tab"
    return {
        "type": "interactive",
        "id": "open-explore-" + ds,
        "action": "navigate",
        "doIt": True,
        "showMe": True,
        "reftarget": blank_explore(ds),
        "verify": "on-page:/explore",
        "content": f"Open **Explore** on the {name} datasource{mode}. The query box is empty on purpose. You type every query in this section yourself.{extra} This step stays open until Explore is actually on screen.",
        "tooltip": "Do it opens a blank Explore. The step completes when the URL is /explore.",
    }


def nav(bid, text, path, tooltip, verify=None, requirements=None, skippable=False, hint=None):
    b = {"type": "interactive", "id": bid, "action": "navigate", "doIt": True, "showMe": True, "reftarget": path, "content": text, "tooltip": tooltip}
    if verify:
        b["verify"] = verify
    if requirements:
        b["requirements"] = requirements
    if skippable:
        b["skippable"] = True
    if hint:
        b["hint"] = hint
    return b


def paste(ds, bid, text, code, tooltip, hint=None, requirements=None):
    b = {
        "type": "interactive",
        "id": bid,
        "action": "highlight",
        "showMe": True,
        "doIt": False,
        "reftarget": FIELD[ds],
        "requirements": requirements or ON_EXPLORE,
        "content": text + fence(code, LANG[ds]),
        "tooltip": tooltip,
    }
    if hint:
        b["hint"] = hint
    return b


def click(bid, text, reftarget, tooltip, targetstate=None, skippable=False, hint=None, requirements=None, extra_req=None):
    b = {
        "type": "interactive",
        "id": bid,
        "action": "button",
        "showMe": True,
        "doIt": True,
        "reftarget": reftarget,
        "requirements": (requirements if requirements is not None else ON_EXPLORE) + (extra_req or []),
        "content": text,
        "tooltip": tooltip,
    }
    if targetstate:
        b["targetstate"] = targetstate
    if skippable:
        b["skippable"] = True
    if hint:
        b["hint"] = hint
    return b


def textbtn(bid, text, label, tooltip, requirements=None, hint=None):
    """Button matched by its visible label. Gated on the button existing, always skippable."""
    return click(bid, text, label, tooltip, skippable=True, hint=hint, requirements=(requirements or []) + ["exists-reftarget"])


def highlight(bid, text, reftarget, tooltip, requirements=None, skippable=True, hint=None):
    b = {"type": "interactive", "id": bid, "action": "highlight", "showMe": True, "doIt": False, "reftarget": reftarget, "requirements": requirements or [], "content": text, "tooltip": tooltip}
    if skippable:
        b["skippable"] = True
    if hint:
        b["hint"] = hint
    return b


def run(bid="run", text="Click **Run query**.", extra=None):
    return click(bid, text, RUN, "Blue Run query button, top right.", extra_req=extra)


def addq(bid, text="Add a second query row yourself, then paste the next query into it."):
    return md(bid, text)


def inspector(bid="open-inspector", text="Open **Query inspector** and read **Stats**."):
    return md(bid, text)


def md(bid, content):
    return {"type": "markdown", "id": bid, "content": content}


def callout(bid, title, content):
    return {"type": "callout", "id": bid, "title": title, "content": content}


def section(bid, title, blocks, requirements=None):
    b = {"type": "section", "id": bid, "title": title, "autoCollapse": True, "blocks": blocks}
    if requirements:
        b["requirements"] = requirements
    return b


def quiz(qid, question, choices):
    """choices: list of (text, correct, hint) ; ids assigned a,b,c..."""
    out = []
    for i, ch in enumerate(choices):
        text, correct, hint = (ch + (None,))[:3] if len(ch) < 3 else ch
        c = {"id": "abcdef"[i], "text": text, "correct": bool(correct)}
        if hint:
            c["hint"] = hint
        out.append(c)
    assert sum(1 for c in out if c["correct"]) == 1, qid
    return {"type": "quiz", "id": qid, "question": question, "completionMode": "correct-only", "shuffle": True, "choices": out}


def challenge(bid, dash_title, brief_extra=""):
    """is-editor conditional: Add to dashboard from Explore, then check a dashboard with that title exists."""
    return {
        "type": "conditional",
        "id": bid,
        "conditions": ["is-editor"],
        "display": "section",
        "description": "Save the query, if this role can",
        "whenTrueSectionConfig": {"title": "Check my work"},
        "whenFalseSectionConfig": {"title": "Saving dashboards"},
        "whenTrue": [
            md(
                bid + "-add",
                f"Save the last query to a new dashboard named **{dash_title}**. The button is in the Explore toolbar. The title has to match, aside from case.{brief_extra}",
            ),
            {
                "type": "challenge",
                "id": bid + "-check",
                "mode": "standard",
                "title": "Dashboard exists",
                "brief": f"Check my work looks for a dashboard titled **{dash_title}**. Save it from Explore, then check. The search is the dashboard title, not the query text.",
                "successCriteria": f"has-dashboard-named:{dash_title}",
                "hintLevels": [
                    {"text": "The button is in the Explore toolbar, not the query row."},
                    {"text": f"The title has to be exactly {dash_title}. Case does not matter."},
                ],
                "failureMessage": "No dashboard with that title yet. Save from Explore, then check again.",
                "skippable": True,
            },
        ],
        "whenFalse": [md(bid + "-viewer", "This org role cannot create dashboards (`is-editor` is editor or higher). The check-my-work step is hidden. The quizzes above still count.")],
    }


def dash_challenge(bid, dash_title, brief):
    return {
        "type": "challenge",
        "id": bid,
        "mode": "standard",
        "title": "Dashboard exists",
        "brief": brief,
        "successCriteria": f"has-dashboard-named:{dash_title}",
        "hintLevels": [
            {"text": "Save is the blue button top right while the dashboard is in edit mode."},
            {"text": f"The title has to be exactly {dash_title}. Case does not matter."},
        ],
        "failureMessage": "No dashboard with that title yet. Save, then check again.",
        "skippable": True,
    }


def editor_gate(bid, when_true, when_false_text, title_true="Try it on your stack", title_false="Try it on your stack (read only)"):
    return {
        "type": "conditional",
        "id": bid,
        "conditions": ["is-editor"],
        "display": "section",
        "description": "Editor or Admin needed",
        "whenTrueSectionConfig": {"title": title_true},
        "whenFalseSectionConfig": {"title": title_false},
        "whenTrue": when_true,
        "whenFalse": [md(bid + "-viewer", when_false_text)],
    }


# --- new-dashboard try-it building blocks ---

def new_dash(bid="open-new-dash", text=None):
    return nav(
        bid,
        text or "Open a **new, empty dashboard**. **Do it** takes you there. Everything in this section happens inside it.",
        "/dashboard/new?orgId=1",
        "New dashboard.",
        verify="on-page:/dashboard/new",
    )


def add_viz(bid="add-viz", text="Click **Add visualization**. The panel editor opens with a datasource picker."):
    """Unused by the learning paths. Do not chain this into a try-it. Learners find Add visualization themselves."""
    return textbtn(bid, text, "Add visualization", "Empty dashboard, centre button.", requirements=ON_DASH, hint="If the dashboard already has a panel, use the + button in the top toolbar and pick Visualization.")


def pick_prom(bid="pick-prom", text="Pick the **Prometheus** datasource. **Show me** points at the picker."):
    return highlight(bid, text, DSPICK, "Datasource picker.", requirements=ON_DASH)


def code_mode(bid="code-mode", text="Switch the query row to **Code**. The panel editor opens in Builder, and Builder writes the query for you."):
    return highlight(bid, text, TOGGLE, "Builder / Code toggle on the query row.", requirements=ON_DASH + ["min-version:10.4.0"])


def panel_query(bid, text, code, tooltip, hint=None, lang="promql"):
    return {
        "type": "interactive", "id": bid, "action": "highlight", "showMe": True, "doIt": False,
        "reftarget": PROM_FIELD if lang == "promql" else LOKI_FIELD, "requirements": ON_DASH, "skippable": True,
        "content": text + fence(code, lang), "tooltip": tooltip, **({"hint": hint} if hint else {}),
    }


def save_dash(bid, title, text=None):
    """Tell them to save. Do not click Save or point at the title field."""
    note = text or f"Save the dashboard as **{title}**. The check looks for that exact title."
    if text and text.startswith("Click **Save"):
        note = f"Save the dashboard as **{title}**. The check looks for that exact title."
        if "variable" in text.lower():
            note += " Save the current variable values if you want this selection to be the default."
        if "finished" in text.lower():
            note += " The customization path builds on this dashboard."
    return [md(bid + "-save", note)]


# --- validation ---
ACTIONS = {"highlight", "button", "formfill", "navigate", "hover", "noop", "popout"}
TYPES = {"markdown", "divider", "html", "image", "video", "callout", "interactive", "multistep", "guided", "quiz", "input", "terminal", "terminal-connect", "challenge", "code-block", "grot-guide", "snippet-ref", "section", "collapsible", "assistant", "conditional"}
REQ_RE = re.compile(r"^(on-page:/\S+|has-datasource:\S+|datasource-configured:\S+|has-plugin:\S+|has-permission:\S+|has-role:\S+|min-version:\d+\.\d+\.\d+|section-completed:\S+|has-feature:\S+|in-environment:\S+|has-dashboard-named:.+|var-\S+:\S+|renderer:\S+|coda-exit-zero:\S+|exists-reftarget|navmenu-open|is-admin|is-editor|is-logged-in|dashboard-exists|has-datasources|form-valid|is-terminal-active)$")


def validate(blocks, where, ids=None):
    ids = set() if ids is None else ids
    errs = []
    for b in blocks:
        t = b.get("type")
        if t not in TYPES:
            errs.append(f"{where}: bad type {t}")
        bid = b.get("id")
        if bid:
            if bid in ids:
                errs.append(f"{where}: duplicate id {bid}")
            ids.add(bid)
        if t == "interactive":
            if b.get("action") not in ACTIONS:
                errs.append(f"{where}: bad action {b.get('action')} in {bid}")
            if b.get("action") != "noop" and not b.get("reftarget"):
                errs.append(f"{where}: no reftarget in {bid}")
        for r in (b.get("requirements") or []) + (b.get("conditions") or []) + ([b["verify"]] if b.get("verify") else []) + (b.get("objectives") or []):
            if not REQ_RE.match(r):
                errs.append(f"{where}: bad requirement {r!r} in {bid}")
        if t == "quiz":
            if sum(1 for c in b["choices"] if c.get("correct")) != 1:
                errs.append(f"{where}: quiz {bid} needs exactly one correct")
        if t == "challenge" and not REQ_RE.match(b.get("successCriteria", "")):
            errs.append(f"{where}: bad successCriteria in {bid}")
        for key in ("blocks", "whenTrue", "whenFalse"):
            if b.get(key):
                errs += validate(b[key], where, ids)
        for st in b.get("steps") or []:
            for r in st.get("requirements") or []:
                if not REQ_RE.match(r):
                    errs.append(f"{where}: bad step requirement {r!r}")
    return errs
