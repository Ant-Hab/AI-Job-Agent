import requests
from bs4 import BeautifulSoup
import time

def fetch_linkedin_jobs(keyword, location):
    print(f"Scraping LinkedIn Guest API for '{keyword}' in {location}...")
    
    url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={keyword}&location={location}&start=0"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    response = requests.get(url, headers=headers)
    jobs = []
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        job_cards = soup.find_all('li')
        
        for card in job_cards[:3]: 
            title_elem = card.find('h3', class_='base-search-card__title')
            link_elem = card.find('a', class_='base-card__full-link')
            
            if title_elem and link_elem:
                job_url = link_elem['href'].split('?')[0]
                
                res_desc = requests.get(job_url, headers=headers)
                desc_text = ""
                if res_desc.status_code == 200:
                    desc_soup = BeautifulSoup(res_desc.text, 'html.parser')
                    desc_div = desc_soup.find('div', class_='description__text')
                    if desc_div:
                        desc_text = desc_div.text.strip()
                
                if desc_text:
                    jobs.append({
                        "title": title_elem.text.strip(),
                        "link": job_url,
                        "description": desc_text
                    })
                time.sleep(2)
    return jobs

if __name__ == "__main__":
    jobs = fetch_linkedin_jobs("Software Engineer", "Finland")
    for j in jobs:
        print(f"Found: {j['title']}")
