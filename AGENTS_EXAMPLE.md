# Workspace Guidelines

Workspace นี้แบ่งข้อมูลออกเป็น 3 พื้นที่หลัก ได้แก่ `.workbench/`, `.runtime/`
และ `repos/` ส่วนไฟล์ที่ root เช่น `.code-workspace` และ `tooling/` ใช้ควบคุมและ
ดูแล workspace โดยรวม

## `.workbench/` — พื้นที่ทำงานร่วมกัน

- ใช้เก็บข้อมูลและเอกสารที่มนุษย์กับ AI ใช้ร่วมกัน แต่ไม่ใช่ source code ของผลิตภัณฑ์
- ตัวอย่าง: แผนงาน, specification, architecture, research, decision record, บันทึกการทำงาน และหลักฐานการประเมิน
- หากงานเป็นการวิเคราะห์ วางแผน วิจัย หรือจัดทำเอกสารประกอบ และยังไม่ใช่ผลลัพธ์ของ repository ใดโดยตรง ให้จัดเก็บไว้ที่นี่
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

## `repos/` — External repositories

- ใช้เก็บ checkout ของ Git repositories ที่เป็นตัวงานจริงหรือสนับสนุนการทำงาน เช่น backend, frontend, API, consumer, worker, library, infrastructure, documentation, test environment, agent skill, extension หรือ automation
- แต่ละโฟลเดอร์ระดับแรกภายใต้ `repos/` โดยปกติต้องเป็น Git repository อิสระจาก root workspace และอาจเป็น repository ที่บุคคลหรือทีมภายนอกเป็นเจ้าของ
- repository ภายใต้ `repos/` อาจเป็น single-project repository หรือ monorepo ที่ประกอบด้วยหลาย applications, services, packages หรือ libraries ก็ได้
- ห้ามอนุมานโครงสร้างภายใน repository จากตำแหน่งที่อยู่ใต้ `repos/` ให้ตรวจ configuration, documentation และคำแนะนำของ repository เป้าหมายก่อนทำงานเสมอ
- ในเอกสารของ workspace นี้ คำว่า **workspace repository** หรือ **repo** หมายถึง direct child directory ใต้ `repos/` ซึ่งโดยปกติควรเป็น Git checkout ส่วน **cataloged repository** หมายถึง repo ที่มีรายการอยู่ใน `.workbench/repositories.yaml`
- คำว่า repository ที่พบภายใน source code เช่น repository pattern, data repository, `Repository<T>` หรือ class ที่ลงท้ายด้วย `Repository` เป็นแนวคิดภายในตัวงาน ไม่ถือเป็น workspace repository หรือ cataloged repository
- `.workbench/repositories.yaml` เป็น authoritative Repository Catalog ของ repositories ทั้งหมดที่เป็นสมาชิกของ project workspace
- `repos/` ต้องมีเฉพาะ workspace repositories ดังนั้น direct child directory ทุกแห่งใต้ `repos/` ต้องมีรายการใน Repository Catalog หากพบ directory ที่ไม่มีรายการ ให้ถือว่า Catalog drift และเพิ่มเข้า catalog
- cataloged repository อาจยังไม่มี checkout บนเครื่องปัจจุบันได้ ให้แจ้ง warning และห้ามลบรายการออกจาก Catalog โดยอัตโนมัติเพียงเพราะ directory ไม่มีอยู่
- การอยู่ใน Repository Catalog ไม่ได้ให้สิทธิ์ AI อ่าน เขียน หรือ execute repository ไม่ได้บังคับให้ codebase knowledge index repository และไม่ได้หมายความว่า repository นั้นต้องเป็น application source code
- repository ที่เป็น test environment, documentation, agent skill, extension, fixture หรือ automation สามารถอยู่ใน catalog ได้แม้ไม่ต้องถูก codebase knowledge index
- `repos/*` ถูก ignore จาก root Git repository ห้ามสมมติว่า root workspace และ repositories เหล่านี้รวมกันเป็น monorepo หรือใช้ Git history, branch, staging area, dependencies หรือ tooling ร่วมกัน ทั้งนี้ repository แต่ละแห่งอาจเป็น monorepo ภายในขอบเขตของตัวเองได้
- ก่อนเรียก Git command หรือเครื่องมือเฉพาะ repository ให้เปลี่ยน working directory เข้า repository เป้าหมายก่อน
- การแก้ไขแต่ละ repository ต้องจำกัดเฉพาะงานที่ผู้ใช้ร้องขอ และต้องปฏิบัติต่อ repository อื่นเป็นขอบเขตอิสระ
- ห้าม commit secrets หรือ credentials ส่วน credential files ที่จำเป็นต่อ local development ต้องเป็นรูปแบบที่ repository นั้นอนุญาตและถูก ignore จาก Git

## AI Harness Isolation

