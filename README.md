# Working Deck

Workspace สำหรับทำงานร่วมกันระหว่างมนุษย์กับ AI บนหลาย Git repositories โดยแยก metadata และ coordination contracts ออกจาก source code ของแต่ละ repository อย่างชัดเจน

root repository นี้ทำหน้าที่เป็น control plane สำหรับเก็บแนวทางการทำงาน เครื่องมือ และ workspace-level metadata ที่ใช้ร่วมกับ AI ส่วนตัวงานจริงและ supporting repositories อยู่ใน `repos/` ซึ่งส่วนใหญ่เป็น Git repository อิสระจาก root workspace แต่บางโฟลเดอร์อาจถูก track ไปกับ root ได้

Working Deck เป็น workspace starter สำหรับนำโครงสร้างและไฟล์ที่จำเป็นไปใช้เป็นฐานของ project อื่น ไม่ใช่ application project

## เริ่ม Project ใหม่

1. คัดลอกไฟล์และโฟลเดอร์ของ Working Deck ที่ต้องใช้ไปยัง project ใหม่ โดยไม่เอา `.git` และไฟล์ local ที่ไม่เกี่ยวข้องไปด้วย
2. ใช้ `$bootstrap-project-workspace` ตอบคำถามเกี่ยวกับ project แล้ว skill จะเปลี่ยน `AGENTS_EXAMPLE.md` เป็น `AGENTS.md` พร้อมบันทึก default repository class
3. ใช้ `$add-workspace-repository` ทีละ repository เมื่อมี repository เข้ามา ทั้งตอนเริ่มและระหว่างพัฒนา
4. ตรวจผลด้วย `python3 tooling/repos_status.py`

ขั้นที่ 2 เก็บเฉพาะ posture ของ project ไม่ใช่รายชื่อ repository เพราะตอนเริ่มมักยังไม่รู้ว่าจะมี repository อะไรบ้าง และ repository จะทยอยเพิ่มระหว่างพัฒนา

Catalog ใน starter เริ่มด้วย `repositories: []` ซึ่งเป็นค่าที่ถูกต้อง ส่วนตัวอย่าง schema อยู่ในเอกสารและ skill เพื่อไม่ให้ AI เข้าใจ mock repository ว่าเป็นสมาชิกจริงของ project ใหม่

## Skills

แยก workflow เป็นสาม skills โดยสองตัวแรกเป็น workflow ที่ผู้ใช้เรียกโดยตรง ส่วนตัวสุดท้ายเป็นขั้นตอนย่อยที่ถูกเรียกต่อ

- `bootstrap-project-workspace` ใช้ครั้งเดียวต่อ project หลังคัดลอก starter เพื่อถามข้อมูลของ project แล้ว generate `AGENTS.md` พร้อม default repository class
- `add-workspace-repository` ใช้ทุกครั้งที่เพิ่ม repository เพื่อจัดการ `.gitignore`, repository class และ catalog ให้สอดคล้องกันในคราวเดียว
- `manage-repository-catalog` ใช้ค้นหาและ sync direct child repositories รวมถึงสร้าง เพิ่ม ลบ หรือแก้ authoritative Repository Catalog โดยไม่ตัดสิน access, indexing หรือ integrations

ตัวอย่างคำขอ:

```text
ใช้ $bootstrap-project-workspace ตั้งค่า workspace สำหรับ project นี้
ใช้ $add-workspace-repository เพิ่ม order-api เข้า workspace
ใช้ $manage-repository-catalog sync catalog กับ repos/ ที่มีอยู่
```

## แนวทางการทำงานประจำวัน

