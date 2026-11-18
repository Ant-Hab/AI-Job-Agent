from scraper import fetch_linkedin_jobs
from agent import evaluate_job
from document_builder import generate_application_docs
from notifier import send_telegram_alert

def process_jobs():
    keywords = ["Software Engineer", "Supply Chain", "Systems Integration"]
    
    for keyword in keywords:
        jobs = fetch_linkedin_jobs(keyword, "Finland")
        
        for job in jobs:
            title = job['title']
            link = job['link']
            desc = job['description']
            
            print(f"\nEvaluating: {title}...")
            evaluation = evaluate_job(title, desc)
            score = evaluation.get("score", 0)
            category = evaluation.get("category", "IT")
            
            print(f"Category: {category} | Match Score: {score}/100")
            
            if score >= 40:
                if score >= 75:
                    color = "🟩"
                elif score >= 51:
                    color = "🟦"
                else:
                    color = "🟨"
                    
                print("🔥 Match found! Generating documents...")
                cv_tex, cl_tex, is_success = generate_application_docs(title, desc, category)
                
                if is_success:
                    file_status = "✅ AI Tailored Success! `.tex` files attached below 👇"
                elif cv_tex is not None and cl_tex is not None:
                    file_status = "⚠️ API Quota Exceeded. Base `.tex` files attached below 👇"
                else:
                    file_status = "❌ System Error. Apply manually."
                
                message = (
                    f"{color} *Match Score: {score}/100*\n\n"
                    f"*{title}*\n"
                    f"**Category:** {category}\n"
                    f"**Why:** {evaluation.get('reasoning')}\n"
                    f"**Missing:** {', '.join(evaluation.get('missing_skills', ['None']))}\n\n"
                    f"📄 *Files:* {file_status}\n\n"
                    f"[Apply Here (LinkedIn)]({link})"
                )
                
                # Bundle the generated .tex files and send to Telegram
                files_to_send = [f for f in [cv_tex, cl_tex] if f is not None]
                send_telegram_alert(message, files=files_to_send)
                
            else:
                print("Score too low. Skipping document generation and alert.")

if __name__ == "__main__":
    process_jobs()
