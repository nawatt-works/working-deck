# Git Policy for Agents

These instructions govern Git actions performed by agent harnesses in this
workspace. They do not restrict the workspace owner using Git, a Git GUI, or
remote operations directly.

The policy protects customer repositories from accidental agent writes and
prevents destructive operations from being inferred from an ordinary coding
request. The current implementation provides policy and validation, not a Git
hook or technical interception layer.

## Repository registry and classes

`_Mission-Control/git-safety.yaml` is the source of repository classification.
Every work repository has an exact workspace-relative `path` and one class:

- `client` — owned by a customer or another party. Agents must not write to any
  remote.
- `own` — owned by the user. An agent may make an ordinary push only when the
  user asks for that push and the repository's own workflow permits it.
- Root workspace — treated as `own`, but agents never push it without a user
  request.

A discovered repository missing from the registry is treated as `client`. Never
register or change a repository to `own` by inference; ask the user when
ownership is unknown.

A linked worktree may inherit the class of a registered path sharing its Git
common directory. A separate clone has a different Git directory and requires
its own registry entry.

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

## Remote writes by agents

### Client and unregistered repositories

An agent must never push a branch, tag, deletion, or any other ref to any remote.
Credentials, an existing upstream, or a generic request to "push" do not
override this rule. If the classification is incorrect, the user must
deliberately update the registry before an agent performs a remote write.

This restriction applies only to agents. The workspace owner may push directly
according to their own judgment and repository access.

### Own repositories and root workspace

An agent may push only after the user asks for the specific remote write. Before
pushing:

1. Resolve the current branch; do not push from detached HEAD.
2. Inspect pending and staged changes.
3. Verify any upstream branch has exactly the same branch name.
4. Run `python3 _Mission-Control/tooling/git_safety.py status` from the workspace root.
5. Use an explicit same-named refspec and dry run:

   ```bash
   git push --dry-run <remote> HEAD:refs/heads/<branch>
   git push <remote> HEAD:refs/heads/<branch>
   ```

Agents must not use a bare `git push`, `--all`, `--mirror`, `--tags`, or
`--follow-tags`. Push a tag only with an exact tag refspec.

## Force push and remote deletion by agents

Force pushes, moving an existing remote tag, and deleting any remote ref are
prohibited for `client` and unregistered repositories. For `own` repositories
they require a separate explicit user instruction for the exact repository and
ref; ordinary push permission does not include them.

If an exceptional destructive remote operation is requested, stop after
verifying the request and repository class. Do not infer authorization from a
previous ordinary push.

## Policy enforcement boundary

`git_safety.py status` reports registry and repository state but does not block
Git commands. Agents must follow this policy even when they technically possess
write credentials.

This avoids changing the workspace owner's Git behavior or requiring special
human overrides. A future harness extension may enforce the same policy around
agent-issued tool calls without affecting commands run by the owner.

## Root Git isolation

When the workspace root is a Git repository, every nested work repository must
be ignored by root Git. Otherwise staging it may create a gitlink. The default
`repos/*` pattern covers the conventional area; every repository elsewhere
needs an exact anchored `.gitignore` entry.

Run Git Safety status after adding or moving a repository. Do not weaken root
ignore rules merely to make search tools see source; use an exact negation in
`.ignore` instead.

## Keep workspace coordination out of work repositories

Do not add Working Deck instructions, plans, prompts, private notes, or
`_Mission-Control/` content to a work repository unless the user asks to change
that repository-owned file directly.

Before committing in a work repository, run `git_safety.py status` and inspect
the staged paths. Existing committed harness configuration belongs to that
repository and must not be edited merely because Working Deck also uses agents.
