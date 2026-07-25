# PR Reviewer — Project Specification v2

> ระบบ Web Application สำหรับดึง Pull Request จาก Git provider ที่ผู้ใช้ต้องการติดตาม
> ให้ AI CLI ช่วยวิเคราะห์ code review แบบ real-time
> และเก็บผลเป็น Markdown artifact ต่อหนึ่ง review session
>
> **เริ่มต้นที่ Azure DevOps** แต่ architecture ต้องรองรับ GitHub / GitLab / Bitbucket ได้ในอนาคต

---

## Table of Contents

1. [Goals](#1-goals)
2. [Core Domain Decisions](#2-core-domain-decisions)
3. [Architecture Overview](#3-architecture-overview)
4. [Provider Abstraction Layer](#4-provider-abstraction-layer)
5. [Configuration and Runtime Status](#5-configuration-and-runtime-status)
6. [Backend Specification](#6-backend-specification)
7. [Review Session Lifecycle](#7-review-session-lifecycle)
8. [Storage Model](#8-storage-model)
9. [Frontend Specification](#9-frontend-specification)
10. [AI CLI Integration](#10-ai-cli-integration)
11. [Markdown Artifact Format](#11-markdown-artifact-format)
12. [Implementation Order](#12-implementation-order)
13. [Pitfalls and Notes](#13-pitfalls-and-notes)

---

## 1. Goals

- ดึง Pull Request list จาก Git provider โดยเริ่มที่ Azure DevOps
- รองรับ **configurable Pull Request List Scope** เช่น review inbox, authored by me, participating, all visible open
- แสดง PR พร้อม review state ที่คำนวณจาก review history ของระบบ
- ให้ผู้ใช้เริ่ม AI review ได้ทั้งจาก PR list และ PR detail
- สร้าง **Review Session** ที่อ้างอิง **Pull Request Snapshot** แบบ immutable
- stream ผล review แบบ real-time มาแสดงใน UI
- บันทึกผลเป็น **Review Artifact** แบบ Markdown ต่อหนึ่ง completed review session โดยอัตโนมัติ
- เปลี่ยน Git provider ได้โดยไม่ต้อง refactor logic กลาง
- เปลี่ยน AI CLI ได้โดยไม่ผูกกับ provider
- ออกแบบเป็น **single-operator application**

---

## 2. Core Domain Decisions

### 2.1 Core Terms

- **Review Session**: การรัน AI review หนึ่งครั้งสำหรับ pull request หนึ่งรายการ
- **Pull Request Reference**: provider-scoped identity ของ pull request โดยมี opaque provider reference ที่ round-trip ได้
- **Pull Request Snapshot**: immutable capture ของ state ที่ใช้ review ณ เวลาเริ่ม session
- **Review Baseline**: completed review session ล่าสุดที่ใช้เป็นจุดอ้างอิงสำหรับ review state
- **Code Update**: source head commit เปลี่ยนหลัง baseline
- **Discussion Update**: review threads เปลี่ยนหลัง baseline จาก new thread, new comment, หรือ thread status change
- **Review Artifact**: Markdown output ที่ application สร้างและบันทึกอัตโนมัติสำหรับ completed review session
- **Review Inbox**: PRs ที่ provider ระบุว่าปัจจุบัน operator ถูก request/assign ให้ review
- **Pull Request List Scope**: กติกาที่กำหนดว่า PR กลุ่มไหนจะอยู่ใน list หลัก
- **Application Configuration**: non-secret settings ที่ application จัดการเอง
- **Active Provider**: provider เดียวที่ระบบใช้ในปัจจุบัน
- **Provider Capabilities**: สิ่งที่ provider adapter รองรับอย่าง explicit
- **Current Operator Profile**: ตัวตนของ operator ที่ resolve จาก active provider credentials

### 2.2 Architectural Decisions

1. Review Session เป็น application-owned record ไม่ใช่ CLI-owned workflow
2. Review Session ต้อง bind กับ Pull Request Snapshot แบบ immutable ณ เวลาเริ่ม session
3. Completed Review Session เท่านั้นที่เป็น Review Baseline ได้
4. Completed Review Session เท่านั้นที่ต้องมี Review Artifact
5. Application เป็นคน mark session status และสร้าง artifact
6. AI CLI เป็น content generator เท่านั้น ไม่ใช่ authority ของ workflow
7. Application Configuration แยกจาก secrets:
   - non-secret settings → app-managed config
   - secrets → environment variables
8. v1 ใช้ single active provider only
9. v1 ใช้ one metadata file per review session
10. v1 ใช้ backend เป็น owner ของ review-state calculation

### 2.3 ADRs

- `docs/adr/0001-review-sessions-are-application-owned-immutable-snapshots.md`
- `docs/adr/0002-application-configuration-splits-non-secret-settings-from-environment-secrets.md`

---

## 3. Architecture Overview

```text
┌─────────────────────────────────────────────────────────────┐
│                         Web App (React)                    │
│  PR List  │  PR Detail  │  Review Panel  │  Settings       │
└───────────────────────────────┬─────────────────────────────┘
                                │ HTTP / SSE
┌───────────────────────────────▼─────────────────────────────┐
│                  Node.js / Express Backend                  │
│                                                             │
│  ┌────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │ Provider Layer │  │ Review Session  │  │ Runtime      │ │
│  │ + Capabilities │  │ Orchestrator    │  │ Status       │ │
│  └───────┬────────┘  └────────┬────────┘  └──────┬───────┘ │
│          │                    │                  │         │
│  ┌───────▼───────────┐  ┌─────▼──────────────┐   │         │
│  │ Provider Adapters │  │ CLI Runner         │   │         │
│  │ Azure / GitHub... │  │ Prompt Templates   │   │         │
│  └───────────────────┘  └─────────┬──────────┘   │         │
│                                    │              │         │
│                       ┌────────────▼────────────┐ │         │
│                       │ Session Store +         │ │         │
│                       │ Review Artifacts        │ │         │
│                       └─────────────────────────┘ │         │
└────────────────────────────────────────────────────┴─────────┘
```

### Tech Stack

| Layer | Technology | Notes |
| --- | --- | --- |
| Frontend | React + Vite + TypeScript | Tailwind CSS |
| Backend | Node.js + Express + TypeScript | REST + SSE |
| AI Layer | CLI process via `spawn` | claude / opencode / codex / custom |
| Git Provider | REST / GraphQL adapter | Azure first |
| Storage | local files | config, session metadata, artifacts |

---

## 4. Provider Abstraction Layer

### 4.1 Provider Names

```ts
export type ProviderName = "azure" | "github" | "gitlab" | "bitbucket";
```

### 4.2 Pull Request List Scopes

```ts
export type PullRequestListScope =
  | "reviewInbox"
  | "authoredByMe"
  | "participating"
  | "allVisibleOpen";
```

### 4.3 Common Models

```ts
export interface PullRequestReference {
  provider: ProviderName;
  displayId: string; // เช่น "4521"
  providerRef: Record<string, string>; // opaque round-trippable identity
}

export interface RepositoryRef {
  id: string;          // stable provider identity
  fullName: string;    // human-readable canonical name
  slug: string;        // filesystem-safe path component
}

export interface ReviewStateSummary {
  state:
    | "notReviewed"
    | "upToDate"
    | "codeUpdated"
    | "discussionUpdated"
    | "codeAndDiscussionUpdated";
  baselineSessionId?: string;
  discussionSignalQuality: "exact" | "best-effort";
  latestAttemptStatus?: "running" | "failed" | "canceled";
}

export interface PRListSignals {
  sourceRevision: string;
  targetRevision?: string;
  discussionSignalQuality: "exact" | "best-effort";
  discussionSummary?: {
    commentCount?: number;
    threadCount?: number;
    latestActivityAt?: string;
  };
}

export interface PRItem {
  ref: PullRequestReference;
  title: string;
  description: string;
  author: {
    id?: string;
    name: string;
    avatarUrl?: string;
  };
  sourceBranch: string;
  targetBranch: string;
  pullRequestStatus: "open" | "merged" | "closed" | "draft";
  createdAt: string;
  updatedAt: string;
  url: string;
  repository: RepositoryRef;
  reviewerVote?: "approved" | "rejected" | "waiting" | "none";
  latestSignals: PRListSignals;
  reviewState: ReviewStateSummary;
}

export interface ReviewComment {
  id?: string;
  authorId?: string;
  author: string;
  body: string;
  createdAt: string;
  filePath?: string;
  line?: number;
}

export interface ReviewThread {
  id: string;
  status: "active" | "resolved" | "pending";
  filePath?: string;
  line?: number;
  comments: ReviewComment[];
}

export interface FileDiff {
  path: string;
  additions: number;
  deletions: number;
  patch: string;
}

export interface PullRequestSnapshot {
  capturedAt: string;
  sourceRevision: string;
  targetRevision?: string;
  codeFingerprint: string;
  discussionFingerprint: string;
  snapshotFingerprint: string;
  diff: {
    files: FileDiff[];
    totalAdditions: number;
    totalDeletions: number;
    rawContent: string;
  };
  threads: ReviewThread[];
}

export interface PRDetail extends PRItem {
  snapshot: PullRequestSnapshot;
  historySummary: {
    lastCompletedSession?: {
      sessionId: string;
      completedAt: string;
      cli: string;
      promptTemplate: string;
      artifactPath: string;
    };
    lastAttempt?: {
      sessionId: string;
      status: "running" | "completed" | "failed" | "canceled";
      startedAt: string;
      message?: string;
    };
  };
}
```

### 4.4 Provider Capabilities

```ts
export interface ProviderCapabilities {
  supportedListScopes: PullRequestListScope[];
}
```

### 4.5 Current Operator Profile

```ts
export interface CurrentOperatorProfile {
  id: string;
  name: string;
  email?: string;
}
```

### 4.6 Provider Interface

```ts
export interface GitProvider {
  name: string;

  getCapabilities(): ProviderCapabilities;

  getCurrentOperatorProfile(): Promise<CurrentOperatorProfile>;

  listPullRequests(scope: PullRequestListScope): Promise<Omit<PRItem, "reviewState">[]>;

  getPullRequestDetail(ref: PullRequestReference): Promise<Omit<PRDetail, "reviewState" | "historySummary">>;
}
```

### 4.7 Rules

- Provider ต้องประกาศ capabilities อย่าง explicit
- ห้าม silent fallback จาก scope หนึ่งไปอีก scope หนึ่ง
- ถ้า scope ไม่รองรับ ต้อง error ชัดเจน
- `sourceBranch` / `targetBranch` ต้อง strip prefixes เช่น `refs/heads/`
- `PullRequestReference` ต้องเพียงพอสำหรับ round-trip กลับไป fetch detail ได้จริง

---

## 5. Configuration and Runtime Status

### 5.1 Configuration Split

#### Application-managed non-secret config

เก็บในไฟล์ เช่น `data/config.json`

```ts
export interface ApplicationConfiguration {
  activeProvider: ProviderName;
  pullRequestListScope: PullRequestListScope;
  defaultCli: string;
  defaultPromptTemplate: string;

  azure?: {
    org: string;
    project: string;
  };

  github?: {
    owner?: string;
  };

  gitlab?: {
    baseUrl?: string;
    groupId?: string;
  };

  bitbucket?: {
    workspace: string;
    username: string;
  };
}
```

#### Environment-managed secrets

เก็บใน `.env`

```bash
AZURE_PAT=
GITHUB_TOKEN=
GITLAB_TOKEN=
BITBUCKET_APP_PASSWORD=
OPENAI_API_KEY=
```

### 5.2 Runtime Status

Runtime status คือ observed/computed state ไม่ใช่ editable config

```ts
export interface RuntimeStatus {
  activeProvider: ProviderName;
  providerReadiness: "ready" | "misconfigured" | "identityUnavailable";
  providerReadinessMessage?: string;

  secretStatus: Record<string, "configured" | "missing">;

  currentOperatorProfile?: {
    id: string;
    name: string;
    email?: string;
  };

  providerCapabilities?: ProviderCapabilities;

  cliStatus: Array<{
    name: string;
    available: boolean;
    message?: string;
  }>;

  promptTemplates: {
    available: string[];
    defaultTemplate: string;
    defaultTemplateValid: boolean;
  };
}
```

### 5.3 Provider Readiness Rules

- `ready` = provider config ครบ, secret พร้อม, resolve operator profile ได้
- `misconfigured` = config หรือ secrets ไม่ครบ
- `identityUnavailable` = credentials ใช้ได้บางส่วน แต่ resolve current operator profile ไม่สำเร็จ

### 5.4 Settings Rules

- Settings modal แก้ได้เฉพาะ non-secret settings
- แสดง secret status แบบ `configured` / `missing`
- แสดง readiness reason ชัดเจน
- secret values ต้องไม่ถูก echo กลับไปยัง UI

---

## 6. Backend Specification

### 6.1 Project Structure

```text
backend/
├── src/
│   ├── providers/
│   │   ├── base.ts
│   │   ├── factory.ts
│   │   ├── azure.ts
│   │   ├── github.ts
│   │   ├── gitlab.ts
│   │   └── bitbucket.ts
│   ├── routes/
│   │   ├── config.ts
│   │   ├── runtimeStatus.ts
│   │   ├── prs.ts
│   │   ├── reviewSessions.ts
│   │   └── artifacts.ts
│   ├── services/
│   │   ├── providerService.ts
│   │   ├── reviewStateService.ts
│   │   ├── reviewSessionService.ts
│   │   ├── cliRunner.ts
│   │   ├── promptTemplates.ts
│   │   └── storage.ts
│   ├── types/
│   │   ├── provider.ts
│   │   ├── reviewSession.ts
│   │   └── config.ts
│   ├── config/
│   │   ├── appConfig.ts
│   │   └── env.ts
│   └── server.ts
└── package.json
```

### 6.2 Review Session Model

```ts
export type ReviewSessionStatus =
  | "queued"
  | "running"
  | "completed"
  | "failed"
  | "canceled";

export interface ReviewSessionError {
  code: string;
  message: string;
}

export interface ReviewSessionRecord {
  id: string;
  prRef: PullRequestReference;
  repository: RepositoryRef;

  status: ReviewSessionStatus;

  provider: ProviderName;
  cli: string;
  promptTemplate: string;

  startedAt: string;
  completedAt?: string;

  snapshot: {
    capturedAt: string;
    sourceRevision: string;
    targetRevision?: string;
    codeFingerprint: string;
    discussionFingerprint: string;
    snapshotFingerprint: string;
  };

  artifactPath?: string;

  rawOutput?: string;
  error?: ReviewSessionError;

  cancellationRequested?: boolean;
}
```

### 6.3 API Endpoints

#### Config and runtime

| Method | Route | Description |
| --- | --- | --- |
| GET | `/api/config` | อ่าน application-managed non-secret config |
| PUT | `/api/config` | แก้ application-managed non-secret config |
| GET | `/api/runtime-status` | readiness, operator profile, capabilities, CLI availability, prompt templates |

#### Pull requests

| Method | Route | Description |
| --- | --- | --- |
| GET | `/api/prs` | ดึง full PR list ของ active provider + configured scope |
| GET | `/api/prs/:encodedRef` | ดึง PR detail + history summary |
| POST | `/api/prs/:encodedRef/refresh` | optional helper สำหรับ refresh latest detail authoritatively |

> หมายเหตุ: `:encodedRef` คือ encoded form ของ `PullRequestReference` สำหรับ route usage

#### Review sessions

| Method | Route | Description |
| --- | --- | --- |
| POST | `/api/review-sessions` | create-and-start review session |
| GET | `/api/review-sessions/:sessionId` | session metadata |
| GET | `/api/review-sessions/:sessionId/stream` | SSE stream พร้อม replay accumulated output |
| POST | `/api/review-sessions/:sessionId/cancel` | request cancellation |
| POST | `/api/review-sessions/:sessionId/retry-artifact-save` | narrow recovery for `ARTIFACT_WRITE_FAILED` |

#### Artifacts

| Method | Route | Description |
| --- | --- | --- |
| GET | `/api/review-sessions/:sessionId/artifact` | download/open Markdown artifact |

### 6.4 Create Review Session Request

```json
{
  "prRef": {
    "provider": "azure",
    "displayId": "4521",
    "providerRef": {
      "project": "my-project",
      "repositoryId": "repo-123",
      "prId": "4521"
    }
  },
  "cli": "claude",
  "promptTemplate": "default"
}
```

### 6.5 Create Review Session Responses

#### `201 Created`

```json
{
  "sessionId": "rs_01J...",
  "status": "queued"
}
```

#### `409 Conflict`

เมื่อมี running session สำหรับ PR เดียวกันอยู่แล้ว

```json
{
  "code": "REVIEW_SESSION_ALREADY_RUNNING",
  "message": "A review session is already running for this pull request.",
  "sessionId": "rs_01J..."
}
```

### 6.6 SSE Event Format

```text
data: {"type":"replay","content":"# PR Review..."}

data: {"type":"chunk","content":"## Summary\n"}

data: {"type":"status","status":"running"}

data: {"type":"done","status":"completed","artifactPath":"reviews/...md"}

data: {"type":"error","code":"CLI_NOT_FOUND","message":"claude CLI not found"}
```

### 6.7 Review Session Start Rules

When `POST /api/review-sessions` is called:

1. validate runtime status
2. validate chosen CLI availability
3. validate chosen prompt template
4. reject if another session for same `PullRequestReference` is already `running`
5. refetch authoritative PR detail from provider
6. build immutable Pull Request Snapshot
7. create session record in `queued`
8. start CLI process
9. move session to `running`
10. stream output
11. on success, create Review Artifact and mark `completed`
12. on failure, mark `failed`
13. on successful cancel, mark `canceled`

### 6.8 Canonical Error Codes

At minimum:

- `PROVIDER_NOT_READY`
- `PROVIDER_AUTH_FAILED`
- `PROVIDER_SCOPE_UNSUPPORTED`
- `OPERATOR_PROFILE_UNAVAILABLE`
- `CLI_NOT_AVAILABLE`
- `CLI_NOT_FOUND`
- `CLI_EXIT_NON_ZERO`
- `PROMPT_TEMPLATE_INVALID`
- `REVIEW_SESSION_ALREADY_RUNNING`
- `PULL_REQUEST_REFRESH_CONFLICT`
- `ARTIFACT_WRITE_FAILED`
- `SESSION_NOT_FOUND`

---

## 7. Review Session Lifecycle

### 7.1 Statuses

```text
queued -> running -> completed
                 -> failed
                 -> canceled
```

### 7.2 Completion Rules

- `completed` only when:
  - CLI process exits successfully
  - artifact creation succeeds
- if CLI succeeds but artifact creation fails:
  - session = `failed`
  - error code = `ARTIFACT_WRITE_FAILED`
- failed/canceled sessions do not become Review Baseline
- completed sessions always auto-create Review Artifact

### 7.3 Cancel Rules

- cancel allowed only while `running`
- public status remains `running` until process closes
- UI may show transient `Canceling...`
- when process closes:
  - if cancellation requested and process stops cleanly → `canceled`
  - otherwise → `failed`

### 7.4 Restart Recovery Rules

On application startup:

- scan session metadata files
- any leftover `queued` or `running` session from previous process is marked `failed`
- use clear message like `Application restarted while session was running`

### 7.5 Review Baseline Rules

- baseline = latest completed session by completion time for a PR
- if multiple completed sessions exist for same snapshot, latest completion still wins
- failed/canceled sessions may appear as latest attempt hints but never become baseline

---

## 8. Storage Model

### 8.1 Directory Layout

```text
data/
├── config.json
└── review-sessions/
    └── {provider}/
        └── {repoSlug}/
            └── PR-{displayId}/
                └── {timestamp}-{sessionIdShort}.json

reviews/
└── {provider}/
    └── {repoSlug}/
        └── PR-{displayId}/
            └── {timestamp}-{sessionIdShort}.md
```

### 8.2 Review Session Metadata Files

- one file per session
- metadata path mirrors artifact hierarchy as much as possible
- v1 scans metadata files on demand
- no separate index in v1

### 8.3 Raw Output Persistence Rules

- `completed` sessions: persist raw output
- `failed` sessions: persist raw output if any exists
- `canceled` sessions: optional, not required in v1
- raw output is not a Review Artifact unless session is `completed`

### 8.4 In-memory Running Output

- during `running`, accumulated output is kept in memory for SSE replay
- on finalize, raw output is persisted to session metadata
- v1 does not guarantee replay across backend restart

### 8.5 Artifact Naming Rules

- one artifact per completed review session
- never overwrite previous artifacts
- use human-readable path plus unique suffix
- repo path uses canonical safe slug, not display text directly

Example:

```text
reviews/azure/backend-api/PR-4521/2026-06-04T14-32-10Z-a1b2c3d4.md
```

---

## 9. Frontend Specification

### 9.1 Project Structure

```text
frontend/
├── src/
│   ├── components/
│   │   ├── PRList.tsx
│   │   ├── PRItem.tsx
│   │   ├── PRDetail.tsx
│   │   ├── ReviewPanel.tsx
│   │   ├── ReviewHistorySummary.tsx
│   │   └── SettingsModal.tsx
│   ├── hooks/
│   │   ├── usePRList.ts
│   │   ├── usePRDetail.ts
│   │   ├── useReviewSession.ts
│   │   └── useRuntimeStatus.ts
│   ├── api/
│   │   └── client.ts
│   ├── types/
│   │   ├── provider.ts
│   │   ├── reviewSession.ts
│   │   └── config.ts
│   └── App.tsx
└── package.json
```

### 9.2 Main Layout

```text
┌──────────────┬──────────────────────────┬──────────────────┐
│ PR List      │ PR Detail                │ Review Output    │
│              │                          │                  │
│ - cards      │ - metadata               │ - stream output  │
│ - badges     │ - snapshot notice        │ - session status │
│ - refresh    │ - diff viewer            │ - cancel         │
│              │ - threads                │ - artifact link  │
└──────────────┴──────────────────────────┴──────────────────┘
```

### 9.3 PR List Behavior

- list uses configured `Pull Request List Scope`
- backend returns full list in v1
- backend computes canonical `reviewState`
- each card shows:
  - main review-state badge
  - one secondary status line only

#### secondary line priority

1. `Review running`
2. `Last attempt failed`
3. `Last attempt canceled`
4. `Discussion signal is approximate`
5. none

### 9.4 Review State UI

Canonical states:

- `notReviewed`
- `upToDate`
- `codeUpdated`
- `discussionUpdated`
- `codeAndDiscussionUpdated`

Presentation may be one combined badge or multiple chips, but canonical state comes from backend.

### 9.5 Refresh Policy

- manual refresh button
- auto-refresh PR list every 5 minutes
- list refresh must not replace detail pane when detail is locked to a running session snapshot
- if selected PR disappears from current list scope, detail pane may remain open with notice

### 9.6 Starting Reviews

- reviews can start from list or detail
- starting from list auto-selects the PR and opens/syncs detail pane
- before creating session, backend refetches authoritative detail every time
- if detail currently shown is stale compared to latest provider state:
  - UI must notify user
  - allow action `Review latest changes`
  - do not allow starting from stale detail snapshot

### 9.7 Detail Pane Rules

- while a session is `running`, detail pane is locked to that session's Pull Request Snapshot
- if live PR changes during run, show notice like `New changes are available since this review started`
- after session completes, keep showing reviewed snapshot until user explicitly refreshes to latest
- detail page shows review history summary:
  - last completed review
  - last attempt

### 9.8 Review Panel Rules

- connect to `/api/review-sessions/:id/stream`
- stream endpoint must replay accumulated output before tailing new output
- panel shows:
  - running/completed/failed/canceled status
  - cancel button while running
  - artifact actions after completion (`Open Artifact`, `Download Markdown`, `Copy Markdown`)

### 9.9 Settings Modal Rules

- edit application-managed non-secret settings only
- show runtime status summary
- show provider readiness
- show secret status without exposing values
- disable unavailable CLIs
- show available prompt templates and default validity

---

## 10. AI CLI Integration

### 10.1 CLI Registry

```ts
interface CLIConfig {
  bin: string;
  args: string[];
}

export const CLI_REGISTRY: Record<string, CLIConfig> = {
  claude: { bin: "claude", args: ["-p"] },
  opencode: { bin: "opencode", args: ["--prompt"] },
  codex: { bin: "codex", args: ["-q"] },
};
```

### 10.2 CLI Availability

- runtime status should report whether each registered CLI is available
- unavailable CLIs should be disabled in UI
- session start must still validate availability server-side

### 10.3 Prompt Templates

v1 uses named templates only:

- `default`
- optional future additions: `strict`, `security-focused`

Rules:

- application config stores default prompt template
- session creation may override template per session
- session record stores effective template used
- no free-form prompt editing in v1

### 10.4 Prompt Responsibilities

Prompt/template may control review structure, but:

- it does not own session completion
- it does not create artifact files directly
- it does not mark workflow status

### 10.5 Diff Size Limit

Before invoking CLI, truncate oversized diffs.

```ts
const MAX_DIFF_CHARS = 80_000;
```

If truncated:

- snapshot still records that truncation occurred
- prompt includes note that diff was truncated

---

## 11. Markdown Artifact Format

### 11.1 Artifact Ownership

- artifact is application-composed Markdown
- main body comes from raw CLI output
- app may add metadata header/footer and light normalization
- app must not rewrite review meaningfully
- raw CLI output should also be preserved separately for audit/debug

### 11.2 Suggested Structure

```markdown
# PR Review: {title}

> **Provider:** {provider}
> **Pull Request:** {repository.fullName} PR {ref.displayId}
> **Branches:** `{sourceBranch}` → `{targetBranch}`
> **Author:** {author}
> **Session ID:** {sessionId}
> **Reviewed At:** {completedAt}
> **CLI:** {cli}
> **Prompt Template:** {promptTemplate}

---

{rawCliMarkdownOutput}

---

_Generated by PR Reviewer_
```

### 11.3 Artifact Creation Rules

- auto-create only for completed sessions
- if artifact write fails, session becomes failed
- support narrow recovery action `retry-artifact-save` for `ARTIFACT_WRITE_FAILED`

---

## 12. Implementation Order

```text
Step 1: Bootstrap backend/frontend structure
  └─ config loading, runtime status endpoint, base types

Step 2: Implement Application Configuration store
  └─ data/config.json + env secret loading

Step 3: Implement Azure provider
  ├─ capabilities
  ├─ current operator profile
  ├─ listPullRequests(scope)
  └─ getPullRequestDetail(ref)

Step 4: Implement review state service
  └─ baseline lookup, code/discussion update calculation, list badges

Step 5: Implement review session storage
  └─ one metadata file per session + startup reconciliation

Step 6: Implement CLI runner and prompt template registry
  └─ availability checks + session orchestration

Step 7: Implement POST /api/review-sessions + SSE stream replay
  └─ create-and-start, replay accumulated output, cancel support

Step 8: Implement artifact creation and retry-artifact-save
  └─ application-composed Markdown

Step 9: Frontend PR list and runtime status
  └─ list scopes, badges, readiness UI

Step 10: Frontend PR detail and review panel
  └─ lock snapshot during run, history summary, artifact actions

Step 11: Settings modal
  └─ non-secret editing, CLI/template/provider readiness

Step 12: Add GitHub/GitLab/Bitbucket stubs
  └─ capability-driven future expansion
```

---

## 13. Pitfalls and Notes

### Backend

- SSE endpoint must set:
  ```text
  Content-Type: text/event-stream
  Cache-Control: no-cache
  Connection: keep-alive
  ```
- `EventSource` is GET-only, so review start and review stream must be separate endpoints
- review start must refetch authoritative provider detail every time
- do not derive review state in the frontend
- do not let CLI mark session complete
- do not overwrite artifacts

### Provider Layer

- Azure/GitHub/GitLab/Bitbucket have different identity semantics for `me`
- resolve Current Operator Profile from credentials, do not require manual reviewer ID config
- support provider pagination internally even though app-level API returns full list in v1
- be explicit about unsupported scopes

### Frontend

- detail pane and review output must stay coherent with session snapshot
- list refresh must not silently replace running-session detail content
- `Discussion updated` in list may be best-effort; detail is authoritative

### Storage

- use safe repo slug in filesystem paths
- keep metadata and artifact hierarchy aligned
- persist raw output for completed and failed sessions when available
- reconcile orphaned running sessions on startup

---

_PR Reviewer Spec v2 — aligned with domain glossary and ADR decisions_