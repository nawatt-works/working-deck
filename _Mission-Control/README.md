# Mission Control

ศูนย์กลางการทำงานร่วมกันระหว่างผู้ใช้กับ agent harness ในระดับ workspace

Mission Control อาจเก็บบริบท กฎร่วม เครื่องมือ หรือ artifact ที่ต้องใช้ข้ามหลาย repositories และหลาย harness แต่ไม่ใช่พื้นที่สำหรับ production source code และไม่บังคับให้ทุกงานต้องมี plan, schema, catalog หรือ handoff

เพิ่ม capability ใหม่เมื่อมี use case จริงเท่านั้น ไม่สร้างโครงสร้างหรือ contract รอไว้ล่วงหน้า

## ความสามารถปัจจุบัน: Git safety

```text
_Mission-Control/
├── README.md
├── git-safety.yaml
├── hooks/
│   └── pre-push
└── tooling/
    ├── git_guard.py
    └── tests/
```

- `git-safety.yaml` จัดทุก repository เป็น `client` โดย default และเก็บเฉพาะ path ที่ผู้ใช้ยืนยันว่าเป็น `own`
- `git_guard.py status` ตรวจ repositories, branches, upstreams, pending coordination artifacts และ hook state
- `git_guard.py install` ติดตั้ง pre-push guard โดยไม่เขียนทับ hook configuration เดิม
- `hooks/pre-push` เป็น template ที่ installer นำไปวางใน Git directory ซึ่งไม่ถูก commit เข้า work repository

กฎ remote write ฉบับเต็มอยู่ที่ `GIT_POLICY.md` ที่ workspace root

## Boundary

- Source code, tests และ configuration ของตัวงานอยู่ใน `repos/<name>/`
- Tooling ที่ดูแลหลาย repositories อยู่ใน `_Mission-Control/tooling/`
- Instructions สำหรับ workspace ปลายทางเริ่มจาก `AGENTS_EXAMPLE.md` และยัง inert จนกว่าผู้ใช้จะ rename หรือทำ symlink เอง
- Temporary files ใช้ temporary directory ของระบบหรือ harness
- ห้ามเก็บ secrets, credentials, tokens หรือ private keys ใน Mission Control

Mission Control เป็น extensible collaboration control plane ส่วน Git safety เป็น subsystem แรก ไม่ใช่ขอบเขตสุดท้ายของพื้นที่นี้
