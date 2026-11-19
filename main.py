import os
import json
import time
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from groq import Groq
from google import genai

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

SEEN_FILE = "seen_jobs.json"

groq_client = Groq(api_key=GROQ_API_KEY)
gemini_client = genai.Client(api_key=GEMINI_API_KEY)

CANDIDATE_PROFILE = """
Name: Antor Chowdhury (Helsinki, Finland)
Education: M.Sc. in Industrial Engineering and Management (University of Oulu), Software Engineering Student at Hive Helsinki (Ecole 42 network, Rank 4 - C/C++, Unix systems, Python, TypeScript, React, PostgreSQL, Docker).
Experience: Systems Integration Consultant & Team Lead (Python data pipelines, stakeholder management), Sourcing & Logistics Manager.
Target Roles: Software Engineer, Systems Engineer, Missions/Operations Engineer, Technical Internships in Finland.
"""

SEARCH_QUERIES = [
    ("Software Engineer", "Helsinki"),
    ("Systems Engineer", "Espoo"),
    ("Intern", "Espoo"),
]


def load_seen_jobs():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()


def save_seen_jobs(seen_set):
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(list(seen_set)), f, indent=2)


def canonical_job_id(url):
    return url.split("?")[0].strip().rstrip("/")


def scrape_linkedin_jobs(keywords, location):
    url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
    params = {
        "keywords": keywords,
        "location": location,
        "f_TPR": "r86400",  # Last 24 hours
        "start": 0,
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }

    try:
        resp = requests.get(url, params=params, headers=headers, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"[Scrape Error] {keywords} in {location}: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    jobs = []

    for card in soup.find_all("li"):
        title_el = card.find("h3", class_="base-search-card__title")
        company_el = card.find("h4", class_="base-search-card__subtitle")
        link_el = card.find("a", class_="base-card__full-link")

        if title_el and company_el and link_el and link_el.get("href"):
            jobs.append({
                "title": title_el.get_text(strip=True),
                "company": company_el.get_text(strip=True),
                "url": canonical_job_id(link_el["href"]),
            })

    return jobs


def fetch_job_description(job_url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
    try:
        resp = requests.get(job_url, headers=headers, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        desc_el = soup.find("div", class_="show-more-less-html__markup")
        return desc_el.get_text("\n", strip=True) if desc_el else ""
    except Exception as e:
        print(f"[Description Fetch Error] {job_url}: {e}")
        return ""


def evaluate_fit_with_groq(job, description):
    prompt = f"""
Evaluate if this job is a strong fit for the candidate.
Respond ONLY with valid JSON: {{"match": true/false, "score": 0-100, "reason": "1 short sentence"}}

Candidate:
{CANDIDATE_PROFILE}

Job:
Title: {job['title']}
Company: {job['company']}
Description:
{description[:3000]}
"""
    try:
        chat = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        return json.loads(chat.choices[0].message.content)
    except Exception as e:
        print(f"[Groq Error] {job['title']}: {e}")
        return {"match": False, "score": 0, "reason": "Evaluation failed"}


def generate_tailored_summary(job, description):
    prompt = f"""
Write a 3-bullet tailored pitch and a 3-line LaTeX Professional Summary tailored for this specific role based on the candidate profile. Keep it concise.

Candidate:
{CANDIDATE_PROFILE}

Role: {job['title']} at {job['company']}
Description:
{description[:3000]}
"""
    try:
        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        return response.text.strip()
    except Exception as e:
        print(f"[Gemini Error] {job['title']}: {e}")
        return "Tailored summary unavailable."


def send_telegram_message(text):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[Telegram Warning] Missing token or chat ID.")
        return False

    api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text[:4000],
        "disable_web_page_preview": True,
    }
    try:
        resp = requests.post(api_url, json=payload, timeout=15)
        resp.raise_for_status()
        return True
    except Exception as e:
        print(f"[Telegram Error] {e}")
        return False


def main():
    seen_jobs = load_seen_jobs()
    new_alerts_sent = 0
    total_scraped = 0

    for keywords, location in SEARCH_QUERIES:
        jobs = scrape_linkedin_jobs(keywords, location)
        total_scraped += len(jobs)

        for job in jobs:
            job_id = job["url"]
            if job_id in seen_jobs:
                continue

            description = fetch_job_description(job_id)
            if not description:
                continue

            evaluation = evaluate_fit_with_groq(job, description)
            score = evaluation.get("score", 0)

            if evaluation.get("match") and score >= 75:
                tailored = generate_tailored_summary(job, description)
                msg = (
                    f"🚀 New Match ({score}/100)\n"
                    f"Role: {job['title']}\n"
                    f"Company: {job['company']}\n"
                    f"Why: {evaluation.get('reason')}\n"
                    f"Link: {job_id}\n\n"
                    f"{tailored}"
                )
                if send_telegram_message(msg):
                    seen_jobs.add(job_id)
                    new_alerts_sent += 1
            else:
                seen_jobs.add(job_id)

            time.sleep(1.5)

    save_seen_jobs(seen_jobs)

    if new_alerts_sent == 0:
        send_telegram_message(
            f"✅ Daily AI Job Agent ran: checked {total_scraped} listings, 0 new matches today."
        )

    print(f"Finished. New alerts sent: {new_alerts_sent} | Total tracked: {len(seen_jobs)}")


if __name__ == "__main__":
    main()
