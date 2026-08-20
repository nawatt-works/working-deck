# Workspace Guidelines

This workspace has two primary areas, `workbench/` and `repos/`. Root-level
files such as `.ignore` and `tooling/` govern and maintain the workspace itself.

## `workbench/` — shared working area

- Holds the information and documents that the user and AI share, but never product source code.
- Examples: plans, specifications, architecture, research, decision records, working notes, and evaluation evidence.
- When work is analysis, planning, research, or supporting documentation that is not yet an output of any repository, store it here.
- Never store anything that grants access to a system — secrets, access tokens, credentials, private keys, session material, or connection strings containing a password. The test: if this leaked, could someone use it to act as a person or reach a system?
- Names or handles of people involved in the work may be stored when they are part of a work record, such as who reviewed or approved something. Keep only what the work needs; do not collect contact details without a reason.
- This area has multiple writers. Read `workbench/README.md` before creating a new file in it.
- Write only inside your own namespace at `workbench/<producer>/`. Files at the root of `workbench/` are shared and require a contract first. When an artifact references a repository, reference it by `repo_id` rather than by path.

## Temporary files

- Use the temporary directory or scratchpad that the harness or the system provides for work-in-progress files such as caches, logs, extracted files, generated samples, and intermediate output.
- This workspace has no central folder for temporary files. Do not create one, and do not leave temporary files inside `workbench/`, `repos/*`, or the workspace root.
- Do not write outside the workspace anywhere other than the harness or system temporary directory, unless the user explicitly allows it.
- Keep each task's files in a meaningful subdirectory so they do not collide and can be reviewed or deleted later.
- Before deleting or overwriting an existing file, confirm it does not belong to the user or to other work.
- When a result becomes a decision, reusable evidence, or a checkpoint worth keeping, summarize or move only what is needed into `workbench/`.
- When a temporary result is something the user must review, always tell them where the file is.
- Never store anything that grants access to a system in temporary files — secrets, access tokens, credentials, private keys, session material, or connection strings containing a password.

## `repos/` — external repositories

- Holds checkouts of the Git repositories that are the real work or that support it, such as backend, frontend, API, consumer, worker, library, infrastructure, documentation, test environment, agent skill, extension, or automation.
- Each first-level directory under `repos/` is normally a Git repository independent of the root workspace, and may be owned by an external person or team.
- A repository under `repos/` may be a single-project repository or a monorepo containing several applications, services, packages, or libraries.
- Never infer a repository's internal structure from the fact that it sits under `repos/`. Always check the target repository's configuration, documentation, and guidance before working in it.
- In this workspace's documents, **workspace repository** or **repo** means a direct child directory under `repos/`, normally a Git checkout. **Cataloged repository** means a repo listed in `workbench/repositories.yaml`.
- The word repository as it appears inside source code — the repository pattern, a data repository, `Repository<T>`, or a class ending in `Repository` — is a concept internal to the work and is neither a workspace repository nor a cataloged repository.
- `workbench/repositories.yaml` is the authoritative Repository Catalog of every repository that belongs to this project workspace.
- `repos/` must contain only workspace repositories, so every direct child directory under it must have a catalog entry. Treat a directory without one as catalog drift and add it.
- A cataloged repository may have no checkout on the current machine. Emit a warning, and never remove a catalog entry automatically merely because the directory is absent.
- Catalog membership does not grant the AI read, write, or execute permission, does not require codebase knowledge to index the repository, and does not imply the repository is application source code.
- A repository that is a test environment, documentation, agent skill, extension, fixture, or automation may be cataloged even when codebase knowledge never indexes it.
- `repos/*` is ignored by the root Git repository. Never assume the root workspace and these repositories form one monorepo or share Git history, branches, a staging area, dependencies, or tooling. Each repository may still be a monorepo within its own boundary.
- A repository with its own `.git` must always stay ignored by the root. Committing it into the root produces a gitlink that clones as an empty directory.
- A directory under `repos/` without its own `.git` must opt in with `!repos/<directory>/` in `.gitignore`, otherwise its work is tracked neither in the root nor in itself.
- Check every repository with `python3 tooling/repos_status.py` before committing inside an external repository, and when finishing work that touched several repositories.
- Before running a Git command or a repository-specific tool such as a test runner or a build, change the working directory into the target repository.
- Searching for code works directly from the workspace root. The root `.ignore` file lets `rg` and `fd` see content under `repos/` even though Git still ignores it. Never edit or delete that file; without it, searches from the root return empty results with no error.
- When using a search tool that does not read `.ignore`, search inside the target repository instead. Never conclude that code does not exist from an empty search result.
- Keep each repository's changes limited to what the user asked for, and treat every other repository as an independent boundary.
- Never commit secrets or credentials. Credential files needed for local development must use a form the repository permits and must be ignored by Git.

