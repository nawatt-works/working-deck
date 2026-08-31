# Git Policy

These rules apply to the root workspace and every Git repository under `repos/`.
They protect customer repositories from remote writes and prevent destructive Git
operations from being inferred from an ordinary coding request.

## Repository classes

`_Mission-Control/git-safety.yaml` is the source of repository classification.
Every repository under `repos/` is `client` unless its path is explicitly listed
in `own_repositories` or it is a linked worktree sharing the Git common directory
of an explicitly listed path.

- `client` — owned by a customer or another party. Remote writes are prohibited.
- `own` — owned by the user. An ordinary push is possible only when the user asks
  for that push and the repository's own workflow permits it.
- Root workspace — treated as `own`, but never pushed without a user request.

Never add a path to `own_repositories` by inference. Ask the user when ownership
is unknown.

## Safe local work

Reading, fetching, editing, testing, committing, creating a branch, and creating
a linked worktree are allowed when they are part of the user's requested work.
Run Git and repository-specific commands from inside the target repository.

The following operations can discard work or alter repository configuration and
require a separate, explicit user instruction naming the intended repository and
operation:

- `git reset --hard`
- `git clean -f` in any form
- `git checkout -- <path>` or `git restore` when it discards changes
- forced branch deletion such as `git branch -D`
- deleting a worktree that contains changes
- changing or removing remotes, upstreams, or Git configuration
- rewriting published history

A request to implement, fix, commit, switch branches, or "clean things up" does
not imply permission for these destructive operations. Prefer non-destructive
alternatives and stop when unrelated local changes would be overwritten.

## Remote writes

### Client repositories

Never push a branch, tag, deletion, or any other ref to any remote. Credentials,
an existing upstream, or a generic request to "push" do not override this rule.
If the user appears to request a client push, report that the repository is
classified as `client` and ask them to change the classification deliberately if
it is incorrect.

### Own repositories and root workspace

Push only after the user asks for the specific remote write. Before pushing:

1. Resolve the current branch; do not push from detached HEAD.
2. Inspect pending and staged changes.
3. Verify any upstream branch has exactly the same branch name.
4. Run `python3 _Mission-Control/tooling/git_guard.py status` from the workspace root.
5. Use an explicit same-named refspec and dry run:

   ```bash
   git push --dry-run <remote> HEAD:refs/heads/<branch>
   git push <remote> HEAD:refs/heads/<branch>
   ```

Never use a bare `git push`, `--all`, `--mirror`, `--tags`, or `--follow-tags`.
Push a tag only with an exact tag refspec.

## Force push and remote deletion

Force pushes, moving an existing remote tag, and deleting any remote ref are
prohibited for `client` repositories. For `own` repositories they require a
separate explicit instruction for the exact repository and ref; ordinary push
permission does not include them.

The Working Deck pre-push guard intentionally blocks these operations. Do not
bypass it with `--no-verify`. If an exceptional destructive remote operation is
truly required, stop and let the user choose a separately reviewed procedure.

## Pre-push guard

Install the optional guard with:

```bash
python3 _Mission-Control/tooling/git_guard.py install
```

It applies at Git level across agent harnesses and interactive tools, but it is
an accident guard rather than a security boundary: hooks can be bypassed or
removed. Use read-only credentials and server-side permissions for customer
repositories whenever possible.

The installer refuses to overwrite an existing pre-push hook or configured
`core.hooksPath`. Resolve such conflicts deliberately rather than replacing a
repository-owned workflow.

## Keep workspace coordination out of work repositories

Do not add Working Deck instructions, plans, prompts, private notes, or
`_Mission-Control/` content to a repository under `repos/` unless the user asks
to change that repository-owned file directly.

Before committing in a work repository, run `git_guard.py status` and inspect the
staged paths. Existing committed harness configuration belongs to that
repository and must not be edited merely because Working Deck also uses agents.
