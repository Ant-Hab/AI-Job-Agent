import os
import shutil
import concurrent.futures
from google import genai
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def generate_application_docs(job_title, job_description, category):
    file_map = {
        "IT": "cv_it.tex",
        "Supply Chain": "cv_sc.tex",
        "Mixed": "cv_mixed.tex"
    }
    base_file = file_map.get(category, "cv_it.tex")
    
    try:
        with open(base_file, "r") as f:
            base_cv = f.read()
        with open("base_cl.tex", "r") as f:
            base_cl = f.read()
    except FileNotFoundError as e:
        print(f"Error loading base templates: {e}")
        return None, None, False
    
    output_dir = "applications"
    os.makedirs(output_dir, exist_ok=True)
    
    prompt = f"""
    You are an expert career consultant and LaTeX formatting engine. 
    I am applying for: {job_title}.
    
    Job Description:
    {job_description}
    
    Here is my base LaTeX CV:
    {base_cv}
    
    TASK 1: TAILOR THE CV (Output as raw LaTeX)
    Apply these strict rules to the CV:
    1. Strictly One Page: Manage section lengths, bullet points, and spacing in LaTeX to guarantee it never spills over.
    2. AI Skill Trigger: If the job requires AI skills, include my personal project: "Building an automated job search, filtering, and alert system using AI agents."
    3. Logistics/Coordination Trigger: If the role involves supply chain, logistics, or cross-functional coordination, include my experience as Sourcing & Logistics Manager at Walton Group (2017–2019).
    4. 42 Projects: Prioritize my Hive Helsinki (École 42) projects.
    5. No Bilingual: DO NOT include "Bilingual (Finnish/English)" in the Skills section.
    
    TASK 2: WRITE A TAILORED COVER LETTER (Output as raw LaTeX)
    Here is my base LaTeX Cover Letter template to use for formatting:
    {base_cl}
    
    Apply these strict rules to the Cover Letter:
    1. Length: Keep it concise. It should be slightly shorter than standard cover letters.
    2. 4-Section Structure:
       - Opening: State which role I am applying for.
       - Interest: Why I am interested in the position and the company.
       - Fit & Value: Why I fit the position/company and what value I add.
         -> MUST explicitly weave in these soft skills: "quick learner", "eager to learn new things", "ownership", "independent work", "proactive", "collaboration", "customer focus".
         -> MANDATORY ENDING FOR THIS SECTION: "Additionally, as a Finnish citizen, I possess unrestricted work authorization and do not require visa sponsorship."
       - Closing: Professional closing and call to action.

    Output your response exactly in this format:
    ===START_CV===
    [Tailored LaTeX CV Code Here]
    ===END_CV===
    ===START_COVER_LETTER===
    [LaTeX Cover Letter Code Here]
    ===END_COVER_LETTER===
    """
    
    print(f"Drafting tailored LaTeX CV ({base_file}) and Cover Letter via Gemini...")
    safe_title = job_title.replace(' ', '_').replace('/', '_')
    cv_filename = os.path.join(output_dir, f"Tailored_CV_{safe_title}.tex")
    cl_filename = os.path.join(output_dir, f"Tailored_CL_{safe_title}.tex")
    
    is_success = False
    
    try:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(
                client.models.generate_content,
                model='gemini-3.5-flash', 
                contents=prompt
            )
            response = future.result(timeout=30)
            
        text = response.text
        
        if "===START_CV===" not in text or "===START_COVER_LETTER===" not in text:
            raise ValueError("AI did not return the expected format.")
            
        cv_part = text.split("===START_CV===")[1].split("===END_CV===")[0].strip()
        cl_part = text.split("===START_COVER_LETTER===")[1].split("===END_COVER_LETTER===")[0].strip()
        
        with open(cv_filename, "w") as f: f.write(cv_part)
        with open(cl_filename, "w") as f: f.write(cl_part)
        is_success = True
        
    except (concurrent.futures.TimeoutError, Exception) as e:
        print(f"Gemini API failed/timed out. Providing dual fallback files. Error: {e}")
        shutil.copy2(base_file, cv_filename)
        shutil.copy2("base_cl.tex", cl_filename)
        is_success = False

    return cv_filename, cl_filename, is_success
