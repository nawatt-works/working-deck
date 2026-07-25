# Application configuration splits non-secret settings from environment secrets

This single-operator application keeps operator-managed non-secret settings in an application-managed configuration store while secrets remain in environment variables. This allows the UI to edit active provider, tool selection, and pull request list scope without turning tokens and passwords into application-managed plaintext records.
