import json
from pathlib import Path

from core.user_data import db

jobs = {}
available_jobs = {}

#=======================
BASE_DIR = Path(__file__).resolve().parent
JOBS_FILE = BASE_DIR/"jobs.json"

def load_jobs():
    try:
        with open(JOBS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print("[!] File not found. Creating:", JOBS_FILE)
        with open(JOBS_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=4)
            return {}
    
def save_jobs(data):
    with open(JOBS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
#=======================

def get_user_job(user_id: int):
    user_job = db.get_user_data("job", user_id)
    if not user_job: return None
    return json.loads(user_job)

def set_user_job(user_id: int, data: dict):
    db.post_user_data("job", user_id, data)

def get_user_courses(user_id: int):
    user_courses = json.loads(db.get_user_data("courses", user_id))
    if not user_courses: return []
    return user_courses

def set_user_courses(user_id: int, courses: list):
    db.post_user_data("courses", user_id, courses)

def add_user_courses(user_id: int, item_name: str):
    user_courses = get_user_courses(user_id)

    if item_name in user_courses: return False

    user_courses.append(item_name)

    set_user_courses(user_id, user_courses)
    return True