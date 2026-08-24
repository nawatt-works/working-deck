# Mission Control

พื้นที่ควบคุมและประสานงานของ project workspace แยกออกจาก repository ที่เป็นตัวงาน
จริงอย่างชัดเจน

Mission Control เป็นเจ้าของ metadata, contracts และ automation ระดับ workspace
ที่ใช้สนับสนุนการทำงานข้ามหลาย repository แต่ไม่ได้เป็นเจ้าของ source code หรือ
workflow ภายใน repository เหล่านั้น

## โครงสร้าง

```text
_Mission-Control/
├── AGENTS.md          # กติกาเฉพาะพื้นที่ Mission Control
├── README.md          # อธิบายบทบาทและ boundary
├── workspace-meta/    # shared workspace metadata และ contracts
└── tooling/           # automation สำหรับดูแล workspace
```

ไฟล์ instruction และ policy ที่ต้องให้ AI harness ค้นพบจาก workspace root เช่น
`AGENTS.md` (หรือ `AGENTS_EXAMPLE.md` ก่อน bootstrap), `GIT_POLICY.md` รวมถึง
directory ที่ harness กำหนดตำแหน่งเอง เช่น `.agents/` ยังคงอยู่ที่ root ไม่จำเป็น
ต้องย้ายเข้ามาในโฟลเดอร์นี้

## หลักการใช้งาน

- เก็บ production source code, repository-owned tests, fixtures และ configuration
  ใน repository ที่เกี่ยวข้องใต้ `repos/`
- เก็บข้อมูลกลางที่หลาย harness หรือ automation ใช้ร่วมกันใน `workspace-meta/`
  ตาม contract ของข้อมูลแต่ละชนิด
- เก็บ automation ของ control plane ใน `tooling/`
- artifact ที่ harness เป็นเจ้าของให้คงอยู่ในตำแหน่งที่ harness นั้นกำหนด และให้
  consumer อื่นอ่านจากตำแหน่งดังกล่าวตาม contract หรือ convention ของเจ้าของ
- ไฟล์ชั่วคราวให้อยู่ใน temporary directory ของ harness หรือระบบ
- ใช้ planning, handoff หรือ agent delegation เมื่อช่วยให้งานส่งต่อหรือตรวจสอบได้
  ดีขึ้น ไม่ใช่ขั้นตอนบังคับสำหรับงานทุกประเภท

การอยู่ใน Mission Control ไม่ได้ให้สิทธิ์ AI อ่าน เขียน execute หรือ push repository
ใดโดยอัตโนมัติ สิทธิ์และ Git safety ยังคงเป็นไปตาม root instructions,
`GIT_POLICY.md` และกติกาของ repository เป้าหมาย