1. ตรวจ `workspace-meta/repositories.yaml` เพื่อหา `repo_id` และ path ของ repository เป้าหมาย
2. ค้นหาโค้ดจาก workspace root ได้โดยตรง แต่ต้องเปลี่ยน working directory เข้า repository ก่อนเรียก Git, test runner หรือ build
3. ใช้ `workspace-meta/` เฉพาะ metadata หรือ contract กลางของ workspace ส่วน artifact ของ harness ให้เก็บตาม convention ของ harness นั้น และไฟล์ชั่วคราวให้ใช้ temporary directory ของ harness หรือระบบ
4. ตรวจ Git status ภายใน repository เป้าหมายก่อน commit
5. รัน `python3 tooling/repos_status.py` ก่อน commit ใน repository ภายนอก และเมื่อจบงานที่แก้หลาย repository

แนวทางฉบับเต็มที่ AI อ่านอยู่ใน `AGENTS_EXAMPLE.md` ซึ่งจะกลายเป็น `AGENTS.md` หลัง bootstrap

## โครงสร้าง Workspace

```text
.
├── AGENTS_EXAMPLE.md        # template ของ workspace instructions
├── GIT_POLICY.md            # Git push safety policy แยกตาม repository class
├── README.md
├── .ignore                  # ให้เครื่องมือค้นหามองเห็น repos/ ที่ Git ignore
├── .agents/
│   └── skills/              # skills ที่เป็นของ root workspace
├── workspace-meta/
│   ├── README.md            # กติกาของ workspace metadata กลาง
│   ├── repositories.yaml    # Repository Catalog instance
│   ├── handoff/             # งานที่ส่งต่อระหว่าง producer ต่าง role
│   └── contracts/           # shared contracts สำหรับ consumers
├── repos/                   # workspace repositories
└── tooling/                 # automation สำหรับดูแล root workspace
```

### `workspace-meta/`

เก็บ metadata และ contract กลางที่ Working Deck เป็นเจ้าของเอง เช่น Repository Catalog, handoff contract และ contract อื่นที่ต้องให้หลาย harness หรือ automation อ้างร่วมกัน

ข้อมูลในพื้นที่นี้เป็นของ root workspace และต้องไม่ถูกคัดลอกหรือ commit เข้า external repositories โดยอัตโนมัติ

`workspace-meta/` ไม่ใช่พื้นที่บังคับสำหรับ notes, plans, prompts หรือ artifact ทั้งหมดที่ AI สร้างขึ้น หาก harness ใดมีตำแหน่งและ format ของตัวเอง เช่น `.agents/`, `.claude/`, `.cursor/` หรือ `.my-harness/` ให้ใช้ convention ของ harness นั้นได้ และให้ producer อื่นอ่านจากตำแหน่งนั้นตาม contract/convention ของเจ้าของ artifact

### `workspace-meta/handoff/`

พื้นที่ส่งต่องานระหว่าง producer ที่ทำหน้าที่ต่างกัน เช่น ตัวที่ออกแบบและวางแผน ตัวที่ implement และตัวที่ตรวจสอบผล ใช้เมื่อรู้ว่างานจะข้าม producer เท่านั้น ส่วนงานที่ทำจบในตัวเองให้ใช้ตำแหน่ง artifact ตาม convention ของ harness หรือ workflow นั้น

เอกสารส่งต่อถูกเขียนให้คนอื่นเอาไปทำต่อ เจ้าของจึงเป็นตัวงานไม่ใช่ผู้เขียน สิทธิ์เขียนจึงกำหนดด้วย stage — หนึ่งหน่วยงานคือหนึ่งโฟลเดอร์ `<work_id>/` ภายในมีไฟล์ `<NN>-<stage>.md` ที่แต่ละไฟล์มีผู้เขียนได้ role เดียว

`status` ใน frontmatter เป็นตัวบอกว่า producer ตัวถัดไปลงมือทำตามได้หรือยัง มีเฉพาะ `ready` เท่านั้นที่ทำตามได้ กติกาทั้งหมดอยู่ใน `workspace-meta/handoff/README.md` และรูปแบบไฟล์อยู่ใน `workspace-meta/contracts/handoff/`

