# Workspace Metadata

พื้นที่ metadata และ contract กลางของ Working Deck สำหรับข้อมูลที่ project
workspace เป็นเจ้าของเอง และต้องการให้หลาย harness, skill หรือ automation อ้างร่วมกัน

โฟลเดอร์นี้ไม่ใช่พื้นที่บังคับสำหรับ artifact ทั้งหมดที่ AI หรือ harness สร้างขึ้น
หาก harness ใดมีตำแหน่งหรือ format ของตัวเอง เช่น `.claude/`, `.agents/`,
`.my-harness/` หรือโฟลเดอร์อื่น ให้ใช้ convention ของ harness นั้นได้ตามปกติ
ตราบใดที่ไม่คัดลอก coordination artifact เข้า repository ใต้ `repos/*`

## โครงสร้าง

```text
workspace-meta/
├── README.md              # กติกาของพื้นที่ metadata กลาง
├── repositories.yaml      # shared — Repository Catalog
├── handoff/               # shared — งานที่ส่งต่อระหว่าง producer
└── contracts/             # shared — contract ของไฟล์ที่ใช้ร่วมกัน
```

## กติกา

### 1. เก็บเฉพาะข้อมูลกลางที่ Working Deck เป็นเจ้าของ

ไฟล์ใน `workspace-meta/` ต้องเป็น metadata, contract หรือ state ที่ workspace
ตั้งใจให้เป็นของกลาง เช่น Repository Catalog, handoff contract หรือ file instance
ที่มี contract ชัดเจน

ไฟล์ที่ระดับ `workspace-meta/` root เป็นของกลาง แก้ได้เมื่อผู้ใช้ร้องขอ เมื่อทำตาม
workflow ที่ contract ของไฟล์นั้นกำหนดไว้ หรือเมื่อกำลังเพิ่ม workspace metadata
ชนิดใหม่พร้อมกติกาและเครื่องมือตรวจที่เหมาะสมกับงานนั้น

`handoff/` เป็นพื้นที่ส่งต่องานระหว่าง producer ที่ทำหน้าที่
ต่างกัน สิทธิ์เขียนที่นั่นกำหนดด้วย stage ไม่ใช่ตำแหน่ง artifact ของ producer เพราะเอกสารส่งต่อถูกเขียน
ให้คนอื่นเอาไปทำต่อ เจ้าของจึงเป็นตัวงานไม่ใช่ผู้เขียน กติกาอยู่ใน
`workspace-meta/handoff/README.md`

### 2. ของที่ shared ต้องมี contract

ไฟล์จะขึ้นมาอยู่ระดับ `workspace-meta/` root ได้เมื่อเป็น shared workspace metadata
ที่ตั้งใจให้หลาย producer อ้างร่วมกัน ต้องมี contract อยู่ใน `contracts/` หรือเพิ่ม
contract นั้นในงานเดียวกัน หากรูปแบบไฟล์ต้องให้ automation อ่าน ควรมี schema หรือ
validator ที่ตรวจได้ด้วย

การที่ producer อื่นอยากอ่าน artifact หนึ่งไม่ใช่เหตุผลเพียงพอที่จะย้าย artifact
นั้นเข้ามาใน `workspace-meta/` หาก artifact นั้นเป็น output ของ harness ที่มี
ตำแหน่งและ contract ของตัวเอง ให้ producer อื่นอ่านจากตำแหน่งนั้นตาม convention
ของ harness เจ้าของ

### 3. เชื่อมกันด้วย `repo_id` เท่านั้น

เมื่อ artifact ต้องอ้างถึง repository ให้อ้างด้วย `repo_id` จาก
`repositories.yaml` ห้ามอ้าง path ภายใต้ `repos/` โดยตรง เว้นแต่ contract นั้นระบุไว้

## ข้อห้าม

- **ห้ามเก็บของที่ใช้เข้าถึงระบบได้** — secrets, access token, credential, private key,
  session หรือ connection string ที่มีรหัสผ่าน
  **เกณฑ์ตัดสิน: ถ้าสิ่งนี้หลุดออกไป มีคนเอาไปสวมรอยหรือเข้าระบบได้ไหม**
- **ชื่อหรือ handle ของผู้ร่วมงานเก็บได้** เมื่อเป็นส่วนหนึ่งของบันทึกการทำงาน เช่น
  ใครรีวิว ใครอนุมัติ · เก็บเท่าที่งานต้องใช้ ไม่เก็บที่อยู่ติดต่อโดยไม่จำเป็น
- ห้ามเก็บไฟล์ชั่วคราว ให้ใช้ temporary directory ของ harness หรือระบบแทน
- ห้ามเก็บ source code ของ repository ใด ตัวงานจริงอยู่ใน `repos/` เท่านั้น
- ห้ามสร้างโฟลเดอร์หมวดหมู่ทิ้งไว้ว่างๆ เพื่อรอให้มีคนมาเติม
- ห้ามคัดลอกหรือ commit เนื้อหาในพื้นที่นี้เข้า repository ใต้ `repos/`
