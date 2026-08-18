# Working Deck

Workspace สำหรับทำงานร่วมกันระหว่างมนุษย์กับ AI บนหลาย Git repositories โดยแยกข้อมูลสำหรับ coordination ออกจาก source code ของแต่ละ repository อย่างชัดเจน

root repository นี้ทำหน้าที่เป็น control plane สำหรับเก็บแนวทางการทำงาน บริบท เอกสาร เครื่องมือ และ configuration ที่ใช้ร่วมกับ AI ส่วนตัวงานจริงและ supporting repositories อยู่ใน `repos/` และยังคงเป็น Git repository อิสระจาก root workspace

Working Deck เป็น workspace starter สำหรับนำโครงสร้างและไฟล์ที่จำเป็นไปใช้เป็นฐานของ project อื่น ไม่ใช่ application project

## เริ่ม Project ใหม่

1. คัดลอกไฟล์และโฟลเดอร์ของ Working Deck ที่ต้องใช้ไปยัง project ใหม่ โดยไม่เอา `.git` และไฟล์ local ที่ไม่เกี่ยวข้องไปด้วย
2. เปลี่ยนชื่อ `AGENTS_EXAMPLE.md` เป็น `AGENTS.md` เพื่อเปิดใช้ workspace instructions กับ AI harness ที่รองรับ
3. นำ Git repositories ของ project ไปไว้เป็น direct child ใต้ `repos/`
4. ใช้ `$manage-repository-catalog` หรือแก้ `workbench/repositories.yaml` ให้ register repositories ทั้งหมด
5. รัน `python3 tooling/validate_repository_catalog.py`
6. รัน `python3 tooling/generate_vscode_workspace.py` แล้วเปิด `.code-workspace`

Catalog ใน starter เริ่มด้วย `repositories: []` ส่วนตัวอย่าง schema อยู่ในเอกสารและ skill เพื่อไม่ให้ AI เข้าใจ mock repository ว่าเป็นสมาชิกจริงของ project ใหม่

## โครงสร้าง Workspace

```text
.
├── AGENTS_EXAMPLE.md        # ร่างแนวทางการทำงานของ workspace
├── GIT_POLICY.md            # Git push safety policy แยกตาม repository class
├── README.md
├── .code-workspace          # generated VS Code multi-root workspace
├── .ignore                  # ให้เครื่องมือค้นหามองเห็น repos/ ที่ Git ignore
├── .agents/
│   └── skills/              # skills ที่เป็นของ root workspace
├── workbench/
│   ├── README.md            # กติกาว่าใครเขียนตรงไหนได้
│   ├── repositories.yaml    # Repository Catalog instance
│   └── workspace-contracts/ # shared contracts สำหรับ consumers
├── repos/                   # independent Git repositories
└── tooling/                 # automation สำหรับดูแล root workspace
```

### `workbench/`

เก็บบริบทและเอกสารที่มนุษย์กับ AI ใช้ทำงานร่วมกัน เช่น แผนงาน specification, architecture, research, decisions และ Repository Catalog

ข้อมูลในพื้นที่นี้เป็นของ root workspace และต้องไม่ถูกคัดลอกหรือ commit เข้า external repositories โดยอัตโนมัติ

พื้นที่นี้มีผู้เขียนได้หลายราย แต่ละ harness หรือเครื่องมือเก็บ artifact ของตัวเองไว้ใน namespace ของตัวเองใต้ `workbench/<producer>/` ส่วนไฟล์ระดับ root ของ `workbench/` เป็นของกลางที่ต้องมี contract กติกาทั้งหมดอยู่ใน `workbench/README.md`

### `repos/`

เก็บ checkout ของ Git repositories ที่เป็นตัวงานจริงหรือสนับสนุนการทำงาน เช่น application, library, documentation, test environment, agent skill, extension หรือ automation แต่ละโฟลเดอร์ระดับแรกภายใต้ `repos/` ควรเป็น Git repository อิสระเท่าที่ทำได้ และอาจเป็น repository ของลูกค้า ทีมภายนอก หรือผู้ใช้เอง

repository แต่ละแห่งอาจเป็น single-project repository หรือ monorepo ที่มีหลาย applications, services, packages หรือ libraries อยู่ภายในก็ได้ การอยู่ใต้ `repos/` บอกเพียง Git boundary ระดับ workspace ไม่ได้บอกรูปแบบโครงสร้างภายใน repository ดังนั้นต้องตรวจ configuration และ documentation ของ repository เป้าหมายก่อนทำงานเสมอ

