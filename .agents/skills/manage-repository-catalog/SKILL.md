---
name: manage-repository-catalog
description: Create, inspect, reconcile, and update the authoritative Repository Catalog at `.workbench/repositories.yaml`. Use when asked to discover or sync direct child directories under `repos/`, create a missing catalog, add or remove workspace repositories, resolve catalog drift, or update stable `repo_id` identities or checkout paths. Catalog membership does not grant AI access, require codebase indexing, or describe integrations. Do not use merely to regenerate `.code-workspace` from an unchanged catalog.
---

# Manage Repository Catalog

Maintain the canonical inventory of repositories known to the project workspace. Keep access policy, indexing configuration, integrations, and generated knowledge outside this catalog.

## Terminology

- Call each direct child directory under `repos/` a **workspace repository** or **repo**. Expect it to be a Git checkout, but catalog a non-Git directory too and emit a warning.
- Call a repo listed in `.workbench/repositories.yaml` a **cataloged repository**.
- Do not confuse a workspace repository with repository-pattern classes or data repositories inside source code.

## Schema

Use only schema version 1:

```yaml
schema_version: 1

repositories:
  - repo_id: repo_customer_portal
    path: repos/customer-portal
```

- Set `repo_id` to a stable, unique identifier matching `repo_<snake_case_name>`.
- Set `path` to a unique workspace-relative direct child of `repos/`.
- Do not add access, indexing, tool, remote, ownership, description, component, or integration fields to schema version 1.
- Represent a valid empty catalog as `repositories: []`.

## Catalog semantics

- Treat `repos/` as containing only repositories that belong to this project workspace. Every direct child directory must have a catalog entry.
- Include supporting repositories such as test environments, fixtures, documentation, skills, extensions, or automation when they belong to the project workspace.
- Do not infer read, write, execute, indexing, or runner permissions from catalog membership.
- Do not omit a project repository merely because codebase knowledge does not need to index it.
- Allow a cataloged path to be absent on the current machine; this means the checkout is missing, not that the catalog entry is stale.

## Workflow

1. Read the root instructions and the existing catalog, if present.
2. Discover all direct child directories of `repos/`. Record whether each has a `.git` file or directory; do not silently omit a non-Git directory.
3. Compare discovered paths with cataloged entries. Do not inspect or modify files inside repositories merely to catalog them.
4. When creating or syncing the catalog, add every uncataloged direct child. Derive a default identity by converting the directory name to lowercase snake case and prefixing `repo_`; ask only when the result is invalid, ambiguous, or collides with an existing identity.
5. Preserve catalog entries whose checkout is missing on the current machine. Remove or rename an entry only when the user requests that change explicitly.
6. Write schema version 1 while preserving unaffected entries and their order. Append newly discovered entries in deterministic path order unless the user specifies an order.
7. Validate the workspace-owned contract, identities, paths, uniqueness, direct-child scope, complete direct-child coverage, and Git-checkout warnings with `python3 tooling/validate_repository_catalog.py`.
8. After the catalog is valid, use `$generate-vscode-workspace` to regenerate and check `.code-workspace`.

## Constraints

- Never leave a discovered direct child directory uncataloged after a requested create, sync, or reconciliation.
- Never create, edit, delete, or rename files inside `repos/*`.
- Never initialize Git in a candidate directory as part of cataloging.
- Never remove a catalog entry solely because its checkout is absent.
- Keep derived knowledge and policy in separate files that reference `repo_id`.
- Do not make a consumer-specific tool the owner of Catalog validation; use the workspace-level validator.
