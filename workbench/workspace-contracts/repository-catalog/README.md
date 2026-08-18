# Repository Catalog Contract

Contract นี้กำหนดรูปแบบและความหมายของ `workbench/repositories.yaml` สำหรับ
Project Workspace ที่สร้างจาก Working Deck โดยไม่ผูกกับ consumer ใด consumer หนึ่ง

## Ownership

- Project Workspace เป็นเจ้าของ Catalog instance ของตัวเอง
- Working Deck เป็นเจ้าของ contract version, validation rules และ conventions
- Software Factory, Codebase Knowledge และระบบอื่นเป็น consumers ที่เท่าเทียมกัน
- Consumer ต้องเก็บ configuration, artifacts และ lifecycle ของตัวเองแยกจาก Catalog แล้วอ้าง repository ด้วย `repo_id`

## Version 1

Catalog ต้องมี `schema_version: 1` และ `repositories` ซึ่งเป็น list ของรายการที่มีเฉพาะ:

- `repo_id` — stable identity ที่ไม่ซ้ำและตรงกับ `repo_<snake_case_name>`
- `path` — path ที่ไม่ซ้ำและเป็น direct child ใต้ `repos/`

direct child directory ทุกแห่งใต้ `repos/` ต้องอยู่ใน Catalog แต่ Catalog entry สามารถมีอยู่ก่อน checkout บนเครื่องปัจจุบันได้

ไฟล์ `schema.json` เป็น machine-readable schema ส่วนกฎ uniqueness ระหว่างรายการและความสอดคล้องกับ directory จริงตรวจด้วย `tooling/validate_repository_catalog.py`

## Compatibility

- ห้ามเพิ่ม field เฉพาะ consumer เข้า schema version 1
- การเพิ่ม required field หรือเปลี่ยนความหมายเดิมต้องออก schema version ใหม่
- Consumer ต้อง reject schema version ที่ตนไม่รองรับแทนการเดาความหมาย
