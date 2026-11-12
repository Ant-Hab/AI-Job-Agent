import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def evaluate_job(job_title, job_description):
    system_prompt = """You are a strict technical recruiter evaluating job listings for a software engineer.
    The candidate has a background in Industrial Engineering and specializes in:
    - C, C++, Python, TypeScript, React, Go
    - Low-level system architecture, Docker, Nginx, Linux Unix system calls
    - PostgreSQL and SAP ERP systems
    
    Analyze the job and return ONLY a valid JSON object with the following structure:
    {
        "score": <integer from 0 to 100 based on stack match>,
        "reasoning": "<1 short sentence explaining the score>",
        "missing_skills": ["<skill_1>", "<skill_2>"]
    }
    Do not output any markdown formatting, conversational text, or backticks. Only the raw JSON object.
    """
    
    user_prompt = f"Job Title: {job_title}\n\nJob Description:\n{job_description}"

    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model="qwen/qwen3.8-27b",
            temperature=0.1,
            max_tokens=200,
        )
        
        # Get the response and clean potential markdown backticks
        content = response.choices[0].message.content.strip()
        if content.startswith("```"):
            content = content.replace("```json", "").replace("```", "").strip()
            
        return json.loads(content)
    except Exception as e:
        print(f"Error during AI evaluation: {e}")
        return {"score": 0, "reasoning": "Evaluation failed.", "missing_skills": []}
