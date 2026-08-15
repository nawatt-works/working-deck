---
name: generate-vscode-workspace
description: Generate and validate this workspace's committed VS Code multi-root `.code-workspace` projection from the existing Repository Catalog at `.workbench/repositories.yaml`. Use after the catalog changes, or when `.code-workspace` is missing, stale, or needs verification. Do not use to decide project catalog membership or to create or edit the catalog.
---

# Generate VS Code Workspace

Generate the editor projection from the existing Repository Catalog with the root-owned script. This projection exists so VS Code opened at the root can discover repositories hidden from the root Git repository by ignore rules.

## Workflow

1. Read the applicable root instructions and `.workbench/repositories.yaml`.
2. If the catalog is missing, needs membership changes, or omits a direct child directory under `repos/`, stop and use `$manage-repository-catalog` instead.
3. Run `python3 tooling/validate_repository_catalog.py` from the workspace root.
4. Run `python3 tooling/generate_vscode_workspace.py`.
5. Inspect the `.code-workspace` diff. Confirm it contains the root workspace plus exactly the cataloged repositories in catalog order.
6. Run `python3 tooling/generate_vscode_workspace.py --check`.
7. Report invalid, duplicate, uncataloged, missing, non-Git, absolute, nested, or non-`repos/` paths without modifying external repositories.

## Constraints

- Treat `.workbench/repositories.yaml` as canonical and `.code-workspace` as a derived editor configuration.
- Treat the workspace-level Repository Catalog contract and validator as canonical; this skill is only a consumer.
- Do not create or edit the catalog with this skill.
- Include every cataloged repository; do not filter folders based on AI access or indexing policy.
- Treat an uncataloged direct child under `repos/` as catalog drift that must be resolved before generation succeeds.
- Preserve catalog order in the generated folder list.
- Do not edit, create, delete, or rename files under `repos/*`.
- Do not add AI harness configuration to external repositories.
- Do not hand-edit `.code-workspace` to resolve drift; update the generator and regenerate it.
