# SAGA FLOW — Robot AgroTech Vivero — Backend General
## Version 1.0 | Java 17 + Spring Boot 3.2 | March 2026

---

## 1. System Overview

```
ROBOT (Raspberry Pi / Python)
        │
        │  HTTP REST + WebSocket
        ▼
BACKEND LOCAL (Spring Boot :8080)
        │
        ├──► PostgreSQL  (structured data + image paths)
        ├──► Docker Volume /app/images  (image files)
        └──► Notification Service  (Email / WhatsApp / Telegram / SMS)
        ▲
        │  HTTP REST + WebSocket
FRONTEND (React :3000)
        │
USER (operator / admin / viewer — browser)
```

---

## 2. Modules and Responsibilities

| Module    | Responsibility                                               | Base path    |
|-----------|--------------------------------------------------------------|--------------|
| `auth`    | Login, register, JWT issue, token refresh                    | `/auth/**`   |
| `users`   | User management and role assignment (ADMIN/OPERATOR/VIEWER)  | `/users/**`  |
| `plants`  | Plant registry by QR code, state history                     | `/plants/**` |
| `patrols` | Robot patrol sessions, AI classification results             | `/patrols/**`|
| `robot`   | Control commands, status, camera stream (WebSocket)          | `/robot/**`  |
| `reports` | Report generation, PDF export, notification dispatch         | `/reports/**`|

---

## 3. Flow: Automatic Patrol

```
1. USER clicks "Start patrol" on frontend
        │
        ▼
2. Frontend → POST /api/patrols/start
   { "mode": "AUTO", "filter": "ALL" }
        │
        ▼
3. Backend creates Patrol record in DB  (status: IN_PROGRESS)
   Backend → Robot: START_PATROL command
        │
        ▼
4. Robot follows line → detects QR code of Plant #001
        │
        ▼
5. Robot captures burst of 3 photos (left camera, front, right)
        │
        ▼
6. Robot runs TFLite model locally → classifies: DANGER
        │
        ▼
7. Robot → POST /api/patrols/{id}/result
   {
     "plantQr":    "PLANT-001",
     "aiResult":   "DANGER",
     "confidence": 0.91,
     "images":     [...],
     "timestamp":  "2026-03-18T14:30:00"
   }
        │
        ▼
8. Backend saves images to /app/images/patrols/{patrolId}/plant-001/
   Backend saves image paths in DB (observations table)
   Backend updates plant state in DB
        │
        ▼
9. Backend → WebSocket broadcast to frontend
   { "event": "PLANT_CLASSIFIED", "plantId": 1, "state": "DANGER" }
        │
        ▼
10. Frontend updates dashboard in real time (no page reload)
        │
        ▼
11. Robot advances → next plant → repeats steps 4–10
        │
        ▼
12. Robot finishes → POST /api/patrols/{id}/complete
        │
        ▼
13. Backend closes Patrol record (status: COMPLETED)
    Backend generates automatic report
    Backend dispatches notifications per user preferences
        │
        ▼
14. Frontend shows patrol summary
```

---

## 4. Flow: Manual Robot Control

```
1. USER activates "Manual Mode" on frontend
        │
        ▼
2. Frontend → POST /api/robot/command
   { "action": "SET_MODE", "mode": "MANUAL" }
        │
        ▼
3. Backend → Robot: disable line follower
        │
        ▼
4. USER presses key (WASD / arrows) or uses on-screen joystick
        │
        ▼
5. Frontend → WebSocket /api/ws/robot/control
   { "direction": "FORWARD", "speed": 50 }
        │
        ▼
6. Backend relays → Robot: move motors
        │
        ▼
7. Robot sends position/status every 500ms → WebSocket → Frontend
```

---

## 5. Flow: Go to Specific Plant

