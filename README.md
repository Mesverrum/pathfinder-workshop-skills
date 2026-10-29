# Pathfinder workshop skills

Skills for turning a Grafana workshop into [Pathfinder](https://github.com/grafana/grafana-pathfinder-app) learning paths. Anyone who can edit a Grafana stack can use them. No customer names, stack hosts, or tokens belong in this repo or in a generated package.

## Skills

| Folder | Role |
|---|---|
| `skills/workshop-to-pathfinder` | Convert a lab guide into paths, milestones, and Show me / Do it steps |
| `skills/pathfinder-author` | Block JSON, `validate()`, Explore selectors |
| `skills/pathfinder-publish` | Dry-run upload to the Grafana HTTP API, then apply only after a person confirms |

## Use them in Claude or Cursor

Copy the three folders into the agent's skills directory. Keep the folder names.

```
.claude/skills/pathfinder-author/
.claude/skills/pathfinder-publish/
.claude/skills/workshop-to-pathfinder/
```

Cursor uses `.cursor/skills/` with the same three names.

Point the agent at a workshop source and tell it to follow `workshop-to-pathfinder`. It should write a `build.py`, call `validate()`, and stop at a publish dry run until you confirm.

## Publish

```
GRAFANA_URL=https://your-stack.grafana.net
GRAFANA_TOKEN=<service account token with Editor rights>
```

Do not commit `GRAFANA_TOKEN`. The uploader reads it from the environment and does not print it.

## What a conversion produces

One learning path per timed lab. Sections of that lab are milestones. Questions are collapsing sections. Open the path id, not a milestone id:

```
https://<stack>/a/grafana-pathfinder-app?doc=api:<path-id>
```