## AI harness isolation

- The root workspace is the coordination area between the user and the AI; `repos/*` holds external repositories.
- Files and directories used for user-AI collaboration in this workspace belong only in the root workspace, in `workbench/`, or in a location the root workspace defines.
- Never add, copy, or generate this workspace's AI harness configuration into `repos/*` unless the user asks for a change to that repository directly.
- Files that must not be added without an explicit instruction include `AGENTS.md`, `CLAUDE.md`, `.agents/`, `.claude/`, and configuration serving a similar purpose.
- AI harness configuration that already exists inside `repos/*` belongs to that external repository. Never edit, delete, rename, or overwrite it unless the user asks for a change to that file directly.
- Never deliberately adopt AI harness configuration found inside `repos/*` as coordination configuration for the root workspace. Preventing a provider from loading those files automatically must be handled per provider.
- Never store or commit private notes, plans, prompts, evaluation evidence, handoff records, or coordination artifacts inside `repos/*`.
- Before committing inside any repository, verify that no root workspace artifact or AI harness configuration has entered the change set unintentionally.

## Workspace tooling

- `tooling/` holds automation that maintains the root workspace and is not source code of any repository under `repos/`.
- `workbench/workspace-contracts/repository-catalog/` is the workspace-level contract for the Repository Catalog. Software Factory, Codebase Knowledge, and other systems are equal consumers.
- `workbench/repositories.yaml` is the source of truth for cataloged repositories. It uses `schema_version: 1`, and each entry carries only a stable `repo_id` matching `repo_<snake_case_name>` and a `path` that is a direct child of `repos/`.
- Access policy, indexing configuration, integration mapping, and generated knowledge live outside the Repository Catalog and reference repositories by `repo_id`.
- Tool-specific configuration decides which cataloged repositories it uses. Never remove a repository from the Catalog to control access, indexing, or a tool's behavior.
- After editing `workbench/repositories.yaml`, validate with `python3 tooling/validate_repository_catalog.py`, then check every repository with `python3 tooling/repos_status.py`.
- Workspace tooling must not write files into `repos/*` unless the command's purpose is to change the work inside that repository and the user asked for it explicitly.

## Choosing where a file belongs

- Documents for thinking and collaboration → `workbench/`
- Source code, committed tests, reusable fixtures, configuration, and repository-owned build artifacts → `repos/<repository-name>/`
- Temporary files, experiments, generated fixtures, and intermediate output → the harness or system temporary directory, never `workbench/` or `repos/*`
- Root workspace automation → `tooling/`
- Build artifacts inside a repository belong in that repository's standard location and must not be committed unless the repository says otherwise.
- Never place a repository's source code at the workspace root, in `workbench/`, or in `tooling/`.

## Git workflow

Before pushing or changing an upstream in the root workspace or in a repository
under `repos/`, read and follow `GIT_POLICY.md` along with any more specific
instructions belonging to the target repository.

### Repository classes

`GIT_POLICY.md` defines the rules for each class. This table records which
repository belongs to which class, and is the part that differs per project.

- Default class for repositories under `repos/` — `client`
- Root workspace repository — `own`

| repo_id | class | notes |
| --- | --- | --- |
| _(no repository differs from the default yet)_ | | |

A repository absent from this table always uses the default class, so a newly
added repository is push-protected until someone classifies it.

Before merging a feature branch into a target repository's integration branch,
check that repository's own workflow and guidance. Never apply the root
workspace's Git workflow to external repositories automatically.

## Language

These are two separate choices. The language of this file does not determine
the language the AI uses when speaking with the user.

**Speaking with the user, and human-facing output**

- Use Thai by default when speaking with the user.
- Documents, content, and human-facing text that the AI produces are primarily in Thai.
- Proper nouns, technical terms, identifiers, source code, commands, and text that must match a system may stay in their original language.
- When the user explicitly asks for another language, follow the requested language for that work.

**Instruction and contract files in this workspace**

- Files that instruct the AI — this file, `GIT_POLICY.md`, and every `SKILL.md` — are written in English for model and tool compatibility.
- Files that explain the workspace to people, such as `README.md`, follow the human-facing rule above.
- Historical artifacts, regression evidence, and text that must keep its exact form for tracing or comparison are never retranslated.
