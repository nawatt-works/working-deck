# Workspace Guidelines

This file is an inert instruction template. The workspace owner decides when and
how to expose it to each agent harness by renaming it or creating symlinks. Do
not create `AGENTS.md`, `CLAUDE.md`, or harness-specific symlinks automatically.

## Workspace model

- `_Mission-Control/` is the collaboration control plane shared by the user and
  agent harnesses. It holds cross-repository context, policy, and tooling when a
  real use case needs them.
- Work repositories may live anywhere below the workspace except inside
  `_Mission-Control/`. `repos/` is the default convention, not a required root.
- Every work repository is registered by exact workspace-relative path and class
  in `_Mission-Control/git-safety.yaml`.
- Mission Control is extensible, but plans, handoffs, schemas, catalogs, and
  other ceremony are optional. Do not create them without a concrete need.

Read `_Mission-Control/README.md` before adding a Mission Control capability.
Keep production source code and repository-owned artifacts in the relevant work
repository, not in Mission Control.

## Repository layout and discovery

A repository may be a direct workspace child, may sit under `repos/`, or may use
non-Git grouping directories such as `repos/customer-a/api`. Grouping directories
do not need registry entries; only actual Git top-level working trees do.

Git Safety discovers repositories recursively, skipping Mission Control and
stopping at each Git boundary. A discovered but unregistered repository fails
closed as `client` and is reported as an error. A registered checkout may be
absent on the current machine and remains in the registry with a warning.

Do not use a symlink as a registered repository path. Avoid nested registered
repositories unless the workspace explicitly adds support for repository-owned
submodules.

Search from the workspace root when convenient. `.ignore` exposes the default
`repos/` area; repositories elsewhere need an exact negation entry. Before
running Git, a test runner, a build, or another repository-specific tool, change
into the target repository. Never assume repositories share branches, history,
remotes, dependencies, configuration, or ownership.

Run this from the workspace root before committing in a work repository and
before finishing work that touched multiple repositories:

```bash
python3 _Mission-Control/tooling/git_guard.py status
```

## Root Git isolation

When the workspace root is a Git repository, every nested work repository must
be ignored by root Git to prevent accidental gitlinks. `repos/*` is ignored by
default. Add an exact anchored path to `.gitignore` for every registered
repository elsewhere, and add the corresponding negation to `.ignore` when root
search tools need to see its source.

Git Safety validates root ignore state but does not edit `.gitignore` or `.ignore`
automatically.

## Git safety

Read and follow `GIT_POLICY.md` before any remote write or destructive Git
operation. `_Mission-Control/git-safety.yaml` classifies repositories:

- Every registry entry declares `path` and `class: client|own`.
- An unregistered repository is always treated as `client`.
- The root workspace is `own`, but this never authorizes an unsolicited push.
- A linked worktree not listed separately inherits the class of a registered
  working tree that shares its Git common directory.

A `client` repository may be edited, tested, committed, branched, or used with a
linked worktree when that work serves the user's request. Never push any ref from
it. Credentials, an upstream, or a request to finish the work do not grant push
permission.

For an `own` repository, an ordinary push still requires a user request. Force
push, remote ref deletion, remote tag movement, destructive local commands, and
remote or upstream changes require separate explicit instructions.

Never bypass the Working Deck pre-push guard with `--no-verify`. Reinstall hooks
after moving the workspace because each local hook pins its absolute workspace
path. The hook is only an accident guard; read-only credentials and server
permissions remain the hard boundary for customer repositories.

## Agent collaboration boundaries

Working Deck coordination belongs at the workspace root or in Mission Control,
not inside work repositories. Do not add or copy `AGENTS.md`, `CLAUDE.md`,
`.agents/`, `.claude/`, `_Mission-Control/`, private plans, prompts, or evaluation
artifacts into a work repository unless the user explicitly asks to modify that
repository-owned file.

Harness configuration already committed in a work repository belongs to that
repository. Read repository-specific guidance required for the task, but do not
edit or adopt it as workspace coordination unless the user asks directly.

Use the harness or system temporary directory for scratch files. Do not store
secrets, credentials, access tokens, private keys, or authenticated session
material in Mission Control, temporary artifacts, or committed files.

## Language

Use Thai by default when speaking with the user and for human-facing documents.
Technical identifiers, commands, source code, proper nouns, and externally fixed
text may remain in their original language. Follow an explicit request for
another language.

Instruction files such as this template and `GIT_POLICY.md` use English for
cross-harness compatibility. This choice does not determine the conversation
language.
