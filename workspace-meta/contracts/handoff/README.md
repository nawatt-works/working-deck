# Handoff Contract

Contract นี้กำหนดรูปแบบและความหมายของเอกสารใน `workspace-meta/handoff/` สำหรับ
Project Workspace ที่สร้างจาก Working Deck โดยไม่ผูกกับ producer ใด producer หนึ่ง

กติกาการทำงานของพื้นที่ เช่น หน่วยงานเกิดเมื่อไหร่และใครกำหนด `work_id` อยู่ที่
`workspace-meta/handoff/README.md` ส่วนไฟล์นี้กำหนดเฉพาะรูปแบบที่เครื่องมือตรวจได้

## Ownership

- Project Workspace เป็นเจ้าของเนื้อหาของหน่วยงานที่เกิดขึ้นในตัวเอง
- Working Deck เป็นเจ้าของ contract version, validation rules และ conventions
- producer ทุก role เป็น consumers ที่เท่าเทียมกัน ไม่มี role ใดเป็นเจ้าของพื้นที่
- producer ต้องเก็บ configuration และ artifact ภายในของตัวเองไว้ในตำแหน่งที่
  harness หรือ workflow ของตนกำหนด แล้วใช้พื้นที่นี้เฉพาะของที่ส่งต่อจริง

## Version 1

### Work item

- หนึ่งหน่วยงานคือหนึ่ง direct child directory ใต้ `workspace-meta/handoff/`
- ชื่อ directory คือ `work_id` ซึ่งต้องตรงกับ `YYYYMMDD-<kebab-slug>` และส่วน
  วันที่ต้องเป็นวันที่ที่มีอยู่จริงตามปฏิทิน
- หน่วยงานต้องมี stage file อย่างน้อยหนึ่งไฟล์ · directory ที่ว่างถือว่าผิด
- ไฟล์ที่ระดับ root ของ `workspace-meta/handoff/` ที่ไม่ใช่ `README.md` ถือว่าผิด

### Stage file

- stage file อยู่ที่ระดับ root ของหน่วยงาน ชื่อตรงกับ `<NN>-<stage>.md` โดย
  `NN` เป็นเลขสองหลักที่กำหนดลำดับ และ `stage` เป็น kebab-case
- ลำดับมาตรฐานคือ `00-brief`, `10-plan`, `20-implementation`, `30-audit`
  project เพิ่ม stage อื่นได้ตราบที่ยังคงรูปแบบชื่อไฟล์เดิม
- ภายในหน่วยงานเดียวกัน ทั้งเลขลำดับและชื่อ stage ต้องไม่ซ้ำกัน
- subdirectory ภายในหน่วยงานเป็นที่เก็บไฟล์แนบ contract ไม่กำหนดรูปแบบ

### Frontmatter

stage file ต้องขึ้นต้นด้วย YAML frontmatter ที่คั่นด้วย `---` และมีเฉพาะ fields:

- `work_id` — required · ต้องตรงกับชื่อ directory ของหน่วยงาน
- `stage` — required · ต้องตรงกับส่วน `<stage>` ในชื่อไฟล์
- `status` — required · `draft`, `ready` หรือ `superseded`
- `author` — required · ชื่อ producer เป็น kebab-case
- `repos` — optional · list ของ `repo_id` ที่มีอยู่จริงใน `workspace-meta/repositories.yaml`

ตัวอย่าง:

```yaml
---
work_id: 20260821-order-refund-flow
stage: plan
status: ready
author: planner
repos: [repo_api, repo_web]
---
```

`work_id` และ `stage` ซ้ำกับข้อมูลที่อยู่ในชื่อไฟล์อยู่แล้วโดยตั้งใจ เพื่อให้เนื้อหา
ที่ถูกคัดลอกหรือยกไปแสดงที่อื่นยังบอกได้ว่าตัวเองเป็นของหน่วยงานใด และเพื่อให้
validator จับกรณีที่ไฟล์ถูกย้ายหรือเปลี่ยนชื่อโดยไม่แก้เนื้อหาตาม

ไฟล์ `schema.json` เป็น machine-readable schema ของ frontmatter ส่วนกฎที่ต้องดู
ชื่อไฟล์ ชื่อ directory และ Repository Catalog ประกอบ ตรวจด้วย
`tooling/validate_handoff.py`

## Compatibility

- ห้ามเพิ่ม field เฉพาะ producer เข้า schema version 1
- การเพิ่ม required field หรือเปลี่ยนความหมายเดิมต้องออก schema version ใหม่
- การเพิ่มชื่อ stage ไม่ถือเป็นการเปลี่ยน schema เพราะ contract กำหนดรูปแบบชื่อ
  ไม่ได้กำหนดรายการชื่อที่อนุญาต
- consumer ต้องปฏิเสธเอกสารที่ `status` ไม่ใช่ `ready` แทนการเดาว่าใช้ได้หรือไม่
