# Review sessions are application-owned immutable snapshots

A review session is an application-owned record created from an authoritative pull request snapshot fetched at session start. The application, not the AI CLI, owns session state, completion, cancellation, and review artifact creation so that review history, update detection, and exported Markdown remain auditable and consistent across providers and CLIs.