- root workspace เป็นพื้นที่ coordination ระหว่างผู้ใช้กับ AI ส่วน `repos/*` เป็น external repositories
- ไฟล์และโฟลเดอร์สำหรับการทำงานร่วมกันระหว่างผู้ใช้กับ AI ของ workspace นี้ต้องเก็บไว้ใน root workspace, `.workbench/`, `.runtime/` หรือตำแหน่งที่ root workspace กำหนดเท่านั้น
- ห้ามเพิ่ม คัดลอก หรือ generate AI harness configuration ของ workspace นี้ลงใน `repos/*` เว้นแต่ผู้ใช้สั่งให้เปลี่ยน repository นั้นโดยตรง
- ตัวอย่างไฟล์ที่ห้ามเพิ่มโดยไม่ได้รับคำสั่งอย่างชัดเจน ได้แก่ `AGENTS.md`, `CLAUDE.md`, `.agents/`, `.claude/` และ configuration ที่มีวัตถุประสงค์ใกล้เคียงกัน
- AI harness configuration ที่มีอยู่แล้วภายใน `repos/*` ถือเป็นไฟล์ของ external repository ห้ามแก้ไข ลบ เปลี่ยนชื่อ หรือเขียนทับ เว้นแต่ผู้ใช้ร้องขอการเปลี่ยนแปลงไฟล์นั้นโดยตรง
- ห้ามตั้งใจนำ AI harness configuration ภายใน `repos/*` มาใช้เป็น coordination configuration ของ root workspace การป้องกันไม่ให้ provider โหลดไฟล์เหล่านั้นโดยอัตโนมัติต้องจัดการแยกตาม provider
- ห้ามนำ notes, plans, prompts, evaluation evidence, handoff records หรือ coordination artifacts ส่วนตัวไปเก็บหรือ commit ภายใน `repos/*`
- ก่อน commit ภายใน repository ใด ให้ตรวจสอบว่าไม่มี artifact ของ root workspace หรือ AI harness configuration ที่เกิดขึ้นโดยไม่ตั้งใจรวมอยู่ใน change set

## Workspace Tooling

- `tooling/` ใช้เก็บ automation ที่ดูแล root workspace และไม่ใช่ source code ของ repository ใดภายใต้ `repos/`
- `.workbench/repositories.yaml` เป็น source of truth สำหรับ cataloged repositories โดยใช้ `schema_version: 1` และแต่ละรายการมีเฉพาะ stable `repo_id` รูปแบบ `repo_<snake_case_name>` กับ `path` ที่เป็น direct child ใต้ `repos/`
- access policy, indexing configuration, integration mapping และ generated knowledge ต้องเก็บแยกจาก Repository Catalog และอ้าง repository ด้วย `repo_id`
- tool-specific configuration ต้องเป็นผู้เลือกว่าจะใช้หรือไม่ใช้ cataloged repository ใด ห้ามใช้การลบ repository ออกจาก Catalog เพื่อควบคุม access, indexing หรือ behavior ของเครื่องมือ
- `.code-workspace` เป็น generated และ committed editor projection ที่รวม cataloged repositories ทุกแห่ง เพื่อให้ VS Code ที่เปิดจาก root workspace ค้นพบ repositories ใต้ `repos/` ซึ่งถูก root Git repository ignore
- เมื่อแก้ `.workbench/repositories.yaml` ให้ generate `.code-workspace` ใหม่ด้วย `python3 tooling/generate_vscode_workspace.py` และตรวจความสอดคล้องด้วย `python3 tooling/generate_vscode_workspace.py --check`
- workspace tooling ห้ามเขียนไฟล์ลงใน `repos/*` เว้นแต่คำสั่งนั้นมีวัตถุประสงค์เพื่อแก้ตัวงานใน repository และผู้ใช้ร้องขออย่างชัดเจน

## หลักการเลือกตำแหน่งไฟล์

- เอกสารสำหรับการคิดและการทำงานร่วมกัน → `.workbench/`
- source code, committed tests, reusable fixtures, configuration และ repository-owned build artifacts → `repos/<repository-name>/`
- ไฟล์ชั่วคราว การทดลอง generated fixtures และผลลัพธ์ระหว่างทาง → `.runtime/`
- root workspace automation → `tooling/`
- build artifacts ภายใน repository ให้อยู่ในตำแหน่งมาตรฐานของ repository และต้องไม่ถูก commit เว้นแต่ repository ระบุไว้เป็นอย่างอื่น
- อย่าวาง source code ของ repository ไว้ที่ workspace root, `.workbench/` หรือ `tooling/`

## Git Workflow

ก่อน merge feature branch เข้า integration branch ของ repository เป้าหมาย ให้ตรวจสอบ workflow และคำแนะนำของ repository นั้นก่อน ห้ามใช้ Git workflow ของ root workspace ครอบ external repositories โดยอัตโนมัติ

## ภาษา

- ใช้ภาษาไทยเป็นภาษาเริ่มต้นในการพูดคุยกับผู้ใช้
- เอกสาร เนื้อหา และข้อความสำหรับมนุษย์ที่ AI สร้างขึ้นต้องใช้ภาษาไทยเป็นหลัก
- ชื่อเฉพาะ ศัพท์เทคนิค identifiers, source code, commands และข้อความที่ต้องตรงกับระบบ สามารถคงภาษาเดิมไว้ได้
- executable contracts เช่น prompts, skills, schemas, exact labels, test expectations และข้อความที่ต้องรักษา model หรือ tool compatibility สามารถใช้ภาษาอังกฤษหรือภาษาที่เหมาะกับ runtime ได้
- historical artifacts, regression evidence และข้อความที่ต้องคงรูปเพื่อ trace หรือเปรียบเทียบผล ไม่ต้องแปลย้อนหลัง
- หากผู้ใช้ระบุภาษาอื่นอย่างชัดเจน ให้ปฏิบัติตามภาษาที่ผู้ใช้ร้องขอสำหรับงานนั้น
