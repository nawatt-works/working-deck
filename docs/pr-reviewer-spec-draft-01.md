# PR Reviewer — Project Specification

> ระบบ Web Application ดึง Pull Request ที่ผู้ใช้เป็น Reviewer มาแสดง
> และให้ AI CLI ช่วยวิเคราะห์ code พร้อม export เป็น Markdown report
>
> **เริ่มต้นที่ Azure DevOps** แต่ออกแบบให้รองรับ GitHub / GitLab / Bitbucket ได้ในอนาคต

---

## Table of Contents

1. [Goals](#1-goals)
2. [Architecture Overview](#2-architecture-overview)
3. [Provider Abstraction Layer](#3-provider-abstraction-layer)
4. [Backend Specification](#4-backend-specification)
5. [Frontend Specification](#5-frontend-specification)
6. [AI CLI Layer](#6-ai-cli-layer)
7. [Markdown Output Format](#7-markdown-output-format)
8. [Setup Guide](#8-setup-guide)
9. [Implementation Order](#9-implementation-order)
10. [Pitfalls & Notes](#10-pitfalls--notes)

---

## 1. Goals

- ดึง PR list ที่ user เป็น reviewer จาก Git provider (เริ่มที่ Azure DevOps)
- แสดง PR พร้อม metadata: title, author, branch, status, วันที่
- กดปุ่ม "Review with AI" เพื่อให้ AI CLI วิเคราะห์ diff และ comment threads
- Stream ผลลัพธ์แบบ real-time มาแสดงใน UI (ไม่รอจนจบ)
- บันทึก output เป็น `.md` file แยกตาม PR
- **เปลี่ยน Git provider ได้โดยแค่ swap config** ไม่ต้อง refactor logic กลาง
- **เปลี่ยน AI CLI ได้อิสระ** ไม่ผูกกับ provider ใด (claude / opencode / codex / ฯลฯ)

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                   Web App (React)                    │
│  PRList │ PRDetail │ ReviewPanel │ SettingsModal     │
└────────────────────┬────────────────────────────────┘
                     │ HTTP / SSE
┌────────────────────▼────────────────────────────────┐
│               Node.js / Express Backend              │
│                                                      │
│  ┌────────────────┐   ┌──────────┐  ┌────────────┐  │
│  │ Provider Router│   │CLI Runner│  │Config Store│  │
│  └───────┬────────┘   └────┬─────┘  └────────────┘  │
│          │                 │                         │
│  ┌───────▼──────────────┐  │                         │
│  │  Provider Adapters   │  │ spawn process           │
│  │  - AzureAdapter      │  │                         │
│  │  - GitHubAdapter     │  │                         │
│  │  - GitLabAdapter     │  │                         │
│  │  - BitbucketAdapter  │  │                         │
│  └───────┬──────────────┘  │                         │
└──────────┼─────────────────┼─────────────────────────┘
           │                 │
    Git Provider API      AI CLI process
    (REST / GraphQL)      (claude / opencode / codex)
                                  │
                           ./reviews/*.md
```

### Tech Stack

| Layer        | Technology                     | หมายเหตุ                        |
| ------------ | ------------------------------ | ------------------------------- |
| Frontend     | React + Vite + TypeScript      | Tailwind CSS                    |
| Backend      | Node.js + Express + TypeScript | REST API + SSE streaming        |
| AI Layer     | CLI process (spawn)            | claude / opencode / codex / ฯลฯ |
| Git Provider | REST API                       | เริ่มที่ Azure DevOps v7.1      |
| Output       | Markdown (.md)                 | บันทึกใน `./reviews/` directory |

---

## 3. Provider Abstraction Layer

นี่คือหัวใจของ design ที่ทำให้รองรับหลาย provider ได้

### 3.1 Common Data Models

ไม่ว่าจะเป็น Azure / GitHub / GitLab — ทุก adapter ต้อง map ข้อมูลมาสู่ format กลางนี้:

```typescript
// types/provider.ts

export interface PRItem {
  id: string;
  title: string;
  description: string;
  author: {
    name: string;
    avatarUrl?: string;
  };
  sourceBranch: string; // "feature/my-feature"  (ไม่มี refs/heads/ prefix)
  targetBranch: string; // "main"
  status: "open" | "merged" | "closed" | "draft";
  createdAt: string; // ISO 8601
  updatedAt: string;
  url: string; // ลิงก์ไปหน้า PR จริง
  repository: {
    name: string;
    fullName: string; // "org/repo"
  };
  reviewerVote?: "approved" | "rejected" | "waiting" | "none";
  commentCount: number;
}

export interface PRDetail extends PRItem {
  diff: {
    files: FileDiff[];
    totalAdditions: number;
    totalDeletions: number;
    rawContent: string; // full diff text ส่งให้ AI
  };
  threads: ReviewThread[];
}

export interface FileDiff {
  path: string;
  additions: number;
  deletions: number;
  patch: string;
}

export interface ReviewThread {
  id: string;
  status: "active" | "resolved" | "pending";
  comments: {
    author: string;
    body: string;
    createdAt: string;
    filePath?: string;
    line?: number;
  }[];
}
```

### 3.2 Provider Interface

```typescript
// providers/base.ts

export interface GitProvider {
  /** ชื่อ provider สำหรับแสดงใน UI */
  name: string;

  /** ดึง PR list ที่ authenticated user เป็น reviewer */
  listMyReviewerPRs(): Promise<PRItem[]>;

  /** ดึง PR detail + diff + threads */
  getPRDetail(prId: string): Promise<PRDetail>;
}
```

### 3.3 Provider Implementations

#### Azure DevOps

```typescript
// providers/azure.ts

export class AzureProvider implements GitProvider {
  name = "Azure DevOps";

  constructor(
    private config: {
      org: string;
      project: string;
      pat: string;
    },
  ) {}

  private get baseUrl() {
    return `https://dev.azure.com/${this.config.org}/${this.config.project}/_apis`;
  }

  private get headers() {
    const token = Buffer.from(`:${this.config.pat}`).toString("base64");
    return {
      Authorization: `Basic ${token}`,
      "Content-Type": "application/json",
    };
  }

  async listMyReviewerPRs(): Promise<PRItem[]> {
    // GET /_apis/git/pullrequests?reviewerId={myId}&api-version=7.1
    // map response → PRItem[]
  }

  async getPRDetail(prId: string): Promise<PRDetail> {
    // GET /_apis/git/repositories/{repoId}/pullrequests/{prId}
    // GET /_apis/git/repositories/{repoId}/pullrequests/{prId}/iterations/{id}/changes
    // GET /_apis/git/repositories/{repoId}/pullrequests/{prId}/threads
    // map response → PRDetail
  }
}
```

#### GitHub (Stub — implement เมื่อต้องการ)

```typescript
// providers/github.ts

export class GitHubProvider implements GitProvider {
  name = "GitHub";

  constructor(
    private config: {
      token: string; // Personal Access Token หรือ GitHub App token
      owner?: string; // filter by org/user (optional)
    },
  ) {}

  async listMyReviewerPRs(): Promise<PRItem[]> {
    // GET https://api.github.com/search/issues
    //   ?q=is:pr+is:open+review-requested:@me
    // หรือใช้ GraphQL: viewer.pullRequests(states: OPEN)
  }

  async getPRDetail(prId: string): Promise<PRDetail> {
    // GET https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}
    // GET https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}/files
    // GET https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}/reviews
  }
}
```

#### GitLab (Stub)

```typescript
// providers/gitlab.ts

export class GitLabProvider implements GitProvider {
  name = "GitLab";

  constructor(
    private config: {
      token: string;
      baseUrl?: string; // สำหรับ self-hosted instance
      groupId?: string;
    },
  ) {}

  async listMyReviewerPRs(): Promise<PRItem[]> {
    // GET /api/v4/merge_requests?reviewer_id={myId}&state=opened
  }

  async getPRDetail(prId: string): Promise<PRDetail> {
    // GET /api/v4/projects/{projectId}/merge_requests/{iid}
    // GET /api/v4/projects/{projectId}/merge_requests/{iid}/diffs
    // GET /api/v4/projects/{projectId}/merge_requests/{iid}/notes
  }
}
```

#### Bitbucket (Stub)

```typescript
// providers/bitbucket.ts

export class BitbucketProvider implements GitProvider {
  name = "Bitbucket";

  constructor(
    private config: {
      username: string;
      appPassword: string;
      workspace: string;
    },
  ) {}

  async listMyReviewerPRs(): Promise<PRItem[]> {
    // GET https://api.bitbucket.org/2.0/pullrequests/{accountId}
    //   ?role=REVIEWER&state=OPEN
  }

  async getPRDetail(prId: string): Promise<PRDetail> {
    // GET /2.0/repositories/{workspace}/{repo}/pullrequests/{id}
    // GET /2.0/repositories/{workspace}/{repo}/pullrequests/{id}/diff
    // GET /2.0/repositories/{workspace}/{repo}/pullrequests/{id}/comments
  }
}
```

### 3.4 Provider Factory

```typescript
// providers/factory.ts

import { AzureProvider } from "./azure";
import { GitHubProvider } from "./github";
import { GitLabProvider } from "./gitlab";
import { BitbucketProvider } from "./bitbucket";

export function createProvider(config: AppConfig): GitProvider {
  switch (config.provider) {
    case "azure":
      return new AzureProvider({
        org: config.azure.org,
        project: config.azure.project,
        pat: config.azure.pat,
      });
    case "github":
      return new GitHubProvider({ token: config.github.token });
    case "gitlab":
      return new GitLabProvider({
        token: config.gitlab.token,
        baseUrl: config.gitlab.baseUrl,
      });
    case "bitbucket":
      return new BitbucketProvider({ ...config.bitbucket });
    default:
      throw new Error(`Unknown provider: ${config.provider}`);
  }
}
```

---

## 4. Backend Specification

### 4.1 Project Structure

```
backend/
├── src/
│   ├── providers/
│   │   ├── base.ts           # GitProvider interface + types
│   │   ├── factory.ts        # createProvider()
│   │   ├── azure.ts          # AzureProvider (implement ก่อน)
│   │   ├── github.ts         # GitHubProvider (stub)
│   │   ├── gitlab.ts         # GitLabProvider (stub)
│   │   └── bitbucket.ts      # BitbucketProvider (stub)
│   ├── routes/
│   │   ├── prs.ts            # GET /api/prs, GET /api/pr/:id
│   │   └── review.ts         # POST /api/review (SSE)
│   ├── services/
│   │   └── cliRunner.ts      # spawn CLI + stream stdout
│   ├── config.ts             # load .env + validate
│   └── server.ts             # Express app entry point
└── package.json
```

### 4.2 Environment Variables

```bash
# .env

# ── Git Provider ──────────────────────────────────────
PROVIDER=azure          # azure | github | gitlab | bitbucket

# Azure DevOps (ใช้เมื่อ PROVIDER=azure)
AZURE_ORG=your-organization
AZURE_PROJECT=your-project
AZURE_PAT=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# GitHub (ใช้เมื่อ PROVIDER=github)
# GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx

# GitLab (ใช้เมื่อ PROVIDER=gitlab)
# GITLAB_TOKEN=glpat-xxxxxxxxxxxxxxxxxxxx
# GITLAB_BASE_URL=https://gitlab.com        # หรือ self-hosted URL

# Bitbucket (ใช้เมื่อ PROVIDER=bitbucket)
# BITBUCKET_USERNAME=your-username
# BITBUCKET_APP_PASSWORD=xxxxxxxxxxxxxxxxxxxx
# BITBUCKET_WORKSPACE=your-workspace

# ── Server ────────────────────────────────────────────
PORT=3001

# ── AI CLI ────────────────────────────────────────────
DEFAULT_CLI=claude      # claude | opencode | codex | custom

# ── Output ────────────────────────────────────────────
REVIEWS_DIR=./reviews
```

### 4.3 API Endpoints

| Method | Route              | Description                                 |
| ------ | ------------------ | ------------------------------------------- |
| GET    | `/api/prs`         | PR list ที่ user เป็น reviewer              |
| GET    | `/api/pr/:id`      | PR detail + diff + threads                  |
| POST   | `/api/review`      | Stream AI review (SSE: `text/event-stream`) |
| GET    | `/api/config`      | Current provider + CLI config               |
| PUT    | `/api/config`      | Update CLI / provider config                |
| POST   | `/api/review/save` | บันทึก Markdown ลงไฟล์                      |

#### POST /api/review — Request Body

```json
{
  "prId": "4521",
  "cli": "claude",
  "promptTemplate": "default"
}
```

#### SSE Event Format

```
data: {"type": "chunk", "content": "## Summary\n"}

data: {"type": "chunk", "content": "This PR adds..."}

data: {"type": "done", "totalChars": 1842}

data: {"type": "error", "message": "claude: command not found"}
```

### 4.4 CLI Runner

```typescript
// services/cliRunner.ts

interface CLIConfig {
  bin: string;
  args: string[];
}

export const CLI_REGISTRY: Record<string, CLIConfig> = {
  claude: { bin: "claude", args: ["-p"] },
  opencode: { bin: "opencode", args: ["--prompt"] },
  codex: { bin: "codex", args: ["-q"] },
  // เพิ่ม CLI ใหม่ได้ที่นี่ โดยไม่ต้อง refactor
};

export async function runReview(
  prompt: string,
  cliName: string,
  onChunk: (chunk: string) => void,
  onError: (err: string) => void,
): Promise<void> {
  const config = CLI_REGISTRY[cliName];
  if (!config) throw new Error(`Unknown CLI: ${cliName}`);

  const proc = spawn(config.bin, [...config.args, prompt], {
    env: { ...process.env },
  });

  proc.stdout.on("data", (d: Buffer) => onChunk(d.toString()));
  proc.stderr.on("data", (d: Buffer) => onError(d.toString()));

  return new Promise((resolve, reject) => {
    proc.on("close", (code) =>
      code === 0 ? resolve() : reject(new Error(`Exit code: ${code}`)),
    );
    proc.on("error", (err) => {
      if ((err as NodeJS.ErrnoException).code === "ENOENT") {
        reject(
          new Error(`"${cliName}" CLI not found. Please install it first.`),
        );
      } else {
        reject(err);
      }
    });
  });
}
```

---

## 5. Frontend Specification

### 5.1 Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── PRList.tsx          # รายการ PR cards ด้านซ้าย
│   │   ├── PRItem.tsx          # PR card แต่ละใบ
│   │   ├── PRDetail.tsx        # diff viewer + metadata ตรงกลาง
│   │   ├── ReviewPanel.tsx     # streaming Markdown output ด้านขวา
│   │   └── SettingsModal.tsx   # เลือก provider + CLI
│   ├── hooks/
│   │   ├── usePRList.ts        # fetch + cache PR list
│   │   └── useReviewStream.ts  # EventSource SSE hook
│   ├── api/
│   │   └── client.ts           # typed fetch wrapper
│   ├── types/
│   │   └── provider.ts         # shared types (copy จาก backend)
│   └── App.tsx
└── package.json
```

### 5.2 Layout

```
┌──────────────┬──────────────────────────┬──────────────────┐
│  PR List     │      PR Detail           │  Review Output   │
│  (300px)     │      (flex: 1)           │  (400px)         │
│              │                          │                  │
│ ┌──────────┐ │  Title / Author / Branch │  [Review with AI]│
│ │ PR card  │ │  Status badges           │                  │
│ │ #1234    │ │                          │  ## Summary      │
│ └──────────┘ │  Files Changed           │  This PR adds... │
│              │  ┌──────────────────┐    │                  │
│ ┌──────────┐ │  │ diff viewer with │    │  ## Risk         │
│ │ PR card  │ │  │ syntax highlight │    │  ...             │
│ │ #1235    │ │  └──────────────────┘    │                  │
│ └──────────┘ │                          │  [Save .md]      │
│              │  Review Threads          │                  │
│ [Refresh]    │  (collapsed by default)  │                  │
└──────────────┴──────────────────────────┴──────────────────┘
```

### 5.3 UI Behaviors

| Feature           | Behavior                                                 |
| ----------------- | -------------------------------------------------------- |
| PR List refresh   | ปุ่ม Refresh + auto-refresh ทุก 5 นาที                   |
| Loading state     | Skeleton cards ขณะโหลด                                   |
| Streaming output  | แสดง Markdown real-time ผ่าน EventSource                 |
| Stream indicator  | Dot animation "AI is reviewing..." ขณะ stream กำลังทำงาน |
| Save button       | Active หลัง stream สิ้นสุด → บันทึก `PR-{id}-{date}.md`  |
| Error toast       | แสดง error message เมื่อ API หรือ CLI ล้มเหลว            |
| Provider badge    | แสดง logo + ชื่อ provider ปัจจุบันใน header              |
| Settings modal    | เลือก provider, เลือก CLI, แก้ prompt template           |
| Branch display    | Strip `refs/heads/` prefix ก่อนแสดง                      |
| Diff size warning | แจ้งเตือนถ้า diff > 100KB (อาจใช้เวลานาน)                |

### 5.4 useReviewStream Hook

```typescript
// hooks/useReviewStream.ts

export function useReviewStream() {
  const [output, setOutput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const startReview = useCallback((prId: string, cli: string) => {
    setOutput("");
    setDone(false);
    setError(null);
    setStreaming(true);

    const es = new EventSource(`/api/review?prId=${prId}&cli=${cli}`);

    es.onmessage = (e) => {
      const data = JSON.parse(e.data);
      if (data.type === "chunk") setOutput((prev) => prev + data.content);
      if (data.type === "done") {
        setDone(true);
        setStreaming(false);
        es.close();
      }
      if (data.type === "error") {
        setError(data.message);
        setStreaming(false);
        es.close();
      }
    };

    es.onerror = () => {
      setError("Connection lost");
      setStreaming(false);
      es.close();
    };
  }, []);

  return { output, streaming, done, error, startReview };
}
```

---

## 6. AI CLI Layer

### 6.1 Prompt Template

ส่งให้ AI CLI เป็น plain text prompt:

```
You are a senior software engineer conducting a code review.

## Pull Request
Title: {pr.title}
Author: {pr.author.name}
Repository: {pr.repository.fullName}
Branch: {pr.sourceBranch} → {pr.targetBranch}
Description:
{pr.description}

## Changes
{pr.diff.totalAdditions} additions, {pr.diff.totalDeletions} deletions across {fileCount} files

## Diff
{pr.diff.rawContent}

## Existing Review Comments
{threads}

---

Please provide a structured code review in Markdown with these sections:
1. **Summary** — what this PR does in 2-3 sentences
2. **Risk Assessment** — bugs, security issues, performance concerns
3. **Code Quality** — readability, patterns, naming conventions
4. **Suggestions** — specific actionable items with file/line references
5. **Verdict** — one of: ✅ Approve | ⚠️ Request Changes | 💬 Needs Discussion

Respond ONLY in Markdown. Be specific and constructive.
```

### 6.2 Supported CLIs

| CLI        | Install                                      | Auth                     |
| ---------- | -------------------------------------------- | ------------------------ |
| `claude`   | `npm install -g @anthropic-ai/claude-code`   | `claude login`           |
| `opencode` | ดูที่ opencode.ai/docs                       | ตั้ง API key ใน config   |
| `codex`    | `npm install -g @openai/codex`               | `OPENAI_API_KEY` env var |
| custom     | ใส่ path ใน `CLI_REGISTRY` ใน `cliRunner.ts` | ขึ้นกับ CLI นั้น         |

### 6.3 Diff Size Limit

ก่อนส่ง prompt ให้ตรวจสอบขนาด diff:

```typescript
const MAX_DIFF_CHARS = 80_000; // ~80KB — ปรับได้ตาม context window ของ CLI ที่ใช้

if (detail.diff.rawContent.length > MAX_DIFF_CHARS) {
  detail.diff.rawContent =
    detail.diff.rawContent.slice(0, MAX_DIFF_CHARS) +
    "\n\n[...diff truncated — showing first 80KB...]";
}
```

---

## 7. Markdown Output Format

### 7.1 File Naming

```
./reviews/{provider}-PR-{id}-{repo}-{YYYY-MM-DD}.md

# ตัวอย่าง:
./reviews/azure-PR-4521-backend-api-2025-06-04.md
./reviews/github-PR-892-frontend-2025-06-04.md
```

### 7.2 File Structure

```markdown
# PR Review: {title}

> **{provider} PR #{id}** | `{repo}` | `{sourceBranch}` → `{targetBranch}`
> **Author:** {author} | **Reviewed:** {datetime} | **CLI:** {cliUsed}

---

## Summary

...

## Risk Assessment

| Risk | Severity            | Description |
| ---- | ------------------- | ----------- |
| ...  | High / Medium / Low | ...         |

## Code Quality

...

## Suggestions

...

## Verdict

> ✅ Approve / ⚠️ Request Changes / 💬 Needs Discussion

---

_Generated by PR Reviewer — {provider} — {datetime}_
```

---

## 8. Setup Guide

### 8.1 Prerequisites

- Node.js >= 22 prefer 24, npm >= 10 prefer 11
- Git provider credentials (เริ่มที่ Azure DevOps PAT)
- อย่างน้อยหนึ่ง AI CLI ติดตั้งและ authenticate แล้ว

### 8.2 Installation

```bash
# Clone
git clone <repo-url>
cd pr-reviewer

# Install dependencies
cd backend  && npm install
cd ../frontend && npm install

# สร้าง .env
cp .env.example .env
# แก้ PROVIDER, AZURE_ORG, AZURE_PROJECT, AZURE_PAT

# สร้าง output directory
mkdir -p reviews

# Start dev
cd backend  && npm run dev   # http://localhost:3001
cd frontend && npm run dev   # http://localhost:5173
```

### 8.3 Getting Azure PAT

1. ไปที่ Azure DevOps → **User Settings** → **Personal Access Tokens**
2. คลิก **+ New Token**
3. Scopes → Custom defined:
   - **Code:** Read
   - **Pull Request Threads:** Read & Write
4. Copy token → ใส่ใน `.env` ที่ `AZURE_PAT`

> หา Reviewer ID ของตัวเองได้จาก:
> `GET https://vssps.dev.azure.com/{org}/_apis/profile/profiles/me?api-version=7.1`

### 8.4 เพิ่ม Provider ใหม่

1. สร้างไฟล์ `backend/src/providers/{name}.ts` implement `GitProvider` interface
2. เพิ่ม case ใน `factory.ts`
3. เพิ่ม env vars ใน `.env.example`
4. เพิ่ม option ใน `SettingsModal.tsx`

ไม่ต้องแตะ routes, cliRunner, หรือ frontend logic อื่นใดเลย

---

## 9. Implementation Order

แนะนำให้ implement ตามลำดับนี้เพื่อให้ทดสอบได้ทุก step:

```
Step 1: Project bootstrap
  └─ สร้าง folder structure, tsconfig, package.json ทั้ง frontend + backend

Step 2: Azure Provider
  └─ azureClient.ts → listMyReviewerPRs() และ getPRDetail() ทำงานได้

Step 3: Backend routes
  └─ GET /api/prs และ GET /api/pr/:id คืนข้อมูลได้

Step 4: CLI Runner
  └─ spawn CLI process และ pipe stdout ออกมาได้

Step 5: SSE streaming
  └─ POST /api/review stream ผ่าน text/event-stream ได้

Step 6: Frontend — PR List
  └─ PRList.tsx ดึงและแสดง PR cards ได้

Step 7: Frontend — Review Panel
  └─ ReviewPanel.tsx + useReviewStream hook แสดง streaming output ได้

Step 8: Settings Modal
  └─ เลือก CLI, เปลี่ยน provider config ได้

Step 9: Save to file
  └─ POST /api/review/save บันทึก .md ลง ./reviews/ ได้

Step 10: GitHub Provider (ถ้าต้องการ)
  └─ implement GitHubProvider stub ให้ครบ
```

---

## 10. Pitfalls & Notes

### Backend

- **CORS** — enable สำหรับ `http://localhost:5173` ใน development
- **SSE headers** — ต้องตั้งครบ:
  ```
  Content-Type: text/event-stream
  Cache-Control: no-cache
  Connection: keep-alive
  ```
- **Azure auth** — ใช้ Basic auth: `Buffer.from(':' + PAT).toString('base64')`
- **Branch prefix** — Azure ส่ง `refs/heads/feature/xxx` ให้ strip ออกก่อนแสดงและส่งให้ AI
- **CLI not found** — ตรวจ `ENOENT` error และส่ง message ที่ชัดเจน เช่น `"claude CLI not found. Run: npm install -g @anthropic-ai/claude-code"`

### Frontend

- **EventSource** — ใช้ native browser EventSource สำหรับ SSE ไม่ต้องติดตั้ง library เพิ่ม
- **Markdown rendering** — ใช้ `react-markdown` + `react-syntax-highlighter` สำหรับ code blocks ใน output
- **Large diff warning** — แสดง banner เตือนเมื่อ diff > 100KB ก่อนกด Review

### Provider Design

- **ทุก adapter ต้อง strip branch prefix** เช่น `refs/heads/` (Azure), `refs/pull/` (GitHub) ก่อน map เข้า `PRItem`
- **Pagination** — Azure และ GitHub มี pagination ต้อง handle สำหรับ org ที่มี PR จำนวนมาก
- **Rate limiting** — GitHub มี rate limit 5000 req/hr สำหรับ PAT, ควร cache PR list ใน memory

### Recommended Packages

| Package                    | Layer    | Purpose                                |
| -------------------------- | -------- | -------------------------------------- |
| `axios`                    | Backend  | HTTP client สำหรับ Provider APIs       |
| `dotenv`                   | Backend  | Load .env                              |
| `cors`                     | Backend  | CORS middleware                        |
| `react-markdown`           | Frontend | Render Markdown output                 |
| `react-syntax-highlighter` | Frontend | Syntax highlight code ใน diff + output |
| `@tanstack/react-query`    | Frontend | Data fetching + cache                  |
| `lucide-react`             | Frontend | Icons                                  |
| `date-fns`                 | Frontend | Format dates                           |

---

_PR Reviewer Spec v1.0 — June 2025_
