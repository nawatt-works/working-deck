---
name: generate-vscode-workspace
description: Generate and validate this workspace's committed VS Code multi-root `.code-workspace` file from `.workbench/repositories.yaml`. Use when repositories are added, removed, renamed, or moved; when the VS Code workspace is missing or stale; or when asked to synchronize or check the repository registry and editor workspace.
---

# Generate VS Code Workspace

Generate the editor workspace with the root-owned script. Keep the repository registry as the source of truth and never place workspace artifacts in external repositories.

## Workflow

1. Read the applicable root instructions and `.workbench/repositories.yaml`.
2. Run `python3 tooling/generate_vscode_workspace.py` from the workspace root.
3. Inspect the `.code-workspace` diff. Confirm every generated folder corresponds to one registry entry and no unrelated settings changed.
4. Run `python3 tooling/generate_vscode_workspace.py --check`.
5. Report invalid, duplicate, missing, absolute, or non-`repos/` paths without modifying external repositories.

## Constraints

- Treat `.workbench/repositories.yaml` as canonical and `.code-workspace` as generated.
- Preserve manifest order in the generated folder list.
- Do not edit, create, delete, or rename files under `repos/*`.
- Do not add AI harness configuration to external repositories.
- Do not hand-edit `.code-workspace` to resolve drift; update the registry or generator and regenerate it.
