# Workspace Guidelines

This file is an inert instruction template. The workspace owner decides when and
how to expose it to each agent harness by renaming it or creating symlinks. Do
not create `AGENTS.md`, `CLAUDE.md`, or harness-specific symlinks automatically.

## Workspace model

- `_Mission-Control/` is the collaboration control plane shared by the user and
  agent harnesses. It holds cross-repository context, policy, and tooling when a
  real use case needs them.
- `repos/` contains the independent Git working trees where product and support
  work happens. Every direct child must be a Git repository or linked worktree.
- The root Git repository ignores all of `repos/*`; never opt a work repository
  into root tracking or create a gitlink.
- Mission Control is extensible, but plans, handoffs, schemas, catalogs, and
  other ceremony are optional. Do not create them without a concrete need.

Read `_Mission-Control/README.md` before adding a Mission Control capability.
Keep production source code and repository-owned artifacts in the relevant work
repository, not in Mission Control.

## Repository discovery and commands

Search from the workspace root when convenient; `.ignore` lets `rg` and `fd` see
content under `repos/` while preserving each repository's own ignore rules.

Before running Git, a test runner, a build, or another repository-specific tool,
change into the target repository. Never assume repositories share branches,
history, remotes, dependencies, configuration, or ownership.

Run this from the workspace root before committing in a work repository and
before finishing work that touched multiple repositories:

```bash
python3 _Mission-Control/tooling/git_guard.py status
```

## Git safety

Read and follow `GIT_POLICY.md` before any remote write or destructive Git
operation. `_Mission-Control/git-safety.yaml` classifies repositories:

- Every repository under `repos/` defaults to `client`.
- A path is `own` only when the user has explicitly placed it in
  `own_repositories`.
- The root workspace is `own`, but this never authorizes an unsolicited push.

A `client` repository may be edited, tested, committed, branched, or used with a
linked worktree when that work serves the user's request. Never push any ref from
it. Do not infer that credentials, an upstream, or a request to finish the work
grants push permission.

For an `own` repository, an ordinary push still requires a user request. Force
push, remote ref deletion, remote tag movement, destructive local commands, and
remote or upstream changes require separate explicit instructions.

Never bypass the Working Deck pre-push guard with `--no-verify`. The hook is only
an accident guard; read-only credentials and server permissions remain the hard
boundary for customer repositories.

## Agent collaboration boundaries

Working Deck coordination belongs at the workspace root or in Mission Control,
not inside work repositories. Do not add or copy `AGENTS.md`, `CLAUDE.md`,
`.agents/`, `.claude/`, `_Mission-Control/`, private plans, prompts, or evaluation
artifacts into `repos/*` unless the user explicitly asks to modify that
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