root Git repository ignore เนื้อหาภายใต้ `repos/` เป็นค่าเริ่มต้น เพื่อไม่ให้ repository ที่มี `.git` ของตัวเองถูก commit เข้า root ซึ่งจะกลายเป็น gitlink ที่ clone แล้วได้โฟลเดอร์ว่าง การตั้งค่านี้ไม่ได้ห้าม repository แต่ละแห่งเป็น monorepo ภายในขอบเขตของตัวเอง

บาง project มีโฟลเดอร์ใต้ `repos/` ที่ไม่จำเป็นต้องมี Git ของตัวเองและควรถูก commit ไปกับ root workspace กรณีนี้ให้ opt-in ทีละรายการด้วย `!repos/<ชื่อโฟลเดอร์>/` ใน `.gitignore`

ในเอกสารของ workspace นี้ คำว่า **workspace repository** หรือ **repo** หมายถึง direct child directory ใต้ `repos/` ซึ่งโดยปกติควรเป็น Git checkout หากยังไม่ใช่ Git repository ให้ถือเป็นข้อยกเว้นและแสดง warning ส่วน **cataloged repository** หมายถึง repo ที่มีรายการอยู่ใน `workbench/repositories.yaml`

คำว่า repository ที่พบภายใน source code เช่น repository pattern, data repository, `Repository<T>` หรือ class ที่ลงท้ายด้วย `Repository` เป็นแนวคิดภายในตัวงาน ไม่ถือเป็น workspace repository หรือ cataloged repository

### `tooling/`

เก็บ automation ที่ดูแล root workspace เครื่องมือในพื้นที่นี้ต้องไม่เขียนไฟล์ลง `repos/*` เว้นแต่ผู้ใช้ร้องขอให้แก้ตัวงานใน repository นั้นอย่างชัดเจน

- `validate_repository_catalog.py` ตรวจ workspace-level Repository Catalog contract และความครบถ้วนของ direct child ใต้ `repos/`
- `generate_vscode_workspace.py` เป็น consumer ที่สร้าง `.code-workspace` จาก Catalog ที่ผ่าน validation
- `repos_status.py` รายงานสถานะ Git ของทุก repository ตรวจ tracking state และเตือนเมื่อพบ coordination artifact ค้างอยู่ใน change set ของ repository ภายนอก
- `repository_catalog.py` เป็น dependency-free contract parser และ validation library ที่ tooling อื่นนำไปใช้ร่วมกันได้

## Repository Catalog

ไฟล์ `workbench/repositories.yaml` เป็น authoritative catalog ของ repositories ทั้งหมดที่เป็นสมาชิกของ project workspace และเป็นจุดอ้างอิงกลางสำหรับ automation กับ knowledge files อื่น:

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

schema version 1 รองรับเฉพาะ `repo_id` และ `path` เพื่อให้ catalog เก็บเฉพาะ identity กับข้อเท็จจริงที่ค่อนข้างคงที่

นิยาม contract, machine-readable schema และ compatibility rules อยู่ที่ `workbench/workspace-contracts/repository-catalog/` ซึ่งเป็น workspace infrastructure ไม่ได้เป็นของ VS Code generator, Software Factory หรือ Codebase Knowledge

หากยังไม่มี cataloged repository ให้ใช้ `repositories: []` ซึ่งเป็น catalog ที่ถูกต้อง

การอยู่ใน catalog ไม่ได้หมายความว่า AI มีสิทธิ์อ่าน แก้ไข หรือ execute repository นั้น และไม่ได้หมายความว่า repository นั้นต้องเป็น application source code ตัวอย่างเช่น repository ที่เป็น test environment, documentation, agent skill หรือ extension สามารถอยู่ใน catalog ได้

`repos/` มีไว้สำหรับ repositories ที่เป็นสมาชิกของ project workspace เท่านั้น ดังนั้น direct child directory ทุกแห่งใต้ `repos/` ต้องมีรายการใน catalog ไม่ว่าจะเป็น application source code, documentation, test environment, agent skill, extension หรือ automation หากพบ directory ที่ไม่มีรายการ ให้ถือว่า Catalog drift และเพิ่มเข้า catalog

ในทางกลับกัน cataloged repository อาจยังไม่มี checkout บนเครื่องปัจจุบันได้ เช่น ยังไม่ได้ clone เครื่องมือจะแจ้ง warning แต่ห้ามลบรายการนั้นโดยอัตโนมัติ เพราะ Catalog อธิบาย project workspace ไม่ใช่เฉพาะสิ่งที่มีอยู่บนเครื่องหนึ่งเครื่อง

