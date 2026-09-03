# Working Deck

Workspace starter สำหรับทำงานร่วมกันระหว่างมนุษย์กับ agent harness หลายตัวบนหลาย Git repositories โดยมี `_Mission-Control/` เป็นศูนย์กลางของบริบท กฎร่วม และ tooling ระดับ workspace

Working Deck ไม่ใช่ application และไม่บังคับ workflow เช่น planning, handoff หรือ repository catalog ล่วงหน้า ความสามารถใหม่ควรถูกเพิ่มใน Mission Control เมื่อมีงานจริงต้องใช้เท่านั้น

## โครงสร้าง

```text
.
├── AGENTS_EXAMPLE.md             # instruction template แบบ inert
├── GIT_POLICY.md                 # กฎ Git safety สำหรับ agents
├── README.md
├── .gitignore                    # ป้องกัน nested repositories จาก root Git
├── .ignore                       # ทำให้ search tools เห็น source ที่ root Git ignore
├── _Mission-Control/
│   ├── README.md                 # landing page ของ Mission Control
│   ├── git-safety.yaml           # registry และ class ของ work repositories
│   └── tooling/git_safety.py     # ตรวจ registry และ repository state
└── repos/                        # ตำแหน่งปกติที่เลือกใช้ได้ ไม่ใช่ข้อบังคับ
```

## `AGENTS_EXAMPLE.md`

ไฟล์นี้ตั้งใจใช้ชื่อที่ agent harness ไม่ auto-load เพื่อให้พัฒนา Working Deck ได้โดยไม่เผลอรับ instructions ของ workspace ปลายทาง

ผู้ใช้เป็นผู้ rename หรือสร้าง symlink เป็น `AGENTS.md`, `CLAUDE.md` หรือชื่ออื่นตาม discovery mechanism ของ harness ที่ใช้งาน Working Deck จะไม่สร้างหรือเปลี่ยน symlink เหล่านี้เอง

## ตำแหน่งของ work repositories

Repository วางที่ใดก็ได้ภายใน workspace ยกเว้นใต้ `_Mission-Control/` โดย `repos/` เป็นเพียง default convention สำหรับกรณีที่ไม่มีข้อกำหนดด้าน layout

รองรับทั้งแบบไม่แบ่งกลุ่ม:

```text
repos/order-api/
repos/customer-web/
```

แบบแบ่งกลุ่ม:

```text
repos/customer-a/api/
repos/customer-a/web/
repos/internal/my-tools/
```

และ path ที่อยู่นอก `repos/`:

```text
clients/acme/legacy-api/
internal-tools/release-cli/
```

Grouping folder ไม่มี `.git` และไม่ต้องลงทะเบียน ตัว repository จริงต้องเป็น Git top-level working tree หรือ linked worktree ห้ามใช้ symlink แทน repository path

Git Safety ค้น repository แบบ recursive ทั่ว workspace โดยข้าม `_Mission-Control/` และหยุดค้นลึกเมื่อพบ Git repository หนึ่งแห่ง จึงไม่ตีความ source folders ภายใน repository เป็น workspace repositories

## Git safety registry

ทุก work repository ต้องลงทะเบียนใน `_Mission-Control/git-safety.yaml` ด้วย exact workspace-relative path และ class:

```yaml
schema_version: 1
default_class: client

repositories:
  - path: repos/customer-a/api
    class: client

  - path: repos/internal/my-tools
    class: own

  - path: internal-tools/release-cli
    class: own
```

- `client` — repository ของลูกค้าหรือบุคคลอื่น Agents ห้ามเขียนขึ้น remote
- `own` — repository ของผู้ใช้ Agents push แบบปกติได้เมื่อผู้ใช้สั่งและ workflow ของ repository อนุญาต
- Repository ที่ค้นพบแต่ยังไม่ลงทะเบียนถูกถือเป็น `client` และ `status` รายงาน error
- รายการที่ยังไม่มี checkout บนเครื่องปัจจุบันถูกเก็บไว้และรายงาน warning
- linked worktree ที่ไม่ได้ลงทะเบียนแยกจะสืบทอด class จาก registered path ที่ใช้ Git common directory เดียวกัน

Registry นี้มีหน้าที่เฉพาะ Git safety ไม่มี `repo_id`, remote URL, description, integrations หรือ metadata สำหรับระบบอื่น

## ขอบเขตของการป้องกัน

Git safety ในรุ่นนี้เป็น **policy และ validation สำหรับ agent harness** ไม่ได้ติดตั้ง Git hook และไม่ขัดขวางการใช้ Git, Git GUI หรือการ push ที่ผู้ใช้ทำเอง

การป้องกันขึ้นกับ agent ที่โหลด `AGENTS_EXAMPLE.md` ผ่านชื่อหรือ symlink ที่ผู้ใช้จัดเตรียมและปฏิบัติตาม `GIT_POLICY.md` ส่วน technical enforcement ระดับ agent อาจเพิ่มภายหลังด้วย extension ของแต่ละ harness

`git_safety.py` ตรวจและรายงานสถานะ แต่ไม่ intercept หรือบล็อกคำสั่ง Git

## ป้องกัน root Git จาก nested repositories

ถ้า workspace root เป็น Git repository ทุก work repository ต้องถูก root ignore มิฉะนั้นการ `git add` อาจสร้าง gitlink

`repos/*` ถูก ignore เป็นค่าเริ่มต้น ส่วน repository ที่อยู่นอก `repos/` ให้เพิ่ม exact path:

```gitignore
/clients/acme/legacy-api/
/internal-tools/release-cli/
```

หากต้องการค้น source จาก workspace root ให้เพิ่ม path เดียวกันแบบ negation ใน `.ignore`:

```gitignore
!/clients/acme/legacy-api/
!/internal-tools/release-cli/
```

Git Safety ตรวจ root ignore ให้ แต่ไม่แก้ `.gitignore` หรือ `.ignore` อัตโนมัติ

## ตรวจ workspace

```bash
python3 _Mission-Control/tooling/git_safety.py status
```

คำสั่งนี้ตรวจ:

- registry syntax, paths และ classes
- registered checkout, missing checkout และ unregistered repositories
- repository path เป็น Git top-level จริงและไม่ใช่ symlink
- root Git ignore nested repository ทุกแห่ง
- branch, pending changes และ upstream mismatch
- coordination artifacts ที่ agent ควรตรวจทานก่อน commit

## การเพิ่ม repository

1. Clone หรือสร้าง linked worktree ใน path ที่ project ต้องการ
2. เพิ่ม exact path และ class ใน `_Mission-Control/git-safety.yaml`
3. ถ้า root workspace เป็น Git ให้เพิ่ม exact path ใน `.gitignore`; `repos/*` มีค่าเริ่มต้นให้แล้ว
4. เพิ่ม negation ใน `.ignore` เมื่อต้องการค้นจาก workspace root
5. รัน `git_safety.py status`

Working Deck ไม่แก้ source หรือ repository-owned configuration เพื่อ onboarding และไม่เก็บ credentials

## ตรวจ automated tests

```bash
python3 -m unittest discover -s _Mission-Control/tooling/tests
```
