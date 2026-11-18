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
                    color = "🍏"
                else:
                    color = "🟨"
                    
                print("🔥 Match found! Generating documents...")
                cv_tex, cl_tex = generate_application_docs(title, desc, category)
                
                if cl_tex is not None:
                    file_status = f"✅ AI Tailored Success!\nLaTeX: `{cv_tex}`, `{cl_tex}`\n(Compile to PDF in Overleaf or terminal)"
                elif cv_tex is not None:
                    file_status = f"⚠️ API Quota Exceeded.\nFallback Base CV Ready: `{cv_tex}`"
                else:
                    file_status = "❌ API Overloaded. Links below to apply manually."
                
                message = (
                    f"{color} *Match Score: {score}/100*\n\n"
                    f"*{title}*\n"
                    f"**Category:** {category}\n"
                    f"**Why:** {evaluation.get('reasoning')}\n"
                    f"**Missing:** {', '.join(evaluation.get('missing_skills', ['None']))}\n\n"
                    f"📄 *Files:* \n{file_status}\n\n"
                    f"[Apply Here (LinkedIn)]({link})"
                )
                send_telegram_alert(message)
            else:
                print("Score too low. Skipping document generation and alert.")

if __name__ == "__main__":
    process_jobs()