## ข้อมูลที่แยกจาก Repository Catalog

ข้อมูลที่มี lifecycle หรือหน้าที่ต่างจาก catalog ต้องอยู่คนละไฟล์และอ้าง repository ด้วย `repo_id` แต่ละเครื่องมือจึงเลือกใช้ repository subset ของตัวเองได้โดยไม่ทำให้ Catalog ขาดสมาชิก ตัวอย่างชั้นข้อมูลที่อาจเพิ่มในอนาคต:

- `ai-access-policy.yaml` — AI อ่าน เขียน หรือ execute repository ใดได้
- `codebase-knowledge.yaml` — repository ใดต้อง index และใช้เครื่องมือหรือ configuration ใด
- `integrations.yaml` — HTTP calls, events, queues, packages หรือ dependencies ที่ตรวจพบเชื่อมไปยัง repository หรือ external system ใด
- `codebase-knowledge/` — generated knowledge ราย repository และ project-level knowledge ที่ประกอบขึ้นภายหลัง

ชื่อและ schema ของไฟล์เหล่านี้ยังต้องออกแบบแยกต่างหาก ห้ามเพิ่ม fields ดังกล่าวเข้า `repositories.yaml` ล่วงหน้า

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

**coordination artifact ที่รั่วออก** — สแกน change set ที่ยัง pending ในแต่ละ repository ภายนอกเพื่อหาไฟล์อย่าง `AGENTS.md`, `CLAUDE.md`, `.agents/`, `.claude/` และ `workbench/` ที่กำลังจะถูก commit เข้า repository ของผู้อื่น

ตรวจเฉพาะไฟล์ที่ยัง pending โดยตั้งใจ ไฟล์ที่ commit ไปแล้วถือเป็นทรัพย์สินของ repository นั้น เช่น AI harness configuration ที่ทีมเจ้าของใช้งานอยู่ ซึ่งไม่ใช่การรั่วไหล

## การค้นหาโค้ดจาก Workspace Root

`rg` และ `fd` เคารพ `.gitignore` โดยปริยาย การค้นหาจาก root จึงเคยคืนผลว่างสำหรับโค้ดที่อยู่ใน `repos/` โดยไม่แจ้ง error ซึ่งอ่านได้ว่า "ไม่มีโค้ดนี้" ทั้งที่มีอยู่

ไฟล์ `.ignore` ที่ workspace root แก้ปัญหานี้ เครื่องมือค้นหาอ่าน `.ignore` ด้วย priority สูงกว่า `.gitignore` ทำให้ค้นจาก root แล้วเห็นเนื้อหาใต้ `repos/` ขณะที่ Git ยังคง ignore เหมือนเดิม

ไฟล์นี้ใช้ `!repos/*` ไม่ใช่ `!repos/**` โดยตั้งใจ เพราะ `**` จะลบล้าง `.gitignore` ภายในแต่ละ repository ด้วย ทำให้ `node_modules`, `dist` และ build artifacts โผล่ขึ้นมาในผลการค้นหา

การค้นหาทำได้จาก root แต่การรันคำสั่งเฉพาะ repository เช่น test, build หรือ Git ยังต้องเปลี่ยน working directory เข้า repository เป้าหมายก่อนเสมอ

## การสร้าง VS Code Workspace

ตรวจ Repository Catalog โดยไม่ผูกกับ consumer ใด:

```bash
python3 tooling/validate_repository_catalog.py
```

รันคำสั่งนี้จาก workspace root:

```bash
python3 tooling/generate_vscode_workspace.py
```

ตรวจว่า `.code-workspace` ตรงกับ catalog โดยไม่เขียนไฟล์:

```bash
python3 tooling/generate_vscode_workspace.py --check
```

เปิด multi-root workspace:

```bash
code .code-workspace
```

ไฟล์ `.code-workspace` เป็น derived editor configuration ที่สร้างจาก Repository Catalog เพื่อแก้ปัญหา VS Code ซึ่งเปิดจาก root workspace แล้วอาจไม่ค้นพบหรือ index repositories ใต้ `repos/` เพราะ directory นี้ถูก root Git repository ignore

ไฟล์ `.code-workspace` ถูก commit ได้ แต่ไม่ควรแก้รายการ folders ด้วยมือ หากข้อมูลไม่ถูกต้องให้แก้ `workbench/repositories.yaml` หรือ generator แล้วสร้างไฟล์ใหม่