พื้นที่นี้เป็นสายพาน ไม่ใช่คลังประวัติ เมื่องานจบให้ย้ายเฉพาะสิ่งที่ยังมีผลบังคับต่อออกไปเก็บที่อื่น แล้วลบโฟลเดอร์หน่วยงานนั้นได้

### `repos/`

เก็บ Git repositories ที่เป็นตัวงานจริงหรือสนับสนุนการทำงาน เช่น application, library, documentation, test environment, agent skill, extension หรือ automation และอาจเป็น repository ของลูกค้า ทีมภายนอก หรือผู้ใช้เอง

repository แต่ละแห่งอาจเป็น single-project repository หรือ monorepo ที่มีหลาย applications, services, packages หรือ libraries อยู่ภายในก็ได้ การอยู่ใต้ `repos/` บอกเพียง Git boundary ระดับ workspace ไม่ได้บอกรูปแบบโครงสร้างภายใน repository ดังนั้นต้องตรวจ configuration และ documentation ของ repository เป้าหมายก่อนทำงานเสมอ

root Git repository ignore เนื้อหาภายใต้ `repos/` เป็นค่าเริ่มต้น เพื่อไม่ให้ repository ที่มี `.git` ของตัวเองถูก commit เข้า root ซึ่งจะกลายเป็น gitlink ที่ clone แล้วได้โฟลเดอร์ว่าง

บาง project มีโฟลเดอร์ใต้ `repos/` ที่ไม่มี Git ของตัวเองและควรถูก commit ไปกับ root workspace กรณีนี้ให้ opt-in ทีละรายการด้วย `!repos/<ชื่อโฟลเดอร์>/` ใน `.gitignore` ทั้งสองแบบเป็นสถานะที่ถูกต้อง รายละเอียดอยู่ในหัวข้อการติดตามสถานะ

ในเอกสารของ workspace นี้ คำว่า **workspace repository** หรือ **repo** หมายถึง direct child directory ใต้ `repos/` ส่วน **cataloged repository** หมายถึง repo ที่มีรายการอยู่ใน `workspace-meta/repositories.yaml`

คำว่า repository ที่พบภายใน source code เช่น repository pattern, data repository, `Repository<T>` หรือ class ที่ลงท้ายด้วย `Repository` เป็นแนวคิดภายในตัวงาน ไม่ถือเป็น workspace repository หรือ cataloged repository

### `tooling/`

เก็บ automation ที่ดูแล root workspace เครื่องมือในพื้นที่นี้ต้องไม่เขียนไฟล์ลง `repos/*` เว้นแต่ผู้ใช้ร้องขอให้แก้ตัวงานใน repository นั้นอย่างชัดเจน

- `validate_repository_catalog.py` ตรวจ workspace-level Repository Catalog contract และความครบถ้วนของ direct child ใต้ `repos/`
- `repos_status.py` รายงานสถานะ Git ของทุก repository ตรวจ tracking state และเตือนเมื่อพบ coordination artifact ค้างอยู่ใน change set ของ repository ภายนอก
- `validate_handoff.py` ตรวจเอกสารใน `workspace-meta/handoff/` ว่าชื่อหน่วยงาน ชื่อไฟล์ stage และ frontmatter ตรงกันและอ้าง `repo_id` ที่มีอยู่จริง
- `repository_catalog.py` และ `handoff.py` เป็น dependency-free contract parser และ validation library ที่ tooling อื่นนำไปใช้ร่วมกันได้

## Repository Catalog

ไฟล์ `workspace-meta/repositories.yaml` เป็น authoritative catalog ของ repositories ทั้งหมดที่เป็นสมาชิกของ project workspace และเป็นจุดอ้างอิงกลางสำหรับ automation กับ knowledge files อื่น:

```yaml
schema_version: 1

repositories:
  - repo_id: repo_order_api
    path: repos/order-api
```

ความหมายของแต่ละ field:

