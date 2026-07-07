# agent-tools install guides v0.1.1 OS platform plan

## Goal

Make the public install flow explicit and safe across macOS, Linux, native
Windows, and WSL.

The v0.1.0 install guide established the copy-the-whole-Markdown flow. This
update keeps that flow but removes the hidden Unix-only assumption in target
paths, cache paths, dry-run reporting, troubleshooting, and validation.

Initial scope remains `slide-creator` only.

## Implementation

Update the install catalog so every supported agent uses
`supported_agents.target_paths` with `macos`, `linux`, and `windows` entries.
Generated install docs must render those paths as a table and tell the
installing agent to detect macOS, Linux, native Windows, or WSL before choosing
a path.

Update common policy and target docs to state:

- native Windows paths use `%USERPROFILE%` or PowerShell `$env:USERPROFILE`
- macOS and Linux paths use `~` and hidden dot directories
- WSL Linux paths and native Windows paths are not interchangeable
- the installer should not bridge through `/mnt/c/` without user confirmation
- PowerShell, Command Prompt, and Git Bash require different command syntax
- symlinks, junctions, package managers, and execution policy changes need
  separate consent

Update troubleshooting for Windows path failures, PowerShell execution policy,
WSL/native Windows confusion, path separators, case sensitivity, and
OS-specific package manager consent.

Update the generator and checker so OS-aware paths are required and generated
docs drift fails CI. Manifest hashing must normalize UTF-8 text file line
endings to LF so Windows checkout behavior does not create false drift, while
leaving binary files unchanged.

## Release Model

Prepare docs for `v0.1.1`. The standard install reference should be the fixed
`v0.1.1` release, not `main`.

After merge, create a tag and GitHub release for `v0.1.1`. Use a signed tag if
available. If signing is unavailable, use an annotated tag plus commit SHA and
release manifest.

## Validation

Run:

```bash
python scripts/generate_install_docs.py --check
python scripts/check_install_docs.py
python -m py_compile scripts/generate_install_docs.py scripts/check_install_docs.py
```

Also run the same checks under Python 3.12, because CI uses Python 3.12.

Run a secret/local path scan over generated install docs and `skills/slide-creator`
for:

- `/Users/`
- `GoogleDrive`
- `gmail`
- private key markers
- token-like strings

Run `git diff --check` and verify the generated manifest is deterministic.

## Out Of Scope

- changing the `slide-creator` runtime behavior
- installing optional runtime dependencies automatically
- adding MCP or bundle install flows
- changing agent config files