generator จะรวม cataloged repositories ทุกแห่งไว้ใน `.code-workspace` โดยไม่พิจารณา access หรือ indexing policy จะแจ้ง warning เมื่อ directory ใน catalog ยังไม่มีอยู่เพื่อรองรับกรณีที่ยังไม่ได้ clone และจะหยุดด้วย error เมื่อพบ direct child ใต้ `repos/` ที่ยังไม่มีใน Catalog

รัน automated tests ของ contract และ tooling:

```bash
python3 -m unittest discover -s tooling/tests
```

## AI Harness Isolation

ไฟล์สำหรับ coordination กับ AI เช่น `AGENTS.md`, `CLAUDE.md`, `.agents/`, `.claude/`, prompts, plans และ evaluation artifacts ต้องอยู่ใน root workspace เท่านั้น

ห้ามเพิ่ม แก้ไข หรือลบ AI harness configuration ภายใน `repos/*` เว้นแต่ผู้ใช้ร้องขอการเปลี่ยนแปลงไฟล์นั้นโดยตรง ไฟล์ configuration ที่มีอยู่ใน external repository ถือเป็นทรัพย์สินและส่วนหนึ่งของ workflow ของเจ้าของ repository

ข้อกำหนดใน workspace สามารถป้องกันการสร้างหรือแก้ไฟล์โดยตั้งใจได้ แต่ไม่รับประกันว่า AI harness ทุก provider จะไม่ค้นพบหรือโหลด nested configuration การควบคุม instruction discovery ต้องตั้งค่าแยกตาม provider

## Skills สำหรับ Repository Workspace

แยก workflow เป็นสอง skills:

- `manage-repository-catalog` อยู่ที่ `.agents/skills/manage-repository-catalog/` ใช้ค้นหาและ sync direct child repositories ทั้งหมด รวมถึงสร้าง เพิ่ม ลบ หรือแก้ authoritative Repository Catalog โดยไม่ตัดสิน access, indexing หรือ integrations
- `generate-vscode-workspace` อยู่ที่ `.agents/skills/generate-vscode-workspace/` ใช้อ่าน catalog ที่มีอยู่แล้วเพื่อสร้างและตรวจ `.code-workspace` เท่านั้น

ตัวอย่างคำขอ:

```text
ใช้ $manage-repository-catalog เพิ่ม order-api เข้า Repository Catalog
ใช้ $generate-vscode-workspace สร้าง VS Code workspace จาก catalog ล่าสุด
```

## แนวทางการทำงาน

1. ตรวจ `workbench/repositories.yaml` เพื่อหา `repo_id` และ path ของ repository เป้าหมาย
2. เปลี่ยน working directory เข้า repository นั้นก่อนเรียก Git หรือเครื่องมือเฉพาะโครงการ
3. เก็บ notes, plans และหลักฐานการทำงานไว้ใน `workbench/` ส่วนไฟล์ชั่วคราวให้ใช้ temporary directory ของ harness หรือระบบ
4. ตรวจ Git status ภายใน repository เป้าหมายก่อน commit
5. ตรวจว่าไม่มี coordination artifacts ของ root workspace ปะปนอยู่ใน change set ของ external repository

รายละเอียด policy ฉบับร่างอยู่ใน `AGENTS_EXAMPLE.md`

Git push safety policy อยู่ใน `GIT_POLICY.md` และถูกอ้างจาก workspace instructions เพื่อให้ AI อ่านก่อนทำ remote write

`GIT_POLICY.md` แบ่ง repository เป็น class — `own` คือ repository ของผู้ใช้ซึ่ง push ได้ตามปกติ ส่วน `client` คือ repository ของผู้อื่นซึ่งห้าม push ทุกกรณี repository ที่ยังไม่ถูกจัดประเภทถือเป็น `client` เสมอ

กฎแยกตาม class อยู่ใน `GIT_POLICY.md` ซึ่งเหมือนกันทุก project ส่วนตารางว่า repository ใดอยู่ class ใดอยู่ใน `AGENTS.md` ที่ root เพราะเป็นข้อมูลเฉพาะ project และเป็นที่เดียวที่เขียนได้โดยไม่ละเมิดกฎ AI harness isolation ซึ่งห้ามเพิ่ม instruction files ลงใน `repos/*`

## สิ่งที่จะออกแบบเพิ่มเติม

ในอนาคต workspace จะมี codebase knowledge ราย repository และข้อมูลสำหรับอธิบายความสัมพันธ์ข้าม repositories เช่น HTTP calls, events, queues และ identifiers ที่ใช้ map การสื่อสารกลับไปยัง `repo_id` หรือ external system โดย schema และชื่อไฟล์จะออกแบบแยกในภายหลัง
