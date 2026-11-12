from agent import evaluate_job
from notifier import send_telegram_alert

def process_new_job(job_title, job_description, apply_link):
    print(f"Evaluating: {job_title}...")
    
    evaluation = evaluate_job(job_title, job_description)
    score = evaluation.get("score", 0)
    
    print(f"Match Score: {score}/100")
    print(f"Reasoning: {evaluation.get('reasoning')}")
    
    if score >= 80:
        message = (
            f"🎯 *High Match Job Alert: {score}/100*\n\n"
            f"*{job_title}*\n"
            f"**Why:** {evaluation.get('reasoning')}\n"
            f"**Missing:** {', '.join(evaluation.get('missing_skills', ['None']))}\n\n"
            f"[Apply Here]({apply_link})"
        )
        send_telegram_alert(message)
    else:
        print("Score too low. Skipping Telegram alert.")

if __name__ == "__main__":
    # Test Data
    test_title = "Junior Full-Stack Engineer (C++ / React)"
    test_description = """
    We are looking for a backend-heavy full-stack developer to join our infrastructure team in Helsinki.
    You will be optimizing low-level system processes and building out our user-facing dashboards.
    Requirements:
    - Strong experience with C/C++ and memory management
    - Proficiency in React and TypeScript
    - Experience containerizing apps with Docker
    - Familiarity with Kubernetes is a plus, but not required.
    """
    test_link = "https://linkedin.com/jobs/view/123456"
    
    process_new_job(test_title, test_description, test_link)