```
1. USER selects "Go to Plant #007" on frontend
        │
        ▼
2. Frontend → POST /api/robot/command
   { "action": "GOTO_PLANT", "plantQr": "PLANT-007" }
        │
        ▼
3. Backend verifies plant exists → forwards command to robot
        │
        ▼
4. Robot activates automatic mode with specific destination
   Robot navigates to QR code of Plant #007
        │
        ▼
5. Robot arrives → activates camera stream
   Robot → WebSocket → Backend → Frontend: live video frames
        │
        ▼
6. USER remotely analyzes plant visual state
   USER can manually flag additional causes from the interface
        │
        ▼
7. Frontend → POST /api/plants/{id}/observations
   {
     "notes": "Brown spot on leaf edge",
     "additionalCauses": ["FUNGUS", "OVERWATERING"]
   }
```

---

## 6. Flow: Report Generation and Dispatch

```
1. Trigger: patrol completed  OR  manual user request
        │
        ▼
2. Backend → ReportService.generate(patrolId)
        │
        ├── Queries all observations for the patrol
        ├── Groups by state (HEALTHY / ATTENTION / DANGER)
        ├── Loads images from volume /app/images
        └── Generates PDF using iText8
        │
        ▼
3. Backend saves PDF to /app/images/reports/report-{id}.pdf
   Backend saves path in DB (reports table)
        │
        ▼
4. Backend reads NotificationConfig for the user
        │
        ├── email     → JavaMailSender → sends PDF as attachment
        ├── whatsapp  → Twilio API     → sends message + PDF link
        ├── telegram  → Bot API        → sends message + PDF file
        └── sms       → Twilio SMS     → sends text summary
        │
        ▼
5. Frontend → GET /api/reports/{id}/pdf → downloads PDF
```

---

## 7. Role-Based Access Control (RBAC)

| Role       | Permissions                                                          |
|------------|----------------------------------------------------------------------|
| `ADMIN`    | Full access: manage users, assign roles, view all, control robot     |
| `OPERATOR` | Control robot, view reports, add manual observations                 |
| `VIEWER`   | Read-only: view reports and plant states (no robot control)          |

---

## 8. Image Directory Structure (Docker Volume)

```
/app/images/
├── patrols/
│   ├── patrol-001/
│   │   ├── plant-001/
│   │   │   ├── left_20260318_143022.jpg
│   │   │   ├── front_20260318_143023.jpg
│   │   │   └── right_20260318_143024.jpg
│   │   └── plant-002/
│   │       └── ...
│   └── patrol-002/
│       └── ...
└── reports/
    ├── report-001.pdf
    └── report-002.pdf
```

---

## 9. Standard Module Structure (repeated across all modules)

```
module/
└── {name}/
    ├── controller/
    │   └── {Name}Controller.java      — REST endpoints, no business logic
    ├── service/
    │   ├── {Name}Service.java         — service interface
    │   └── impl/
    │       └── {Name}ServiceImpl.java — business logic implementation
    ├── repository/
    │   └── {Name}Repository.java      — Spring Data JPA
    ├── entity/
    │   └── {Name}.java                — database table mapping
    ├── dto/
    │   ├── {Name}RequestDto.java      — input (what the API receives)
    │   └── {Name}ResponseDto.java     — output (what the API returns)
    └── mapper/
        └── {Name}Mapper.java          — MapStruct Entity <-> DTO
```

---

## 10. Development Order

```
Phase 1 — Foundation
  [x] pom.xml · application.yml · Dockerfile · docker-compose.yml
  [x] BaseEntity · ApiResponse · GlobalExceptionHandler · Custom exceptions

Phase 2 — Security
  [ ] auth module (JWT + login + register + refresh token)
  [ ] SecurityConfig + JwtAuthFilter

Phase 3 — Master data
  [ ] users module (CRUD + role management)
  [ ] plants module (QR registry + state history)

Phase 4 — Robot operation
  [ ] patrols module (sessions + AI results)
  [ ] robot module (commands + WebSocket + camera stream)

Phase 5 — Reports and notifications
  [ ] reports module (PDF + email + WhatsApp + Telegram)

Phase 6 — Frontend
  [ ] React + Tailwind + shadcn/ui
  [ ] Dashboard + robot control + reports + notifications
```
