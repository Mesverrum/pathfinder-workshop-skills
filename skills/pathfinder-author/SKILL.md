---
name: pathfinder-author
description: >-
  Authors Grafana Pathfinder InteractiveGuide content: try-it steps, quizzes,
  challenges, conditionals, and selectors. Use when writing or editing a
  learning path, learning journey, milestone, interactive guide, Show me / Do it
  step, or Pathfinder content.json. Covers the copy-the-query pattern (blank
  Explore, hand-typed queries, no code-block).
---

# Pathfinder author

Write guide JSON with `scripts/pf.py`. Do not hand-assemble block dicts, and do not invent selectors. Publish with the `pathfinder-publish` skill.

Install this skill beside `pathfinder-publish`.

## Settled pattern

This is the shape that was clicked through on a Grafana Cloud stack (Pathfinder 2.18). Keep it unless the user asks for something else.

1. **Do it** on a `navigate` step opens a blank page. Explore URLs carry an empty query in Code mode (TraceQL tab for Tempo). `verify` is `on-page:/explore` (or `/dashboard/new`, `/d`, `/a/...`) so the step stays open until that page is actually showing.
2. The learner **types every query**. The step is `highlight` with `showMe: true` and `doIt: false`, `reftarget` on the query field, query in a fenced block in `content`. Two navigate steps in one guide need distinct ids (`open-explore-prom`, `open-explore-loki`).
3. Run query, Add query, Query inspector, Save, Share, Export are `button` steps with `showMe` and `doIt`. A button with no `grafana:` selector is targeted by its visible label, plus `exists-reftarget` and `skippable: true`.
4. Wrap the steps in a `section` titled "Try it on your stack" with `autoCollapse: true`. Steps that write (dashboard, recording rule, datasource correlation) go inside an `is-editor` or `is-admin` `conditional` with `display: "section"`. Viewers get the queries as markdown. The quizzes still count.
5. One `quiz` has exactly one correct choice, `shuffle: true`, `completionMode: "correct-only"`. A `challenge` `successCriteria` is a requirement token, usually `has-dashboard-named:<title>`.

## Do not

- `code-block` (it types into Monaco). A query inside the Explore URL. `openGuide` (it did not open the next milestone on 2.18.3).
- Time-picker `formfill`. Popout dock and undock.
- `input` steps whose saved value is never read again.
- `dataCheckQuery` / `dataCheckTimeFrom` / `dataCheckTimeTo` / `dataCheckBlocking`. The stack API drops them on save.
- `action: "noop"`. A requirement string that is not in the validator in `scripts/pf.py`.
- Launch instructions that use a milestone id. The milestone bar, cover, and next/prev come from the **path** id: `/a/grafana-pathfinder-app?doc=api%3A<path-id>`.

## Helpers

`navigate`, `paste`, `click`, `textbtn`, `run`, `addq`, `inspector`, `quiz`, `challenge`, `section`, `callout`, `md`, `editor_gate`, `new_dash`, `save_dash`. Call `validate(blocks, where)` before writing JSON. It checks types, actions, unique ids, requirement grammar, one correct quiz answer, and challenge criteria.

Datasource UIDs at the top of `scripts/pf.py` (`grafanacloud-prom`, `grafanacloud-logs`, `grafanacloud-traces`) are the usual Grafana Cloud names. Confirm them on the target stack (`GET /api/datasources`) before reusing them. A self-managed Grafana stack will have different uids.

## Ground the queries

Before putting a metric, label, or log line in a step, query the target stack in Explore. If the stack has no data for that signal, say so in a `callout` and give a stand-in query. Do not leave a step that fails with an empty panel and no explanation.

Selectors that have not been click-tested: Loki `grafana:components.QueryField.container`, Tempo `grafana:components.CodeEditor.container`, dashboard save / share / export selectors, and visible-text buttons (`Add visualization`, `Back to dashboard`). If a Show me misses, check `@grafana/e2e-selectors` at the stack's Grafana version. Loki lives in `grafana/grafana-loki-datasource`, Tempo in `grafana/grafana-tempo-datasource`.

## Further reading

Block types, the requirement tokens this validator accepts, and the selector list: [reference.md](reference.md).
