---
name: workshop-to-pathfinder
description: >-
  Converts a Grafana workshop, breakout, or lab guide into Pathfinder learning
  paths. Use when turning workshop questions into Show me / Do it steps, or any
  click-through that should become InteractiveGuide
  packages. Follow pathfinder-author for block JSON and pathfinder-publish for
  the upload. Run the static check, then the click sample, before publishing.
  Do not hand-write content.json.
---

# Workshop to Pathfinder

Convert a workshop into Pathfinder packages. `pathfinder-author` owns block JSON, selectors for Explore, and `validate()`. `pathfinder-publish` owns the upload. This skill owns the workshop shape and the click-target rules those two skills do not state.

Write a `build.py`. Generate `packages/`. Run `validate()`. Do not hand-edit the JSON.

## Shape

| Workshop | Pathfinder |
|---|---|
| One timed lab (about 20 minutes) | One learning path |
| A section of that lab | One milestone, in lab order |
| One question inside the section | One auto-collapsing section |
| The "what should you conclude" check | One quiz at the end of the milestone |

Do not merge every lab into a single path. Do not make every question its own guide. If the source has no time boxes, ask how to split before generating.

Keep fixture names that are the workshop contract (`ecommerce`, a demo service, a namespace). Do not put a customer name, a stack host, or a token in the package.

## One question

A question section contains, in order:

1. An `interactive` navigate step whose `reftarget` is the fixture path for this question. The learner can start here without finishing the previous question.
2. A `guided` block. The Assistant "Fix this" patch looks up `multistep` or `guided` by the author id. A `section` with that id fails with `No multistep/guided container found`.
3. A callout titled `Answer to compare`. Live numbers, pod names, image tags, and Assistant sentences go here. They are not completion checks.

The section id ends in `-section`. The guided id is `{guide}-{slug}` and is the id Assistant can patch. Steps inside the guided block use the publisher step allowlist only: `action`, `description`, `id`, `reftarget`, `requirements`, `skippable`, `tooltip`, plus `targetstate` / `targetvalue` / `formHint` / `validateInput` when a step actually needs them. Do not put `content`, `showMe`, or `doIt` on a guided step.

`section()` from `pf.py` sets `autoCollapse: true`. "Do Section (1 step)" counting the whole guided block as one step is expected. The clicks are inside it.

End the milestone with one `quiz()`. Exactly one correct choice. Ask what the evidence means or what to do next. Do not ask for a count that moves.

Optional questions stay `skippable`. Steps that create or save something go behind an `is-editor` conditional. Viewers get the question and the expected result as markdown.

## Clicks

| The learner does this | `action` | `reftarget` |
|---|---|---|
| Open a known page | `navigate` on the interactive block before the guided steps | The path, such as `/a/grafana-k8s-app/navigation/workload` |
| Click a card, tab, table link, or panel | `highlight` | CSS, `data-testid`, `data-cy`, or `a[href...]` |
| Click a real button whose label you have seen | `highlight` | `button:contains('Exact label')` |
| Read a value or type into a field | `highlight` with the field or panel as the target | The learner types. Show me only points. |

A bare word such as `Traces` or `Services` is a button-label lookup. On a page with no button of that name, Show me draws nothing and the guided modal waits on Skip. `exists-reftarget` plus `skippable: true` does not auto-advance.

`:contains('Traces')` with no element type can match the guide's own step text. Scope it: `a[href$='/traces']`, `[role='tab']`, `[data-testid='...']`, `[data-cy='...']`, `th`, `h3`, or `button:contains('Exact label')`.

`on-page` is a prefix check. `on-page:/a/.../services` also matches `/services/service/...`. Do not use a short path as `verify` when the learner must be on the list rather than a child page. Omit `verify` on that navigate and let Do it open the exact URL.

Tell the learner to set Last 1 hour or Last 24 hours in the step text. Do not use a time-picker `formfill`.

