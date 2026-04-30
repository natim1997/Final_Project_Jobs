import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import os
import firebase_admin
from firebase_admin import credentials, db
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

# ==========================================
# 1. Initialize Firebase & Geocoder
# ==========================================
# Make sure your serviceAccountKey.json is in the same folder!
try:
    cred = credentials.Certificate(r"C:\Users\netan\JobMatcher_Project\Node_Backend\src\config\serviceAccountKey.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://jobmatcherproject-default-rtdb.firebaseio.com/'
    })
    print("✅ Firebase initialized successfully")
except Exception as e:
    print(f"❌ Firebase init failed: {e}")

geolocator = Nominatim(user_agent="job_matcher_crawler")

# List of common skills to extract from description
SKILL_KEYWORDS = ["python", "java", "sql", "excel", "english", "service", "office", "שירות", "מכירות", "אנגלית"]

def get_lat_lng(city_name):
    """ Converts city name to coordinates with a simple cache/delay to avoid blocking """
    try:
        location = geolocator.geocode(city_name + ", Israel", timeout=10)
        if location:
            return location.latitude, location.longitude
    except:
        pass
    return 32.0853, 34.7818 # Default to Tel Aviv if search fails

def extract_keywords(description):
    """ Simple keyword extractor from Hebrew/English text """
    found = []
    desc_lower = description.lower()
    for kw in SKILL_KEYWORDS:
        if kw in desc_lower:
            found.append(kw.capitalize())
    return list(set(found))

# ==========================================
# 2. Scraper Logic
# ==========================================

def scrape_single_page(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
    except:
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    processed_jobs = []
    job_cards = soup.find_all('div', class_='open-board') 
    
    for card in job_cards:
        try:
            # Basic Extraction
            title = card.find('h2').text.strip() if card.find('h2') else "Unknown"
            company = card.find('div', class_='T14').text.strip() if card.find('div', class_='T14') else "Secret"
            desc = card.find('div', class_='job-content-top-desc').text.strip() if card.find('div', class_='job-content-top-desc') else ""
            job_id = card.find('div', class_='jobid-hidden').text.strip() if card.find('div', class_='jobid-hidden') else str(random.randint(1000, 9999))
            
            city = "Tel Aviv"
            location_box = card.find('div', class_='job-regions-box')
            if location_box:
                city = location_box.find('a').text.strip()

            # --- THE "GOLD STANDARD" TRANSFORMATION ---
            lat, lng = get_lat_lng(city)
            keywords = extract_keywords(desc)
            
            firebase_job = {
                "basic_info": {
                    "job_title": title,
                    "company_name": company,
                    "location_city": city
                },
                "location": {
                    "lat": lat,
                    "lng": lng
                },
                "availability": {
                    "is_flexible": True, # Most AllJobs listings are flexible shifts
                    "monday": [{"start": "08:00", "end": "17:00"}] # Default placeholder
                },
                "requirements": {
                    "min_experience_years": 0,
                    "keywords": keywords
                },
                "characteristics": {
                    "suitable_for_students": "סטודנט" in desc or "סטודנט" in title,
                    "work_alone": False
                },
                "text_fields": {
                    "description": desc
                }
            }
            processed_jobs.append((job_id, firebase_job))
            
        except Exception as e:
            print(f"Error processing card: {e}")
            
    return processed_jobs

def upload_to_firebase(job_list):
    """ Uploads processed jobs directly to Firebase Realtime Database """
    if not job_list: return
    
    jobs_ref = db.reference('jobs')
    for job_id, job_data in job_list:
        try:
            # Using update instead of push to maintain our own Job_ID
            jobs_ref.child(f"job_{job_id}").update(job_data)
        except Exception as e:
            print(f"Failed to upload job {job_id}: {e}")

# ==========================================
# 3. Main Execution
# ==========================================

def run_sync(total_pages=5):
    base_url = "https://www.alljobs.co.il/SearchResultsGuest.aspx?page={}"
    
    for page in range(1, total_pages + 1):
        print(f"🚀 Scraping & Uploading Page {page}...")
        jobs = scrape_single_page(base_url.format(page))
        upload_to_firebase(jobs)
        print(f"✅ Finished Page {page}. Found {len(jobs)} jobs.")
        time.sleep(random.uniform(2, 4))

if __name__ == "__main__":
    # Start with a small number to test (e.g., 2 pages)
    run_sync(total_pages=2)