- `schema_version` — version ของ catalog schema ปัจจุบันต้องเป็น `1`
- `repo_id` — stable identity ที่ไม่ซ้ำในรูปแบบ `repo_<snake_case_name>` สำหรับให้ไฟล์อื่นอ้างอิง
- `path` — relative path ที่ไม่ซ้ำและต้องเป็น direct child ภายใต้ `repos/`

schema version 1 รองรับเฉพาะ `repo_id` และ `path` เพื่อให้ catalog เก็บเฉพาะ identity กับข้อเท็จจริงที่ค่อนข้างคงที่ นิยาม contract, machine-readable schema และ compatibility rules อยู่ที่ `workspace-meta/contracts/repository-catalog/`

Catalog ดูแลเรื่องสมาชิกภาพอย่างเดียว ไม่ตัดสินว่า repository นั้นมี Git ของตัวเองหรือไม่ AI มีสิทธิ์เข้าถึงแค่ไหน ต้องถูก index หรือไม่ หรือเป็น application source code หรือเปล่า repository ที่เป็น test environment, documentation, agent skill หรือ extension จึงอยู่ใน catalog ได้

กฎสองข้อที่ตรงข้ามกันและต้องแยกให้ออก:

- `repos/` มีไว้สำหรับสมาชิกของ project workspace เท่านั้น **direct child directory ทุกแห่งต้องมีรายการใน catalog** หากพบ directory ที่ไม่มีรายการ ให้ถือว่า Catalog drift และเพิ่มเข้า catalog
- **cataloged repository อาจยังไม่มี checkout บนเครื่องปัจจุบันได้** เช่น ยังไม่ได้ clone เครื่องมือจะแจ้ง warning แต่ห้ามลบรายการนั้นโดยอัตโนมัติ เพราะ Catalog อธิบาย project workspace ไม่ใช่เฉพาะสิ่งที่มีอยู่บนเครื่องหนึ่งเครื่อง

## การติดตามสถานะ Repositories

`git status` ที่ workspace root ตอบไม่ได้ว่างานใน `repos/` ถูกบันทึกแล้วหรือยัง เพราะเนื้อหาใต้ `repos/` ถูก ignore ใช้คำสั่งนี้แทน:

```bash
python3 tooling/repos_status.py
```

เครื่องมือนี้รายงานสถานะ Git ของทุก repository พร้อมตรวจสองอย่างที่ root มองไม่เห็น

**tracking state** — repository แต่ละแห่งต้องอยู่ในสถานะใดสถานะหนึ่งที่ถูกต้อง

| มี `.git` ของตัวเอง | root ignore | สถานะ | ผลลัพธ์ |
| --- | --- | --- | --- |
| ใช่ | ใช่ | `external` | ถูกต้อง |
| ไม่ | ไม่ | `internal` | ถูกต้อง |
| ใช่ | ไม่ | `gitlink` | error — commit แล้วจะได้ gitlink ที่ clone มาว่างเปล่า |
| ไม่ | ใช่ | `untracked` | error — งานไม่ถูก track ทั้งใน root และในตัวมันเอง |

สถานะ `untracked` เป็นเหตุผลหลักที่ต้องมีเครื่องมือนี้ เพราะโฟลเดอร์ที่ไม่มี Git ของตัวเองและถูก root ignore คืองานที่มีอยู่บนเครื่องปัจจุบันเพียงที่เดียวโดยไม่มี version control ใดรองรับ และไม่มีสัญญาณใดแจ้งเตือนตามปกติ

การตัดสิน tracking state เป็นหน้าที่ของเครื่องมือนี้เท่านั้น เพราะต้องดู `.gitignore` ประกอบด้วย `validate_repository_catalog.py` จึงไม่ตัดสินเรื่องนี้และไม่เตือนเมื่อ repository ไม่มี `.git`

**coordination artifact ที่รั่วออก** — สแกน change set ที่ยัง pending ในแต่ละ repository ภายนอกเพื่อหาไฟล์อย่าง `AGENTS.md`, `CLAUDE.md`, `.agents/`, `.claude/` และ `workspace-meta/` ที่กำลังจะถูก commit เข้า repository ของผู้อื่น

