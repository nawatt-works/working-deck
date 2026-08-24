# Workspace Guidelines

This workspace has two primary areas: `_Mission-Control/` is the workspace
control plane, and `repos/` contains the work repositories. Root-level files
such as `.ignore`, `GIT_POLICY.md`, and harness-specific directories remain at
the root when they must be discovered there.

## `_Mission-Control/` — workspace control plane

- Holds shared workspace metadata, contracts, and automation, but never product
  source code.
- Read `_Mission-Control/AGENTS.md` and `_Mission-Control/README.md` before
  adding a new control-plane area.
- Direct work and delegated multi-agent work are both valid. Use plans,
  handoffs, logs, or delegation only when the task actually needs durable
  coordination across roles, sessions, or automation.
- Being inside Mission Control does not grant access to a work repository.
  Repository access and Git operations remain governed by these root
  instructions, `GIT_POLICY.md`, user authorization, and repository-specific
  guidance.

### `_Mission-Control/workspace-meta/` — public workspace metadata

- Holds workspace-owned metadata and contracts that multiple harnesses, skills, or automation can share, but never product source code.
- Examples: Repository Catalog, handoff contracts, shared schemas, and future workspace-level contract instances.
- Do not treat this as the required home for every AI note, plan, prompt, output, or harness artifact.
- Harness-owned artifacts may live wherever that harness defines them, such as `.agents/`, `.claude/`, `.cursor/`, `.my-harness/`, or another documented location. Other producers should consume those artifacts from the owning harness's location and contract instead of copying them into `_Mission-Control/workspace-meta/`.
- Never store anything that grants access to a system — secrets, access tokens, credentials, private keys, session material, or connection strings containing a password. The test: if this leaked, could someone use it to act as a person or reach a system?
- Names or handles of people involved in the work may be stored when they are part of a work record, such as who reviewed or approved something. Keep only what the work needs; do not collect contact details without a reason.
- Read `_Mission-Control/workspace-meta/README.md` before creating a new file in it.
- Files at the root of `_Mission-Control/workspace-meta/` are shared. Create or edit them when the user asks, when following that file's contract, or when adding a new workspace metadata type together with its contract and appropriate validation. When an artifact references a repository, reference it by `repo_id` rather than by path unless the relevant contract explicitly says otherwise.
- Work that will cross to another role may go into `_Mission-Control/workspace-meta/handoff/<work_id>/`, where write permission is set by stage, because a handoff document is written for someone else to act on. Read `_Mission-Control/workspace-meta/handoff/README.md` before creating or continuing a work item.
- A stage file has exactly one writing role. Respond by writing your own stage file, never by editing another role's, and act only on a document whose `status` is `ready`.
- Work you finish yourself does not go through `handoff/`. Keep it in the owning harness or workflow's normal artifact location.

## Temporary files

- Use the temporary directory or scratchpad that the harness or the system provides for work-in-progress files such as caches, logs, extracted files, generated samples, and intermediate output.
- This workspace has no central folder for temporary files. Do not create one, and do not leave temporary files inside `_Mission-Control/`, `repos/*`, or the workspace root.
- Do not write outside the workspace anywhere other than the harness or system temporary directory, unless the user explicitly allows it.
- Keep each task's files in a meaningful subdirectory so they do not collide and can be reviewed or deleted later.
- Before deleting or overwriting an existing file, confirm it does not belong to the user or to other work.
- When a result becomes workspace-level metadata, reusable evidence with a shared contract, or a checkpoint another producer must follow, summarize or move only what is needed into the appropriate durable location.
- When a temporary result is something the user must review, always tell them where the file is.
- Never store anything that grants access to a system in temporary files — secrets, access tokens, credentials, private keys, session material, or connection strings containing a password.

## `repos/` — work repositories

