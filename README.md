# AI HR Recruiter Bot

[![Ru](https://img.shields.io/badge/lang-ru-green.svg)](README_ru.md)
![Coverage](./coverage.svg)
![Python](https://img.shields.io/badge/python-3.12-blue.svg)
![Aiogram](https://img.shields.io/badge/Aiogram-3.x-2ca5e0.svg)
![Gemini](https://img.shields.io/badge/AI-Gemini_2.5-purple.svg)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ed.svg)

This project demonstrates how to build a **proactive AI Recruiter** that actually reads resumes, understands context, and filters candidates before they reach a human.

It moves beyond linear `if/else` logic, using **Google Gemini 2.5** to conduct natural conversations and analyze technical backgrounds.

---

## Key Features

* **It Reads PDFs:** The bot extracts text from PDF resumes, analyzes the candidate's tech stack against vacancy requirements, and gives instant, relevant feedback.
* **It Browses Links:** Candidate sent a link to their portfolio or LinkedIn? No problem. The bot parses external content using `httpx` + `BeautifulSoup`.
* **It Remembers Context:** Thanks to **Redis**, the bot doesn't forget who you are or what file you sent 5 minutes ago.
* **It's Professional:** The system prompt is engineered to act as a gatekeeper. It politely deflects salary/benefit questions ("Let's discuss this at the interview") and focuses on technical fit.
* **It's Clean:** Fully typed Python 3.12, modular architecture, and packaged with Docker & Poetry.

## Tech Stack

* **Core:** Python 3.12, Aiogram 3 (Asyncio)
* **AI Engine:** Google Gemini 2.5 (via `google-generativeai`)
* **Infrastructure:** Docker, Docker Compose
* **Storage:** Redis (FSM state & caching)
* **Tools:** Poetry, Pydantic, Makefile, Pytest

---

## Quick Start

Everything is automated via `Makefile`.

### Prerequisites
1. Docker & Docker Compose.
2. Telegram Bot Token (@BotFather).
3. Google Gemini API Key (Google AI Studio).

### 1. Configure
Create a `.env` file in the root directory (copy from `.env.example`):

```ini
BOT_TOKEN=your_telegram_bot_token
GOOGLE_API_KEY=your_gemini_api_key
REDIS_HOST=redis
REDIS_PORT=6379
```

### 2. Run (Docker) — Recommended

One command to rule them all:

```bash
make docker-up
```

 * **View logs:** make docker-logs
 * **Stop:** make docker-down

### 3. Run (Local)

If you want to run it without Docker (requires local Redis):

```bash
make install
make run
```

## Quality Control

```bash
# Run Unit & Integration tests
make test

# Check code style (Black + Flake8)
make check
```

## Structure

```plaintext
.
├── app
│   ├── bot          # Telegram handlers & UI
│   ├── services     # Logic: AI, Parser,
│   ├── config.py    # Strict config validation
│   └── main.py      # Entry point 
├── tests            # Comprehensive testing
├── Dockerfile       # Optimized for Poetry
└── Makefile         # Shortcuts
```