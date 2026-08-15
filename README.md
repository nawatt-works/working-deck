# Working Deck

Workspace สำหรับทำงานร่วมกันระหว่างมนุษย์กับ AI บนหลาย Git repositories โดยแยกข้อมูลสำหรับ coordination ออกจาก source code ของแต่ละ repository อย่างชัดเจน

root repository นี้ทำหน้าที่เป็น control plane สำหรับเก็บแนวทางการทำงาน บริบท เอกสาร เครื่องมือ และ configuration ที่ใช้ร่วมกับ AI ส่วนตัวงานจริงและ supporting repositories อยู่ใน `repos/` และยังคงเป็น Git repository อิสระจาก root workspace

## โครงสร้าง Workspace

```text
.
├── AGENTS_EXAMPLE.md             # ร่างแนวทางการทำงานของ workspace
├── README.md
├── .code-workspace               # generated VS Code multi-root workspace
├── .agents/
│   └── skills/                   # skills ที่เป็นของ root workspace
├── .workbench/
│   └── repositories.yaml         # canonical Repository Catalog
├── .runtime/                     # temporary files และผลลัพธ์ระหว่างทาง
├── repos/                         # independent Git repositories
└── tooling/                       # automation สำหรับดูแล root workspace
```

### `.workbench/`

เก็บบริบทและเอกสารที่มนุษย์กับ AI ใช้ทำงานร่วมกัน เช่น แผนงาน specification, architecture, research, decisions และ Repository Catalog

ข้อมูลในพื้นที่นี้เป็นของ root workspace และต้องไม่ถูกคัดลอกหรือ commit เข้า external repositories โดยอัตโนมัติ

### `.runtime/`

เก็บไฟล์ชั่วคราว เช่น logs, extracted files, generated samples และผลลัพธ์ระหว่างทาง ไฟล์ในพื้นที่นี้ไม่ใช่ deliverable ฉบับสุดท้ายและถูก ignore จาก Git ยกเว้น `.gitkeep`

### `repos/`

เก็บ checkout ของ Git repositories ที่เป็นตัวงานจริงหรือสนับสนุนการทำงาน เช่น application, library, documentation, test environment, agent skill, extension หรือ automation แต่ละโฟลเดอร์ระดับแรกภายใต้ `repos/` ควรเป็น Git repository อิสระเท่าที่ทำได้ และอาจเป็น repository ของลูกค้า ทีมภายนอก หรือผู้ใช้เอง

repository แต่ละแห่งอาจเป็น single-project repository หรือ monorepo ที่มีหลาย applications, services, packages หรือ libraries อยู่ภายในก็ได้ การอยู่ใต้ `repos/` บอกเพียง Git boundary ระดับ workspace ไม่ได้บอกรูปแบบโครงสร้างภายใน repository ดังนั้นต้องตรวจ configuration และ documentation ของ repository เป้าหมายก่อนทำงานเสมอ

root Git repository ignore เนื้อหาภายใต้ `repos/` เพื่อป้องกันไม่ให้ source code หรือการเปลี่ยนแปลงของ external repository ถูก commit ปะปนกับ coordination workspace การตั้งค่านี้ไม่ได้ห้าม repository แต่ละแห่งเป็น monorepo ภายในขอบเขตของตัวเอง

ในเอกสารของ workspace นี้ คำว่า **workspace repository** หรือ **repo** หมายถึง direct child directory ใต้ `repos/` ซึ่งโดยปกติควรเป็น Git checkout หากยังไม่ใช่ Git repository ให้ถือเป็นข้อยกเว้นและแสดง warning ส่วน **cataloged repository** หมายถึง repo ที่มีรายการอยู่ใน `.workbench/repositories.yaml`

คำว่า repository ที่พบภายใน source code เช่น repository pattern, data repository, `Repository<T>` หรือ class ที่ลงท้ายด้วย `Repository` เป็นแนวคิดภายในตัวงาน ไม่ถือเป็น workspace repository หรือ cataloged repository

### `tooling/`

เก็บ automation ที่ดูแล root workspace เครื่องมือในพื้นที่นี้ต้องไม่เขียนไฟล์ลง `repos/*` เว้นแต่ผู้ใช้ร้องขอให้แก้ตัวงานใน repository นั้นอย่างชัดเจน

## Repository Catalog

ไฟล์ `.workbench/repositories.yaml` เป็น authoritative catalog ของ repositories ทั้งหมดที่เป็นสมาชิกของ project workspace และเป็นจุดอ้างอิงกลางสำหรับ automation กับ knowledge files อื่น:

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

