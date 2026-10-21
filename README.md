# Campus Attendance Bot - Dire Dawa University (DDU)

An enterprise-grade, asynchronous Telegram-based attendance management system built for Dire Dawa University (DDU) using Python, Aiogram 3, and SQLite with Write-Ahead Logging (WAL) concurrency.

## System Architecture
- **Frontend Client:** Telegram Platform (Cross-platform on Android, iOS, Desktop, and Web).
- **Backend Service:** Python 3 (Aiogram 3, Asyncio).
- **Database Layer:** SQLite with Write-Ahead Logging (WAL) enabled for high-concurrency parallel writes.
- **Document Engine:** Vector-based PDF report generation using ReportLab.

## Core Features
1. **Multi-Course Administration:** Authorized instructors can configure and oversee multiple distinct courses across different departments, academic years, and semesters.
2. **Deep-Link Enrollment via Class Representatives (CR):** Generates unique Telegram deep-links forwarded by instructors to Class Representatives for streamlined student account onboarding.
3. **Timed Anti-Cheat In-Class Sessions:** Generates a randomized 4-digit PIN with a strict 60-second time-restricted window to eliminate remote proxy check-ins from dormitories.
4. **Dead Phone / No-Device Manual Override:** Real-time missing student roster allowing instructors to verify and mark students with depleted batteries in one tap with an official audit trail.
5. **Instant University PDF Dossier Export:** Generates official institutional PDF attendance tables with clean borders, zebra striping, and formal signature blocks ready for departmental archival.
6. **Academic Disciplinary Watchdog (3-Absence Threshold):** Automatically monitors cumulative missed sessions and flags students exceeding the university absence limit.
7. **Permission & Leave of Absence Workflow:** Provides structured submission and review of student medical and personal leave requests directly within Telegram.

## Project Structure
```
campus-attendance-bot/
├── main.py              # Application entrypoint, routers, FSM states, and handlers
├── database.py          # SQLite schema, WAL configuration, and data access layer
├── pdf_generator.py     # Institutional PDF generation using ReportLab
├── requirements.txt     # Locked production dependencies
├── .env.example         # Template for environment configuration
├── .gitignore           # Excludes virtual environments, secrets, and SQLite files
└── README.md            # System documentation and operational manual
```

## Installation and Deployment

### 1. Clone Repository
```bash
git clone https://github.com/adios-mars/campus-attendance-bot.git
cd campus-attendance-bot
```

### 2. Configure Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Secrets
Create a `.env` file in the root directory:
```env
BOT_TOKEN=your_telegram_bot_token_here
```

### 5. Launch Service
```bash
python main.py
```

## Security & Verification Standards
- **Role Isolation:** Strict separation between instructor controls and student check-in interfaces.
- **Concurrency Protection:** SQLite WAL mode ensures zero lock contention during simultaneous classroom check-ins.
- **Cross-Course Protection:** Validates student enrollment to prevent unauthorized cross-course attendance submissions.
