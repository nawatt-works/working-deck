# Working Deck

Workspace สำหรับทำงานร่วมกันระหว่างมนุษย์กับ AI บนหลาย Git repositories โดยแยกข้อมูลสำหรับ coordination ออกจาก source code ของแต่ละ repository อย่างชัดเจน

root repository นี้ทำหน้าที่เป็น control plane สำหรับเก็บแนวทางการทำงาน บริบท เอกสาร เครื่องมือ และ configuration ที่ใช้ร่วมกับ AI ส่วน source code จริงอยู่ใน `repos/` และยังคงเป็น Git repository อิสระของแต่ละทีม

## โครงสร้าง Workspace

```text
.
├── AGENTS_EXAMPLE.md             # ร่างแนวทางการทำงานของ workspace
├── README.md
├── .code-workspace               # generated VS Code multi-root workspace
├── .agents/
│   └── skills/                   # skills ที่เป็นของ root workspace
├── .workbench/
│   └── repositories.yaml         # registry ของ external repositories
├── .runtime/                     # temporary files และผลลัพธ์ระหว่างทาง
├── repos/                         # independent Git repositories
└── tooling/                       # automation สำหรับดูแล root workspace
```

### `.workbench/`

เก็บบริบทและเอกสารที่มนุษย์กับ AI ใช้ทำงานร่วมกัน เช่น แผนงาน specification, architecture, research, decisions และ repository registry

ข้อมูลในพื้นที่นี้เป็นของ root workspace และต้องไม่ถูกคัดลอกหรือ commit เข้า external repositories โดยอัตโนมัติ

### `.runtime/`

เก็บไฟล์ชั่วคราว เช่น logs, extracted files, generated samples และผลลัพธ์ระหว่างทาง ไฟล์ในพื้นที่นี้ไม่ใช่ deliverable ฉบับสุดท้ายและถูก ignore จาก Git ยกเว้น `.gitkeep`

### `repos/`

เก็บ checkout ของ Git repositories ที่เป็นตัวงานจริง แต่ละโฟลเดอร์ระดับแรกภายใต้ `repos/` ควรเป็น Git repository อิสระเท่าที่ทำได้ และอาจเป็น repository ของลูกค้าหรือทีมภายนอก

repository แต่ละแห่งอาจเป็น single-project repository หรือ monorepo ที่มีหลาย applications, services, packages หรือ libraries อยู่ภายในก็ได้ การอยู่ใต้ `repos/` บอกเพียง Git boundary ระดับ workspace ไม่ได้บอกรูปแบบโครงสร้างภายใน repository ดังนั้นต้องตรวจ configuration และ documentation ของ repository เป้าหมายก่อนทำงานเสมอ

root Git repository ignore เนื้อหาภายใต้ `repos/` เพื่อป้องกันไม่ให้ source code หรือการเปลี่ยนแปลงของ external repository ถูก commit ปะปนกับ coordination workspace การตั้งค่านี้ไม่ได้ห้าม repository แต่ละแห่งเป็น monorepo ภายในขอบเขตของตัวเอง

### `tooling/`

เก็บ automation ที่ดูแล root workspace เครื่องมือในพื้นที่นี้ต้องไม่เขียนไฟล์ลง `repos/*` เว้นแต่ผู้ใช้ร้องขอให้แก้ตัวงานใน repository นั้นอย่างชัดเจน

## Repository Registry

ไฟล์ `.workbench/repositories.yaml` เป็น source of truth สำหรับรายชื่อ repository และตำแหน่ง checkout:

```yaml
repositories:
  - id: repo_order_api
    service: order-api
    path: repos/order-api
```

ความหมายของแต่ละ field:

- `id` — identity ที่คงที่ของ repository ภายใน workspace
- `service` — ชื่อที่ใช้แสดงใน VS Code workspace
- `path` — relative path ของ repository โดยต้องอยู่ภายใต้ `repos/`

เมื่อเพิ่ม ลบ เปลี่ยนชื่อ หรือย้าย repository ให้แก้ registry ก่อน แล้ว generate `.code-workspace` ใหม่

## การสร้าง VS Code Workspace

รันคำสั่งนี้จาก workspace root:

```bash
python3 tooling/generate_vscode_workspace.py
```

ตรวจว่า `.code-workspace` ตรงกับ registry โดยไม่เขียนไฟล์:

```bash
python3 tooling/generate_vscode_workspace.py --check
```

เปิด multi-root workspace:

```bash
code .code-workspace
```

ไฟล์ `.code-workspace` ถูก commit ได้ แต่ไม่ควรแก้รายการ folders ด้วยมือ หากข้อมูลไม่ถูกต้องให้แก้ `.workbench/repositories.yaml` หรือ generator แล้วสร้างไฟล์ใหม่

generator จะแจ้ง warning เมื่อ directory ใน registry ยังไม่มีอยู่ แต่ยังสามารถสร้าง workspace file ได้ เพื่อรองรับกรณีที่ repository ยังไม่ได้ clone

## AI Harness Isolation

ไฟล์สำหรับ coordination กับ AI เช่น `AGENTS.md`, `CLAUDE.md`, `.agents/`, `.claude/`, prompts, plans และ evaluation artifacts ต้องอยู่ใน root workspace เท่านั้น

ห้ามเพิ่ม แก้ไข หรือลบ AI harness configuration ภายใน `repos/*` เว้นแต่ผู้ใช้ร้องขอการเปลี่ยนแปลงไฟล์นั้นโดยตรง ไฟล์ configuration ที่มีอยู่ใน external repository ถือเป็นทรัพย์สินและส่วนหนึ่งของ workflow ของเจ้าของ repository

ข้อกำหนดใน workspace สามารถป้องกันการสร้างหรือแก้ไฟล์โดยตั้งใจได้ แต่ไม่รับประกันว่า AI harness ทุก provider จะไม่ค้นพบหรือโหลด nested configuration การควบคุม instruction discovery ต้องตั้งค่าแยกตาม provider

## Skill สำหรับ Generate Workspace

skill `generate-vscode-workspace` อยู่ที่ `.agents/skills/generate-vscode-workspace/` ใช้สำหรับให้ AI สร้างและตรวจ `.code-workspace` ด้วย workflow เดียวกับที่มนุษย์ใช้

ตัวอย่างคำขอ:

```text
ใช้ $generate-vscode-workspace เพิ่ม repository ใหม่และตรวจว่า VS Code workspace เป็นปัจจุบัน
```

## แนวทางการทำงาน

1. ตรวจ `.workbench/repositories.yaml` เพื่อหา repository เป้าหมาย
2. เปลี่ยน working directory เข้า repository นั้นก่อนเรียก Git หรือเครื่องมือเฉพาะโครงการ
3. เก็บ notes, plans และหลักฐานการทำงานไว้ใน `.workbench/` หรือ `.runtime/` ตามอายุของข้อมูล
4. ตรวจ Git status ภายใน repository เป้าหมายก่อน commit
5. ตรวจว่าไม่มี coordination artifacts ของ root workspace ปะปนอยู่ใน change set ของ external repository

รายละเอียด policy ฉบับร่างอยู่ใน `AGENTS_EXAMPLE.md`

## สิ่งที่จะออกแบบเพิ่มเติม

ในอนาคต workspace จะมีข้อมูลสำหรับอธิบายความสัมพันธ์ระหว่าง repositories เช่น HTTP calls, events, queues และ identifiers ที่ใช้ map การสื่อสารกลับไปยัง repository เป้าหมาย โดย schema และชื่อไฟล์จะออกแบบแยกในภายหลัง