หากยังไม่มี cataloged repository ให้ใช้ `repositories: []` ซึ่งเป็น catalog ที่ถูกต้อง

การอยู่ใน catalog ไม่ได้หมายความว่า AI มีสิทธิ์อ่าน แก้ไข หรือ execute repository นั้น ไม่ได้บังคับให้สร้าง codebase knowledge และไม่ได้หมายความว่า repository นั้นต้องเป็น application source code ตัวอย่างเช่น repository ที่เป็น test environment, documentation, agent skill หรือ extension สามารถอยู่ใน catalog ได้โดยไม่ต้องถูก index

`repos/` มีไว้สำหรับ repositories ที่เป็นสมาชิกของ project workspace เท่านั้น ดังนั้น direct child directory ทุกแห่งใต้ `repos/` ต้องมีรายการใน catalog ไม่ว่าจะเป็น application source code, documentation, test environment, agent skill, extension หรือ automation หากพบ directory ที่ไม่มีรายการ ให้ถือว่า Catalog drift และเพิ่มเข้า catalog

ในทางกลับกัน cataloged repository อาจยังไม่มี checkout บนเครื่องปัจจุบันได้ เช่น ยังไม่ได้ clone เครื่องมือจะแจ้ง warning แต่ห้ามลบรายการนั้นโดยอัตโนมัติ เพราะ Catalog อธิบาย project workspace ไม่ใช่เฉพาะสิ่งที่มีอยู่บนเครื่องหนึ่งเครื่อง

## ข้อมูลที่แยกจาก Repository Catalog

ข้อมูลที่มี lifecycle หรือหน้าที่ต่างจาก catalog ต้องอยู่คนละไฟล์และอ้าง repository ด้วย `repo_id` แต่ละเครื่องมือจึงเลือกใช้ repository subset ของตัวเองได้โดยไม่ทำให้ Catalog ขาดสมาชิก ตัวอย่างชั้นข้อมูลที่อาจเพิ่มในอนาคต:

- `ai-access-policy.yaml` — AI อ่าน เขียน หรือ execute repository ใดได้
- `codebase-knowledge.yaml` — repository ใดต้อง index และใช้เครื่องมือหรือ configuration ใด
- `integrations.yaml` — HTTP calls, events, queues, packages หรือ dependencies ที่ตรวจพบเชื่อมไปยัง repository หรือ external system ใด
- `codebase-knowledge/` — generated knowledge ราย repository และ project-level knowledge ที่ประกอบขึ้นภายหลัง

ชื่อและ schema ของไฟล์เหล่านี้ยังต้องออกแบบแยกต่างหาก ห้ามเพิ่ม fields ดังกล่าวเข้า `repositories.yaml` ล่วงหน้า

## การสร้าง VS Code Workspace

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

ไฟล์ `.code-workspace` ถูก commit ได้ แต่ไม่ควรแก้รายการ folders ด้วยมือ หากข้อมูลไม่ถูกต้องให้แก้ `.workbench/repositories.yaml` หรือ generator แล้วสร้างไฟล์ใหม่

generator จะรวม cataloged repositories ทุกแห่งไว้ใน `.code-workspace` โดยไม่พิจารณา access หรือ indexing policy จะแจ้ง warning เมื่อ directory ใน catalog ยังไม่มีอยู่เพื่อรองรับกรณีที่ยังไม่ได้ clone และจะหยุดด้วย error เมื่อพบ direct child ใต้ `repos/` ที่ยังไม่มีใน Catalog

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

1. ตรวจ `.workbench/repositories.yaml` เพื่อหา `repo_id` และ path ของ repository เป้าหมาย
2. เปลี่ยน working directory เข้า repository นั้นก่อนเรียก Git หรือเครื่องมือเฉพาะโครงการ
3. เก็บ notes, plans และหลักฐานการทำงานไว้ใน `.workbench/` หรือ `.runtime/` ตามอายุของข้อมูล
4. ตรวจ Git status ภายใน repository เป้าหมายก่อน commit
5. ตรวจว่าไม่มี coordination artifacts ของ root workspace ปะปนอยู่ใน change set ของ external repository

รายละเอียด policy ฉบับร่างอยู่ใน `AGENTS_EXAMPLE.md`

## สิ่งที่จะออกแบบเพิ่มเติม

ในอนาคต workspace จะมี codebase knowledge ราย repository และข้อมูลสำหรับอธิบายความสัมพันธ์ข้าม repositories เช่น HTTP calls, events, queues และ identifiers ที่ใช้ map การสื่อสารกลับไปยัง `repo_id` หรือ external system โดย schema และชื่อไฟล์จะออกแบบแยกในภายหลัง
