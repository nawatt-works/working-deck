# Workspace Guidelines

Workspace นี้แบ่งออกเป็น 3 พื้นที่หลัก:

## `.workbench/` — พื้นที่ทำงานร่วมกัน

- ใช้เก็บข้อมูลและเอกสารที่มนุษย์กับ AI ใช้ร่วมกัน แต่ไม่ใช่ source code ของผลิตภัณฑ์
- ตัวอย่าง: แผนงาน, specification, architecture, research, decision record, บันทึกการทำงาน และหลักฐานการประเมิน
- หากงานเป็นการวิเคราะห์ วางแผน วิจัย หรือจัดทำเอกสารประกอบ และยังไม่ใช่ผลลัพธ์ของ app ใดโดยตรง ให้จัดเก็บไว้ที่นี่
- ห้ามเก็บ secrets, access tokens, credentials หรือข้อมูลรับรองตัวตนใน `.workbench/`

## `.runtime/` — ไฟล์ชั่วคราวภายใน workspace

- ใช้เก็บไฟล์ชั่วคราวที่ AI สร้างขึ้นระหว่างทำงาน เช่น generated fixtures, generated samples, cache, logs, extracted files และผลลัพธ์ระหว่างทาง
- หากเครื่องมือหรือคำสั่งรองรับการกำหนด temporary directory ให้กำหนดเป็น `.runtime/` หรือโฟลเดอร์ย่อยภายในนั้น
- แยกไฟล์ของแต่ละงานไว้ในโฟลเดอร์ย่อยที่สื่อความหมาย เพื่อลดการชนกันและทำให้ตรวจสอบหรือลบภายหลังได้ง่าย
- ห้ามใช้ `.runtime/` เก็บ source code, committed tests, reusable test fixtures หรือ deliverable ฉบับสุดท้าย
- เมื่อผลลัพธ์ใน `.runtime/` กลายเป็น decision, reusable evidence หรือ checkpoint ที่ต้องเก็บถาวร ให้สรุปหรือย้ายเฉพาะส่วนที่จำเป็นไป `.workbench/`
- AI ห้ามเขียนไฟล์นอก workspace นี้ เว้นแต่ผู้ใช้อนุญาตอย่างชัดเจน หรือเป็นไฟล์ภายในที่ระบบหรือเครื่องมือจัดการเองและไม่สามารถกำหนดตำแหน่งได้
- ก่อนลบหรือเขียนทับไฟล์ที่มีอยู่ใน `.runtime/` ให้ตรวจสอบก่อนว่าไม่ได้เป็นข้อมูลของผู้ใช้หรืองานอื่น
- ห้ามเก็บ secrets, access tokens, credentials หรือข้อมูลรับรองตัวตนใน `.runtime/`

## `apps/` — ตัวงานและผลลัพธ์จริง

- ใช้เก็บ source code, committed tests, reusable test fixtures, configuration และ deliverables ที่เป็นตัวงานจริง
- แต่ละโฟลเดอร์ระดับแรกภายใต้ `apps/` โดยปกติเรียกว่า **app** เช่น `apps/user/` เรียกว่า User app
- แต่ละ app อาจเป็น backend application, frontend application, API, consumer, worker, reporting application, library หรือ executable รูปแบบอื่น
- แต่ละ app อาจเป็น Git repository อิสระ และมี dependencies, tooling, configuration และคำสั่งพัฒนาของตัวเอง
- ห้ามสมมติว่า `apps/` เป็น monorepo เว้นแต่มี configuration หรือเอกสารระบุไว้อย่างชัดเจน
- ก่อนแก้ไข app ให้ตรวจหาและปฏิบัติตาม `AGENTS.md` หรือคำแนะนำเฉพาะภายใน app นั้นก่อน โดยคำแนะนำที่อยู่ใกล้ไฟล์เป้าหมายกว่าจะมีผลก่อน
- ก่อนเรียกคำสั่งหรือเครื่องมือเฉพาะ app ให้เปลี่ยน working directory เข้า app นั้นก่อน เว้นแต่เอกสารของ app ระบุว่าสามารถเรียกจาก workspace root ได้
- app สามารถกำหนด `.workbench/`, `.runtime/` หรือโครงสร้างภายในของตัวเองผ่าน nested `AGENTS.md`
- ห้าม commit secrets หรือ credentials ส่วน credential files ที่จำเป็นต่อ local development ต้องเป็นรูปแบบที่ app อนุญาตและถูก ignore จาก Git

## หลักการเลือกตำแหน่งไฟล์

- เอกสารสำหรับการคิดและการทำงานร่วมกัน → `.workbench/`
- source code, committed tests, reusable fixtures, configuration และ app-owned build artifacts → `apps/<app-name>/`
- ไฟล์ชั่วคราว การทดลอง generated fixtures และผลลัพธ์ระหว่างทาง → `.runtime/`
- build artifacts ภายใน app ให้อยู่ในตำแหน่งมาตรฐานของ app และต้องไม่ถูก commit เว้นแต่ app ระบุไว้เป็นอย่างอื่น
- อย่าวาง source code ของ app ไว้ที่ workspace root หรือใน `.workbench/`

## Git Workflow

ก่อน merge feature branch เข้า `main` ให้ rebase กับ `main` ล่าสุดและตรวจสอบผลบน rebased tip ก่อน จากนั้น merge แบบสร้าง merge commit เพื่อรักษาจุดรวม change set ที่ตรวจภาพรวมได้ เว้นแต่ผู้ใช้ระบุวิธีอื่นอย่างชัดเจน

## ภาษา

- ใช้ภาษาไทยเป็นภาษาเริ่มต้นในการพูดคุยกับผู้ใช้
- เอกสาร เนื้อหา และข้อความสำหรับมนุษย์ที่ AI สร้างขึ้นต้องใช้ภาษาไทยเป็นหลัก
- ชื่อเฉพาะ ศัพท์เทคนิค identifiers, source code, commands และข้อความที่ต้องตรงกับระบบ สามารถคงภาษาเดิมไว้ได้
- executable contracts เช่น prompts, skills, schemas, exact labels, test expectations และข้อความที่ต้องรักษา model หรือ tool compatibility สามารถใช้ภาษาอังกฤษหรือภาษาที่เหมาะกับ runtime ได้
- historical artifacts, regression evidence และข้อความที่ต้องคงรูปเพื่อ trace หรือเปรียบเทียบผล ไม่ต้องแปลย้อนหลัง
- หากผู้ใช้ระบุภาษาอื่นอย่างชัดเจน ให้ปฏิบัติตามภาษาที่ผู้ใช้ร้องขอสำหรับงานนั้น
