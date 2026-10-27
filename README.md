# Campus Attendance Bot — Dire Dawa University (DDU)

An asynchronous Telegram-based attendance management system built for Dire Dawa University (DDU). Built with Python and Aiogram 3, utilizing SQLite configured with Write-Ahead Logging (WAL) to handle high-concurrency batch check-ins without write contention.

## System Architecture

- **Interface:** Telegram Bot API (accessible across Mobile, Desktop, and Web clients).
- **Runtime & Framework:** Python 3.11+, `aiogram` 3.x, `asyncio`.
- **Database:** SQLite with Write-Ahead Logging (`PRAGMA journal_mode=WAL`) for non-blocking concurrent writes.
- **Reporting Engine:** Vector-based PDF generation via ReportLab.

## Core Features

- **Multi-Course Management:** Configure and manage separate course sections across departments, batches, and semesters from a single instructor interface.
- **Deep-Link Onboarding:** Instructors generate course-specific Telegram deep-links for Class Representatives (CR) to distribute, allowing friction-free student self-enrollment.
- **Ephemeral PIN Check-In:** Generates a randomized 4-digit token with a 60-second TTL to eliminate remote proxy sign-ins from outside the lecture hall.
- **Manual Override Fallback:** Live missing-student roster allows instructors to verify and mark present any students with dead batteries or missing devices with one tap.
- **Absence Threshold Alerts:** Tracks attendance history automatically and flags students reaching the 3-absence limit prior to exam qualification cutoffs.
- **In-Chat Excuse Workflow:** Students can submit medical notes or leave requests directly through the bot for instructor review and approval.
- **Departmental PDF Export:** Generates print-ready attendance dossiers formatted with alternating row stripes and signature blocks for departmental archiving.

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