ตรวจเฉพาะไฟล์ที่ยัง pending โดยตั้งใจ ไฟล์ที่ commit ไปแล้วถือเป็นทรัพย์สินของ repository นั้น เช่น AI harness configuration ที่ทีมเจ้าของใช้งานอยู่ ซึ่งไม่ใช่การรั่วไหล

## การค้นหาโค้ดจาก Workspace Root

`rg` และ `fd` เคารพ `.gitignore` โดยปริยาย การค้นหาจาก root จึงเคยคืนผลว่างสำหรับโค้ดที่อยู่ใน `repos/` โดยไม่แจ้ง error ซึ่งอ่านได้ว่า "ไม่มีโค้ดนี้" ทั้งที่มีอยู่

ไฟล์ `.ignore` ที่ workspace root แก้ปัญหานี้ เครื่องมือค้นหาอ่าน `.ignore` ด้วย priority สูงกว่า `.gitignore` ทำให้ค้นจาก root แล้วเห็นเนื้อหาใต้ `repos/` ขณะที่ Git ยังคง ignore เหมือนเดิม

ไฟล์นี้ใช้ `!repos/*` ไม่ใช่ `!repos/**` โดยตั้งใจ เพราะ `**` จะลบล้าง `.gitignore` ภายในแต่ละ repository ด้วย ทำให้ `node_modules`, `dist` และ build artifacts โผล่ขึ้นมาในผลการค้นหา

การค้นหาทำได้จาก root แต่การรันคำสั่งเฉพาะ repository เช่น test, build หรือ Git ยังต้องเปลี่ยน working directory เข้า repository เป้าหมายก่อนเสมอ

## Git Policy

`GIT_POLICY.md` เก็บกฎความปลอดภัยตอนเขียนขึ้น remote และถูกอ้างจาก workspace instructions เพื่อให้ AI อ่านก่อนทำ remote write

repository ถูกแบ่งเป็น class:

- `own` — repository ของผู้ใช้ push ได้เมื่อผู้ใช้สั่งและ workflow ของ repository นั้นอนุญาต
- `client` — repository ของผู้อื่น ห้าม push ทุกกรณี
- repository ที่ยังไม่ถูกจัดประเภทถือเป็น `client` เสมอ repository ใหม่จึงถูกป้องกันไว้ก่อนโดยไม่ต้องพึ่งความจำ

กฎของแต่ละ class อยู่ใน `GIT_POLICY.md` ซึ่งเหมือนกันทุก project ส่วนตารางว่า repository ใดอยู่ class ใดอยู่ใน `AGENTS.md` ที่ root เพราะเป็นข้อมูลเฉพาะ project และเป็นที่เดียวที่เขียนได้โดยไม่ละเมิดกฎ AI harness isolation ซึ่งห้ามเพิ่ม instruction files ลงใน `repos/*`

การอนุญาตให้ push ไม่ได้รวมถึง force push หรือการลบ ref ซึ่งต้องระบุอนุญาตแยกต่างหาก

## AI Harness Isolation

ไฟล์สำหรับ coordination กับ AI เช่น `AGENTS.md`, `CLAUDE.md`, `.agents/`, `.claude/`, prompts, plans และ evaluation artifacts ต้องอยู่ใน root workspace เท่านั้น

ห้ามเพิ่ม แก้ไข หรือลบ AI harness configuration ภายใน work repository เช่น `repos/*` หรือ source root อื่นที่ project กำหนดไว้ เว้นแต่ผู้ใช้ร้องขอการเปลี่ยนแปลงไฟล์นั้นโดยตรง ไฟล์ configuration ที่มีอยู่ใน external repository ถือเป็นทรัพย์สินและส่วนหนึ่งของ workflow ของเจ้าของ repository