- Holds checkouts of the Git repositories that are the real work or that support it, such as backend, frontend, API, consumer, worker, library, infrastructure, documentation, test environment, agent skill, extension, or automation.
- Each first-level directory under `repos/` is normally a Git repository independent of the root workspace, and may be owned by an external person or team.
- A repository under `repos/` may be a single-project repository or a monorepo containing several applications, services, packages, or libraries.
- Never infer a repository's internal structure from the fact that it sits under `repos/`. Always check the target repository's configuration, documentation, and guidance before working in it.
- In this workspace's documents, **workspace repository** or **repo** means a direct child directory under `repos/`, normally a Git checkout. **Cataloged repository** means a repo listed in `_Mission-Control/workspace-meta/repositories.yaml`.
- The word repository as it appears inside source code — the repository pattern, a data repository, `Repository<T>`, or a class ending in `Repository` — is a concept internal to the work and is neither a workspace repository nor a cataloged repository.
- `_Mission-Control/workspace-meta/repositories.yaml` is the authoritative Repository Catalog of every repository that belongs to this project workspace.
- `repos/` must contain only workspace repositories, so every direct child directory under it must have a catalog entry. Treat a directory without one as catalog drift and add it.
- A cataloged repository may have no checkout on the current machine. Emit a warning, and never remove a catalog entry automatically merely because the directory is absent.
- Catalog membership does not grant the AI read, write, or execute permission, does not require codebase knowledge to index the repository, and does not imply the repository is application source code.
- A repository that is a test environment, documentation, agent skill, extension, fixture, or automation may be cataloged even when codebase knowledge never indexes it.
- `repos/*` is ignored by the root Git repository. Never assume the root workspace and these repositories form one monorepo or share Git history, branches, a staging area, dependencies, or tooling. Each repository may still be a monorepo within its own boundary.
- A repository with its own `.git` must always stay ignored by the root. Committing it into the root produces a gitlink that clones as an empty directory.
- A directory under `repos/` without its own `.git` must opt in with `!repos/<directory>/` in `.gitignore`, otherwise its work is tracked neither in the root nor in itself.
- Check every repository with `python3 _Mission-Control/tooling/repos_status.py` before committing inside an external repository, and when finishing work that touched several repositories.
- Before running a Git command or a repository-specific tool such as a test runner or a build, change the working directory into the target repository.
- Searching for code works directly from the workspace root. The root `.ignore` file lets `rg` and `fd` see content under `repos/` even though Git still ignores it. Never edit or delete that file; without it, searches from the root return empty results with no error.
- When using a search tool that does not read `.ignore`, search inside the target repository instead. Never conclude that code does not exist from an empty search result.
- Keep each repository's changes limited to what the user asked for, and treat every other repository as an independent boundary.
- Never commit secrets or credentials. Credential files needed for local development must use a form the repository permits and must be ignored by Git.

## AI harness isolation

- The root workspace is the coordination area between the user and the AI; `repos/*` and any other documented source roots hold work repositories.
- Files and directories used for user-AI collaboration in this workspace belong only in the root workspace, in `_Mission-Control/`, or in a documented harness-owned location at the root workspace.
- Never add, copy, or generate this workspace's AI harness configuration into a work repository unless the user asks for a change to that repository directly.
- Files that must not be added without an explicit instruction include `AGENTS.md`, `CLAUDE.md`, `.agents/`, `.claude/`, and configuration serving a similar purpose.
- AI harness configuration that already exists inside a work repository belongs to that repository. Never edit, delete, rename, or overwrite it unless the user asks for a change to that file directly.
- Never deliberately adopt AI harness configuration found inside a work repository as coordination configuration for the root workspace. Preventing a provider from loading those files automatically must be handled per provider.
- Never store or commit private notes, plans, prompts, evaluation evidence, handoff records, or coordination artifacts inside a work repository.
- Before committing inside any repository, verify that no root workspace artifact or AI harness configuration has entered the change set unintentionally.

## Mission Control tooling

- `_Mission-Control/tooling/` holds automation that maintains the root workspace and is not source code of any repository under `repos/`.
- `_Mission-Control/workspace-meta/contracts/repository-catalog/` is the workspace-level contract for the Repository Catalog. Software Factory, Codebase Knowledge, and other systems are equal consumers.
- `_Mission-Control/workspace-meta/contracts/handoff/` is the workspace-level contract for handoff documents. It defines the work item directory name, the `<NN>-<stage>.md` file name, and the required frontmatter.
- `_Mission-Control/workspace-meta/repositories.yaml` is the source of truth for cataloged repositories. It uses `schema_version: 1`, and each entry carries only a stable `repo_id` matching `repo_<snake_case_name>` and a `path` that is a direct child of `repos/`.
- Access policy, indexing configuration, integration mapping, and generated knowledge live outside the Repository Catalog and reference repositories by `repo_id`.
- Tool-specific configuration decides which cataloged repositories it uses. Never remove a repository from the Catalog to control access, indexing, or a tool's behavior.
- After editing `_Mission-Control/workspace-meta/repositories.yaml`, validate with `python3 _Mission-Control/tooling/validate_repository_catalog.py`, then check every repository with `python3 _Mission-Control/tooling/repos_status.py`.
- After writing or moving a handoff document, validate with `python3 _Mission-Control/tooling/validate_handoff.py`.
- Workspace tooling must not write files into `repos/*` unless the command's purpose is to change the work inside that repository and the user asked for it explicitly.

## Choosing where a file belongs

- Workspace-level metadata and contracts → `_Mission-Control/workspace-meta/`
- Documents one role hands to another through the Working Deck handoff contract → `_Mission-Control/workspace-meta/handoff/<work_id>/`
- Harness-specific notes, plans, prompts, outputs, skills, and generated artifacts → the owning harness's documented location
- Source code, committed tests, reusable fixtures, configuration, and repository-owned build artifacts → `repos/<repository-name>/`
- Temporary files, experiments, generated fixtures, and intermediate output → the harness or system temporary directory, never `_Mission-Control/` or `repos/*`
- Root workspace automation → `_Mission-Control/tooling/`
- Build artifacts inside a repository belong in that repository's standard location and must not be committed unless the repository says otherwise.
- Never place a repository's source code at the workspace root or in `_Mission-Control/`.

## Git workflow

Push or change an upstream only when the user asks for that remote write.
Before doing so in the root workspace, in a repository under `repos/`, or in any
other source root this project documents, read and follow `GIT_POLICY.md` along
with any more specific instructions belonging to the target repository.

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
