"""Static QA for generated Pathfinder workshop packages.

Usage:
  python check.py <packages-root>
  python check.py --self-test

validate() does not catch a Show me that draws nothing. This script catches the
static half of that miss: a bare reftarget, and an on-page path that is only a
prefix of a deeper page in the same guide. The click sample in SKILL.md is
still required before publishing.
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

SELECTOR = (
    "[",
    "#",
    ".",
    "a[",
    "a:",
    "button",
    "input",
    "textarea",
    "th",
    "h1",
    "h3",
    "span",
)
# These are prefix matches on purpose. A shorter app route is not.
ALLOWED_PREFIX = {"/d", "/explore", "/dashboard/new", "/dashboards"}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def walk(blocks: list):
    for block in blocks or []:
        if not isinstance(block, dict):
            continue
        yield block
        for key in ("blocks", "whenTrue", "whenFalse"):
            nested = block.get(key)
            if isinstance(nested, list):
                yield from walk(nested)


def looks_like_selector(target: str) -> bool:
    head = target.lstrip()
    return head.startswith(SELECTOR)


def on_page_paths(block: dict) -> list[str]:
    found = []
    for token in list(block.get("requirements") or []) + ([block["verify"]] if block.get("verify") else []):
        if isinstance(token, str) and token.startswith("on-page:"):
            found.append(token[len("on-page:") :])
    return found


def strict_prefix(short: str, long: str) -> bool:
    if short in ALLOWED_PREFIX or short == long:
        return False
    base = short.rstrip("/")
    return long.startswith(base + "/")


def package_dirs(root: Path) -> list[Path]:
    if (root / "manifest.json").is_file():
        return [root]
    return sorted(path for path in root.iterdir() if (path / "manifest.json").is_file())


def check_guide(directory: Path, manifest: dict, content: dict) -> list[str]:
    errors = []
    where = directory.name
    if manifest.get("id") != content.get("id"):
        errors.append(f"{where}: manifest id {manifest.get('id')!r} != content id {content.get('id')!r}")
    blocks = list(walk(content.get("blocks") or []))
    ids = [block.get("id") for block in blocks if block.get("id")]
    dupes = sorted({item for item in ids if ids.count(item) > 1})
    if dupes:
        errors.append(f"{where}: duplicate block id {dupes}")
    step_ids = []
    for block in blocks:
        for step in block.get("steps") or []:
            if isinstance(step, dict) and step.get("id"):
                step_ids.append(step["id"])
    step_dupes = sorted({item for item in step_ids if step_ids.count(item) > 1})
    if step_dupes:
        errors.append(f"{where}: duplicate step id {step_dupes}")

    quizzes = [block for block in blocks if block.get("type") == "quiz"]
    if len(quizzes) != 1:
        errors.append(f"{where}: expected one quiz, found {len(quizzes)}")
    for block in blocks:
        if block.get("type") == "code-block":
            errors.append(f"{where}: code-block {block.get('id')}")
        if block.get("action") == "noop" or block.get("type") == "noop":
            errors.append(f"{where}: noop {block.get('id')}")

    section_ids = {block.get("id") for block in blocks if block.get("type") == "section"}
    for block in blocks:
        if block.get("type") == "guided" and block.get("id") in section_ids:
            errors.append(
                f"{where}: guided id {block.get('id')!r} is also a section id. "
                "Assistant looks up the guided id and misses a section."
            )
        for step in block.get("steps") or []:
            if not isinstance(step, dict):
                continue
            target = step.get("reftarget") or ""
            if not looks_like_selector(target):
                errors.append(
                    f"{where}: bare target {target!r} in {step.get('id')}. "
                    "Use a selector, or button:contains('Label') for a real button."
                )

    paths = []
    for block in blocks:
        for path in on_page_paths(block):
            paths.append((block.get("id"), path))
        for step in block.get("steps") or []:
            if isinstance(step, dict):
                for path in on_page_paths(step):
                    paths.append((step.get("id"), path))
    seen = set()
    for left_id, left in paths:
        for right_id, right in paths:
            pair = tuple(sorted((left, right)))
            if pair in seen or not strict_prefix(left, right):
                continue
            seen.add(pair)
            errors.append(
                f"{where}: on-page:{left} ({left_id}) also matches on-page:{right} ({right_id}). "
                "A short path completes on the deeper page. Omit verify on the short navigate."
            )

    for block in blocks:
        if block.get("type") != "section":
            continue
        nested = list(walk(block.get("blocks") or []))
        if not any(item.get("type") == "guided" for item in nested):
            continue
        if not any(item.get("type") == "callout" and item.get("title") == "Answer to compare" for item in nested):
            errors.append(f"{where}: section {block.get('id')} has a guided question and no Answer to compare callout")
    return errors


def check_root(root: Path) -> list[str]:
    if not root.is_dir():
        return [f"missing packages directory {root}"]
    packages = package_dirs(root)
    if not packages:
        return [f"no manifest.json under {root}"]
    errors = []
    for package in packages:
        manifest = load(package / "manifest.json")
        content_path = package / "content.json"
        if not content_path.is_file():
            errors.append(f"{package.name}: missing content.json")
            continue
        if manifest.get("type") == "guide":
            errors.extend(check_guide(package, manifest, load(content_path)))
        for milestone in manifest.get("milestones") or []:
            guide_dir = package / milestone
            if not (guide_dir / "manifest.json").is_file():
                errors.append(f"{package.name}: missing milestone {milestone}")
                continue
            errors.extend(check_guide(guide_dir, load(guide_dir / "manifest.json"), load(guide_dir / "content.json")))
    return errors


def guide(blocks: list) -> dict:
    return {
        "schemaVersion": "1.1.0",
        "id": "sample-guide",
        "type": "guide",
        "blocks": blocks,
    }


def write_guide(directory: Path, blocks: list) -> None:
    directory.mkdir(parents=True)
    manifest = {"schemaVersion": "1.1.0", "id": "sample-guide", "type": "guide", "milestones": []}
    (directory / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (directory / "content.json").write_text(json.dumps(guide(blocks)), encoding="utf-8")


def good_blocks() -> list:
    return [
        {
            "id": "sample-open",
            "type": "interactive",
            "action": "navigate",
            "reftarget": "/a/example-app/services/service/demo",
            "verify": "on-page:/a/example-app/services/service/demo",
            "content": "Open the service.",
        },
        {
            "id": "sample-q-section",
            "type": "section",
            "title": "1. Error",
            "blocks": [
                {
                    "id": "sample-q",
                    "type": "guided",
                    "content": "Question",
                    "steps": [
                        {
                            "id": "sample-q-step-1",
                            "action": "highlight",
                            "reftarget": "a[href$='/traces']",
                            "description": "Open Traces.",
                            "requirements": ["on-page:/a/example-app/services/service/demo", "exists-reftarget"],
                        }
                    ],
                },
                {"id": "sample-q-answer", "type": "callout", "title": "Answer to compare", "content": "The live error."},
            ],
        },
        {
            "id": "sample-quiz",
            "type": "quiz",
            "question": "What next?",
            "choices": [{"id": "a", "text": "Follow the failing hop.", "correct": True}],
        },
    ]


def self_test() -> None:
    root = Path(tempfile.mkdtemp(prefix="pathfinder-check-"))
    try:
        good = root / "good"
        write_guide(good, good_blocks())
        if check_root(good):
            raise SystemExit("self-test: good package failed: " + "; ".join(check_root(good)))

        bare = root / "bare"
        blocks = good_blocks()
        blocks[1]["blocks"][0]["steps"][0]["reftarget"] = "Traces"
        write_guide(bare, blocks)
        if not any("bare target" in item for item in check_root(bare)):
            raise SystemExit("self-test: bare target was accepted")

        prefix = root / "prefix"
        blocks = good_blocks()
        blocks[0]["verify"] = "on-page:/a/example-app/services"
        blocks[0]["reftarget"] = "/a/example-app/services"
        write_guide(prefix, blocks)
        if not any("also matches" in item for item in check_root(prefix)):
            raise SystemExit("self-test: short on-page was accepted")

        same = root / "same-id"
        blocks = good_blocks()
        blocks[1]["id"] = "sample-q"
        write_guide(same, blocks)
        if not any("also a section id" in item for item in check_root(same)):
            raise SystemExit("self-test: shared section id was accepted")
    finally:
        shutil.rmtree(root)
    print("self-test ok")


def main() -> None:
    if len(sys.argv) == 2 and sys.argv[1] == "--self-test":
        self_test()
        return
    if len(sys.argv) != 2:
        sys.exit("usage: python check.py <packages-root> | python check.py --self-test")
    errors = check_root(Path(sys.argv[1]))
    if errors:
        for error in errors:
            print(error)
        sys.exit(1)
    print(f"checked {sys.argv[1]}")


if __name__ == "__main__":
    main()