**ข้อจำกัดที่ต้องยอมรับ** — ข้อกำหนดเหล่านี้ป้องกันการสร้างหรือแก้ไฟล์โดยตั้งใจได้ แต่ป้องกัน instruction discovery ไม่ได้ทั้งหมด จากการทดสอบพบว่าเมื่อ AI เปลี่ยน working directory เข้าไปใน repository ใต้ `repos/` มันยังอาจอ่าน `AGENTS.md` หรือ skills ที่อยู่ภายใน repository นั้นได้ พฤติกรรมนี้ขึ้นกับ provider และต้องตั้งค่าแยกตาม provider โดยยังไม่มีวิธีปิดที่ได้ผล 100%

ผลกระทบที่ต้องระวังคือ AI อาจทำตามคำสั่งของทีมเจ้าของ repository โดยที่ workspace ไม่ได้ตั้งใจ ให้ถือเป็นความเสี่ยงที่รู้อยู่ ไม่ใช่สิ่งที่แก้ได้ด้วยกฎใน workspace

## ภาษาของไฟล์ใน Workspace

workspace แยกภาษาออกเป็นสองเรื่องที่ไม่เกี่ยวกัน

- **ไฟล์ที่เป็นคำสั่งให้ AI** — `AGENTS.md`, `GIT_POLICY.md` และ `SKILL.md` ทุกไฟล์ ใช้ภาษาอังกฤษเพื่อ model และ tool compatibility
- **ไฟล์ที่อธิบาย workspace ให้คน** — `README.md` และเอกสารที่ AI สร้างให้ผู้ใช้ ใช้ภาษาไทยเป็นหลัก

ภาษาของไฟล์คำสั่งไม่ได้กำหนดภาษาที่ AI ใช้คุยกับผู้ใช้ ค่าเริ่มต้นของการสนทนายังเป็นภาษาไทย และ `$bootstrap-project-workspace` ถามเฉพาะภาษาฝั่งที่คุยกับคนเท่านั้น ไม่แปลไฟล์คำสั่ง

## การตรวจสอบ Workspace

ตรวจ Repository Catalog ตาม contract โดยไม่ผูกกับ consumer ใด:

```bash
python3 tooling/validate_repository_catalog.py
```

ตรวจเอกสารใน `workspace-meta/handoff/` ตาม contract:

```bash
python3 tooling/validate_handoff.py
```

รัน automated tests ของ contract และ tooling:

```bash
python3 -m unittest discover -s tooling/tests
```

## สิ่งที่จะออกแบบเพิ่มเติม

ข้อมูลที่มี lifecycle หรือหน้าที่ต่างจาก Catalog ต้องอยู่คนละไฟล์และอ้าง repository ด้วย `repo_id` แต่ละเครื่องมือจึงเลือกใช้ repository subset ของตัวเองได้โดยไม่ทำให้ Catalog ขาดสมาชิก ชั้นข้อมูลที่อาจเพิ่มในอนาคต:

- `ai-access-policy.yaml` — AI อ่าน เขียน หรือ execute repository ใดได้
- `codebase-knowledge.yaml` — repository ใดต้อง index และใช้เครื่องมือหรือ configuration ใด
- `integrations.yaml` — HTTP calls, events, queues, packages หรือ dependencies ที่ตรวจพบเชื่อมไปยัง repository หรือ external system ใด
- `codebase-knowledge/` — generated knowledge ราย repository และ project-level knowledge ที่ประกอบขึ้นภายหลัง
- `repo-sources.yaml` — remote URL ของ external repository สำหรับ clone workspace กลับมาบนเครื่องใหม่

ชื่อและ schema ของไฟล์เหล่านี้ยังต้องออกแบบแยกต่างหาก ห้ามเพิ่ม fields ดังกล่าวเข้า `repositories.yaml` ล่วงหน้า และไม่ควรสร้างชั้นเหล่านี้จนกว่าจะมีงานจริงเรียกร้อง
