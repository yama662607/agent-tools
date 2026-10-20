# slide-creator v0.3.0 release plan

## Goal

Release the slide-creator updates made after v0.2.0 as one pinned version, so
that installs from the install guides get the current behaviour.

## Scope

- New-poster workflow (`references/poster.md` §0) and SKILL.md routing for posters.
- Existing-deck quality pass (`references/improving-existing-decks.md`), for
  decks a user built by hand and wants refined without layout changes.
- `capture_edits.py` reports run font-size changes (including table cells).
  Before this, font-only edits were reported as "No differences".
- Poster, HTML storyboard, visual exhibit, text readability, and layout rule
  references and scripts that were synced after v0.2.0.

## Verification

```bash
python scripts/generate_install_docs.py --check
python scripts/check_install_docs.py
python -m py_compile scripts/*.py skills/slide-creator/scripts/*.py
python -m unittest discover -s tests -p "test_*.py"
uv run tests/runtime_smoke.py
```

Also: a clean clone of `main` installed into a temporary home directory, with
`verify_deck.py` and `ingest_deck.py` run from the installed copy.

## Release

Merge through a pull request, create the annotated `v0.3.0` tag on the merge
commit, and publish a GitHub release that points at the tag.
