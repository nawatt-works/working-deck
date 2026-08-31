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

- `git-safety.yaml` ลงทะเบียน exact workspace-relative path และ `client`/`own` class ของทุก work repository
- Work repositories วางที่ใดก็ได้ใต้ workspace ยกเว้น `_Mission-Control/`; `repos/` เป็น default convention เท่านั้น
- Repository ที่ค้นพบแต่ยังไม่ลงทะเบียน fail closed เป็น `client`
- `git_guard.py status` ตรวจ registry, repository discovery, root ignore, branches, upstreams, pending coordination artifacts และ hook state
- `git_guard.py install` ติดตั้ง pre-push guard โดยไม่เขียนทับ hook configuration เดิม
- `hooks/pre-push` เป็น template ที่ installer ฝัง absolute workspace path ลงใน local hook เพื่อไม่เชื่อถือไฟล์จาก work repository; เมื่อย้าย workspace ต้องติดตั้งใหม่

กฎ remote write ฉบับเต็มอยู่ที่ `GIT_POLICY.md` ที่ workspace root

## Boundary

- Source code, tests และ configuration ของตัวงานอยู่ใน registered work repository ไม่ว่าจะใช้ path ใด
- ห้ามวาง work repository ใต้ `_Mission-Control/`
- Tooling ที่ดูแลหลาย repositories อยู่ใน `_Mission-Control/tooling/`
- Instructions สำหรับ workspace ปลายทางเริ่มจาก `AGENTS_EXAMPLE.md` และยัง inert จนกว่าผู้ใช้จะ rename หรือทำ symlink เอง
- Temporary files ใช้ temporary directory ของระบบหรือ harness
- ห้ามเก็บ secrets, credentials, tokens หรือ private keys ใน Mission Control

Mission Control เป็น extensible collaboration control plane ส่วน Git safety เป็น subsystem แรก ไม่ใช่ขอบเขตสุดท้ายของพื้นที่นี้
