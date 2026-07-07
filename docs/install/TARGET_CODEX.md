# Target: Codex

Use this target only when the user explicitly chooses Codex.

Default skill paths:

| OS | Default path |
|---|---|
| macOS | `~/.codex/skills/slide-creator` |
| Linux | `~/.codex/skills/slide-creator` |
| Windows | `%USERPROFILE%\.codex\skills\slide-creator` |

Installation is a directory copy. If the directory already exists and was not
created by this installer, stop and ask the user before replacing it.

This target does not require an MCP config change for `slide-creator`.
Restarting the agent session may be required before a newly installed skill is
discovered.

If Codex runs inside WSL, use the Linux path inside WSL. If Codex runs as a
native Windows app, use the Windows path. Do not bridge between the two without
explicit user confirmation.
