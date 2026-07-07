# Target: Antigravity

Use this target only when the user explicitly chooses Antigravity.

Default skill paths:

| OS | Default path |
|---|---|
| macOS | `~/.gemini/antigravity-cli/skills/slide-creator` |
| Linux | `~/.gemini/antigravity-cli/skills/slide-creator` |
| Windows | `%USERPROFILE%\.gemini\antigravity-cli\skills\slide-creator` |

Installation is a directory copy. If the directory already exists and was not
created by this installer, stop and ask the user before replacing it.

Antigravity skill support can vary by local setup. If the default path does not
exist and the user cannot confirm Antigravity's current skill directory, stop
and ask instead of guessing.

If Antigravity runs inside WSL, use the Linux path inside WSL. If Antigravity
runs as a native Windows app, use the Windows path. Do not bridge between the
two without explicit user confirmation.