A link href must not also match a longer fixture name. `a[href$='ecommerce-prod---productcatalogservice']` does not match `productcatalogservice-europe`. Application Observability encodes a `/` in the job as `---`.

## Selectors

Do not invent a hook. Read it from the plugin bundle at the version installed on the target stack, then prefer a click-through.

1. `GET /api/plugins` for the plugin id and version. The UI name and the id can differ. Knowledge Graph is `grafana-asserts-app`. Frontend Observability is `grafana-kowalski-app`.
2. Download `https://plugins-cdn.grafana.net/{id}/{version}/public/plugins/{id}/module.js` and the numbered chunks from the webpack map (`e+".js?_cache="+{id:hash}`).
3. Use a `data-cy` or `data-testid` string you found in a `createElement` call, or a panel title passed to `setTitle` / `title:`. A minified path like `A.b.catalog.foo` is not a CSS selector. Find the string value in the selector map.
4. Dashboard panels on `/d` may use `panel:<title>` (Pathfinder 2.5.0+). App plugins use the header attribute that worked on Grafana 13.3.0: `[data-testid='data-testid Panel header <title>']`. The words `data-testid` are part of the attribute value.

If the root chunk does not contain the control (Assistant's composer did not), say so in the step text and keep the step skippable. Do not coin a test id.

## Do not

- `code-block`. A query inside an Explore URL. `openGuide`. `action: "noop"`.
- `dataCheckQuery`, `dataCheckTimeFrom`, `dataCheckTimeTo`, `dataCheckBlocking`. The API drops them.
- A requirement string that `validate()` in `pathfinder-author/scripts/pf.py` rejects.
- Launch text that uses a milestone id. The bar comes from the path id.
- Publishing from `build.py`. Dry-run `pathfinder-publish` (`upsert_net.py`, no `--apply`). Apply only after the user has seen the plan and confirmed in that turn. Learners need `published`. Drafts stay in the editor library and the path TOC locks them.
- Resetting a learner's progress, or clicking Reset guide, while fixing a selector.
- A customer name, stack host, or token inside the generated package.

## QA

`validate()` can pass while Show me draws nothing. Do not publish on that alone.

Static check, from this skill:

```
python skills/workshop-to-pathfinder/scripts/check.py <packages-root>
```

It fails a bare reftarget (including a plain button label; write `button:contains('Save')`), an `on-page` path that is only a prefix of a deeper page in the same guide, a guided id that is also a section id, a question with no `Answer to compare` callout, and a guide that does not have exactly one quiz. `/d`, `/explore`, `/dashboard/new`, and `/dashboards` are allowed prefixes. Run `python skills/workshop-to-pathfinder/scripts/check.py --self-test` after changing the checker.

Click sample, after the static check and a dry-run upload. A step passes only when Show me outlines the control the sentence names. Skip is a fail. A section that is already green is not a pass. Readback only proves the API kept the fields.

Open the **path** id. Start each sample from that question's own navigate, not from the page the previous question left on screen.

- The first step of every question. This is the wrong-page miss.
- Every target that uses `:contains`, or a name that has a longer twin (`service` versus `service-europe`).
- One step that leaves the app.
- One live number, with the time picker written down. If the question says last 1 hour, the picker has to say last 1 hour or the answer callout is wrong.
- The quiz, from the path id. A milestone id hides the bar.

Log a miss as the guide id, the step id, the URL, the reftarget, and what outlined (nothing, the guide's own sentence, or the wrong twin). Fix `build.py` and regenerate. Do not Reset guide on a stack a learner has already started. Use a second user.

"Do Section (1 step)" is expected. The clicks sit inside the guided block.

## Done

`validate()` reports no errors. `check.py` exits 0. The click sample above was walked, and every miss was fixed in `build.py`. The README lists plugin ids, versions, fixture names, and which hooks were taken from a bundle versus still unconfirmed. The user has seen the dry-run plan. Learners need `published`.

Detail and the block shape: [reference.md](reference.md).
