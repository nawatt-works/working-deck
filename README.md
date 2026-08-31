# Working Deck

Workspace starter สำหรับทำงานร่วมกันระหว่างมนุษย์กับ agent harness หลายตัวบนหลาย Git repositories โดยมี `_Mission-Control/` เป็นศูนย์กลางของบริบท กฎร่วม และ tooling ระดับ workspace

Working Deck ไม่ใช่ application และไม่บังคับ workflow เช่น planning, handoff หรือ repository catalog ล่วงหน้า ความสามารถใหม่ควรถูกเพิ่มใน Mission Control เมื่อมีงานจริงต้องใช้เท่านั้น

## โครงสร้าง

```text
.
├── AGENTS_EXAMPLE.md             # instruction template แบบ inert
├── GIT_POLICY.md                 # กฎ Git safety กลาง
├── README.md
├── .gitignore                    # root Git ignore ทุกอย่างใต้ repos/
├── .ignore                       # ทำให้ค้นจาก root แล้วเห็นโค้ดใต้ repos/
├── _Mission-Control/
│   ├── README.md                 # landing page ของ Mission Control
│   ├── git-safety.yaml           # own-repository allowlist
│   ├── hooks/pre-push            # hook template
│   └── tooling/git_guard.py      # status และ hook installer
└── repos/                        # independent Git repositories/worktrees
```

## `AGENTS_EXAMPLE.md`

ไฟล์นี้ตั้งใจใช้ชื่อที่ agent harness ไม่ auto-load เพื่อให้สามารถพัฒนา Working Deck ได้โดยไม่เผลอรับ instructions ของ workspace ปลายทาง

ผู้ใช้เป็นผู้ rename หรือสร้าง symlink เป็น `AGENTS.md`, `CLAUDE.md` หรือชื่ออื่นตาม discovery mechanism ของ harness ที่ใช้งาน Working Deck จะไม่สร้างหรือเปลี่ยน symlink เหล่านี้เอง

## `repos/`

ทุก direct child ใต้ `repos/` ต้องเป็น Git working tree หรือ linked worktree ที่เป็นอิสระจาก root Git repository:

```text
repos/customer-api/
repos/customer-web/
repos/my-tools/
```

root Git ignore `repos/*` ทั้งหมด จึงไม่เกิด gitlink และไม่ผสม history, branch, staging area หรือ tooling ของ work repositories เข้ากับ Working Deck

ใช้ `rg` หรือ `fd` ค้นจาก workspace root ได้ตามปกติ เพราะ `.ignore` เปิดให้ search tools มองเห็น `repos/*` โดยไม่เปลี่ยนพฤติกรรมของ Git

## Git safety model

Repository ทุกแห่งใต้ `repos/` ถูกจัดเป็น `client` โดยอัตโนมัติ ซึ่งหมายถึงห้ามเขียนขึ้น remote ทุกกรณี

Repository ของผู้ใช้ที่อนุญาตให้ push ได้ต้องถูกเพิ่มใน `_Mission-Control/git-safety.yaml` อย่างชัดเจน:

```yaml
schema_version: 1
default_class: client

own_repositories:
  - repos/my-tools
```

กฎของแต่ละ class อยู่ใน `GIT_POLICY.md` การอยู่ใน `own_repositories` ไม่ใช่คำสั่งให้ push แต่หมายความว่าสามารถ push แบบปกติได้เมื่อผู้ใช้สั่งและ workflow ของ repository อนุญาต

linked worktree ที่ใช้ Git common directory เดียวกับ path ที่เป็น `own` จะสืบทอด class เดียวกัน ส่วน clone แยกที่มี `.git` คนละชุดต้องเพิ่ม allowlist แยก

## ตรวจ workspace

```bash
python3 _Mission-Control/tooling/git_guard.py status
```

คำสั่งนี้ตรวจ:

- direct child ทุกแห่งเป็น Git working tree จริง
- path ใน own allowlist ยังมีอยู่และถูกต้อง
- class ของแต่ละ repository
- branch, pending changes และ upstream mismatch
- coordination artifacts ที่กำลังจะหลุดเข้า work repository
- สถานะของ optional pre-push guard

## ติดตั้ง pre-push guard

ติดตั้งให้ทุก repository:

```bash
python3 _Mission-Control/tooling/git_guard.py install
```

หรือติดตั้งเฉพาะแห่ง:

```bash
python3 _Mission-Control/tooling/git_guard.py install repos/customer-api
```

Guard ทำงานที่ระดับ Git จึงใช้กับ Pi, Codex, Claude, terminal และ Git client อื่นเหมือนกัน โดย:

- บล็อกทุก push จาก `client`
- บล็อก remote ref deletion
- บล็อก branch-name mismatch และ non-fast-forward update
- บล็อกการย้าย remote tag เดิม

Installer ไม่เขียนทับ pre-push hook หรือ `core.hooksPath` ที่ repository มีอยู่แล้ว

Hook เป็นเพียง accident guard เพราะข้ามได้ด้วย `--no-verify` และป้องกัน local destructive commands ไม่ได้ read-only credentials กับ server-side permissions จึงยังเป็น hard security boundary ที่ควรใช้กับ repositories ของลูกค้า

## การเพิ่ม repository

1. Clone หรือสร้าง linked worktree เป็น direct child ใต้ `repos/`
2. ถือว่าเป็น `client` จนกว่าผู้ใช้จะยืนยันว่าเป็น repository ของตน
3. หากเป็น `own` ให้เพิ่ม path ใน `_Mission-Control/git-safety.yaml`
4. รัน `git_guard.py status`
5. ติดตั้ง pre-push guard หากไม่ชนกับ hook เดิม

Working Deck ไม่แก้ไฟล์ภายใน work repository เพื่อ onboarding และไม่เก็บ remote URL, credentials หรือ repository catalog

## ตรวจ automated tests

```bash
python3 -m unittest discover -s _Mission-Control/tooling/tests
```
