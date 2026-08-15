---
name: generate-vscode-workspace
description: Generate and validate this workspace's committed VS Code multi-root `.code-workspace` projection from the existing `.workbench/repositories.yaml`. Use after the selective repository registry changes, or when `.code-workspace` is missing, stale, or needs verification. Do not use to decide which repos should be registered or to create or edit the registry.
---

# Generate VS Code Workspace

Generate the editor projection from the existing repository registry with the root-owned script.

## Workflow

1. Read the applicable root instructions and `.workbench/repositories.yaml`.
2. If the registry is missing or needs membership changes, stop and use `$manage-repository-registry` instead.
3. Run `python3 tooling/generate_vscode_workspace.py` from the workspace root.
4. Inspect the `.code-workspace` diff. Confirm it contains the root workspace plus exactly the registered repositories in manifest order.
5. Run `python3 tooling/generate_vscode_workspace.py --check`.
6. Report invalid, duplicate, missing, non-Git, absolute, nested, or non-`repos/` paths without modifying external repositories.

## Constraints

- Treat `.workbench/repositories.yaml` as canonical and `.code-workspace` as generated.
- Do not create or edit the registry with this skill.
- Keep unregistered repos out of `.code-workspace`.
- Preserve manifest order in the generated folder list.
- Do not edit, create, delete, or rename files under `repos/*`.
- Do not add AI harness configuration to external repositories.
- Do not hand-edit `.code-workspace` to resolve drift; update the generator and regenerate it.
