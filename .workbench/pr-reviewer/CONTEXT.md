# PR Reviewer

PR Reviewer is a system for collecting pull requests assigned to a reviewer, analyzing them with an AI CLI, and exporting the resulting review as Markdown.

## Language

**Review Session**:
A single AI review run for one pull request, including its input snapshot, streaming output, and terminal state.
_Avoid_: review job, stream job, task, run

**Pull Request Reference**:
The provider-scoped identity of a pull request, including an opaque provider reference that can be round-tripped to retrieve that pull request reliably across repositories and providers.
_Avoid_: prId, PR ID, number

**Pull Request Snapshot**:
An immutable capture of a pull request's reviewable state at a point in time, including the compared revisions, diff, and relevant review threads.
_Avoid_: latest PR, live PR state, current diff

**Code Update**:
A change to a pull request's source head commit after a previously recorded snapshot or review session.
_Avoid_: PR updated, refreshed PR

**Discussion Update**:
A change to review threads after a previously recorded snapshot or review session, caused by a new thread, a new comment, or a thread status change.
_Avoid_: PR updated, refreshed PR

**Review Baseline**:
The most recent completed review session used as the comparison point for whether a pull request is not reviewed, up to date, or has newer code or discussion changes.
_Avoid_: last seen state, last opened state, cached state

**Review Inbox**:
The set of pull requests where the current user is presently requested or assigned as a reviewer by the provider.
_Avoid_: my PRs, reviewer PRs, assigned PR list

**Pull Request List Scope**:
The configured rule that determines which pull requests appear in the main list, such as the review inbox, pull requests authored by the current user, participating pull requests, or all visible open pull requests.
_Avoid_: PR filter, reviewer mode, list type

**Single-Operator Application**:
An application configured and used by one operator, so system configuration can also serve as that operator's working preference.
_Avoid_: multi-user app, shared workspace

**Application Configuration**:
The operator-managed non-secret settings that define the active provider, selected tools, and main pull request list scope.
_Avoid_: environment only, user preference store, runtime flags

**Current Operator Profile**:
The identity of the application's operator as resolved from the active provider credentials and used to evaluate provider-scoped pull request list scopes.
_Avoid_: manual reviewer ID, configured user ID, current user field

**Active Provider**:
The single provider selected in application configuration and used to populate the current pull request list in this single-operator application.
_Avoid_: current backend, selected integration, provider mode

**Provider Capabilities**:
The explicit statement of which pull request list scopes and related behaviors a provider adapter supports.
_Avoid_: fallback behavior, guessed support, implicit support

**Review Artifact**:
The automatically saved Markdown output created by the application for one completed review session, preserved as an immutable record of that session's review result.
_Avoid_: latest review file, overwritten report, mutable note
