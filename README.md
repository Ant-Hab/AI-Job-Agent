# Agentic AI Job Filter & Alert System

An automated, LLM-powered job filtering pipeline that ingests job descriptions, evaluates them using semantic matching against a specific technical profile, and pushes high-quality matches to a Telegram bot.

## Architecture & Workflow
1. **Agentic Evaluation**: Passes job descriptions to **Qwen 3.8 27B (via Groq API)**. The LLM acts as a strict technical recruiter, scoring the role based on requirements (e.g., C++, React, TypeScript, Docker, PostgreSQL, low-level systems).
2. **Notification**: Filters out noise and pushes roles with a >80% match score directly to a Telegram chat via webhooks.

## Tech Stack
* **Language**: Python 3
* **AI/LLM**: Groq API
* **Integrations**: Telegram Bot API

## Setup
1. Clone repo and `pip install -r requirements.txt`
2. Add your `GROQ_API_KEY`, `TELEGRAM_BOT_TOKEN`, and `TELEGRAM_CHAT_ID` to a `.env` file.
3. Run `python3 main.py`
