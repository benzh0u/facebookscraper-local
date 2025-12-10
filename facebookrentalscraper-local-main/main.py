import json
import os
import time
from playwright.sync_api import sync_playwright
from openai import OpenAI
from dotenv import load_dotenv

import fb_scraper
import notifier

# Load environment variables
load_dotenv()

CONFIG_FILE = "config.json"
STORAGE_DIR = "storage"
SESSION_FILE = os.path.join(STORAGE_DIR, "session.json")
SEEN_POSTS_FILE = os.path.join(STORAGE_DIR, "seen_posts.json")

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def load_config():
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def load_seen_posts():
    if os.path.exists(SEEN_POSTS_FILE):
        try:
            with open(SEEN_POSTS_FILE, 'r') as f:
                return set(json.load(f))
        except:
            return set()
    return set()

def save_seen_posts(seen_ids):
    with open(SEEN_POSTS_FILE, 'w') as f:
        json.dump(list(seen_ids), f)

def ensure_storage_dir():
    if not os.path.exists(STORAGE_DIR):
        os.makedirs(STORAGE_DIR)

def login_and_save_session(context):
    """
     pauses execution to allow user to log in manually, then saves the session.
    """
    page = context.new_page()
    page.goto("https://www.facebook.com/")
    
    print("\n" + "="*60)
    print("SESSION FILE NOT FOUND OR INVALID")
    print("Please log in to Facebook in the opened browser window.")
    print("Once you are logged in and can see your feed, press Enter here.")
    print("="*60 + "\n")
    
    input("Press Enter after you have logged in...")
    
    # Save storage state
    context.storage_state(path=SESSION_FILE)
    print(f"Session saved to {SESSION_FILE}")
    page.close()

def check_if_looking_for_room(post_text):
    """
    Uses GPT-4o-mini to determine if the post author is looking for a room.
    Returns True if YES, False otherwise.
    """
    if not post_text or len(post_text) < 10:
        return False

    prompt = f"""
    Determine if this Facebook post is from someone looking for a room or place to rent.
    
    Post:
    "{post_text}"
    
    Output only: YES or NO.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that classifies social media posts."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )
        answer = response.choices[0].message.content.strip().upper()
        return "YES" in answer
    except Exception as e:
        print(f"  [!] OpenAI API Error: {e}")
        # Fail safe: if API fails, maybe return True to not miss it? 
        # Or False to avoid noise? Let's return False for now to avoid spam.
        return False

def main():
    ensure_storage_dir()
    config = load_config()
    seen_ids = load_seen_posts()
    
    keywords = [k.lower() for k in config.get("keywords", [])]
    groups = config.get("groups", [])
    scroll_passes = config.get("scroll_passes", 3)

    if not groups:
        print("No groups configured in config.json")
        return

    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("Warning: OPENAI_API_KEY not found in environment variables.")
        print("AI filtering will likely fail.")

    with sync_playwright() as p:
        # Launch browser (headless=False so user can see what's happening or login)
        browser = p.chromium.launch(headless=False)
        
        # Check if session exists
        if os.path.exists(SESSION_FILE):
            print(f"Loading session from {SESSION_FILE}")
            context = browser.new_context(storage_state=SESSION_FILE)
        else:
            print("No saved session found.")
            context = browser.new_context()
            login_and_save_session(context)
            # Re-create context with saved state to be sure
            context.close()
            context = browser.new_context(storage_state=SESSION_FILE)

        page = context.new_page()

        all_new_posts = []

        for group_url in groups:
            print(f"\nScraping group: {group_url}")
            raw_posts = fb_scraper.scrape_group(page, group_url, scroll_passes)
            
            # Filter and deduplicate
            for post in raw_posts:
                post_id = post['id']
                post_text = post['text'] # Keep original case for AI
                
                # Deduplication check
                if post_id in seen_ids:
                    continue
                
                # Keyword check (Pre-filter to save API costs)
                lower_text = post_text.lower()
                keyword_match = False
                if not keywords:
                    keyword_match = True
                else:
                    for kw in keywords:
                        if kw in lower_text:
                            keyword_match = True
                            break
                
                if not keyword_match:
                    continue

                # AI Check
                print(f"  > Checking post {str(post_id)[:10]}... with AI...")
                is_relevant = check_if_looking_for_room(post_text)
                
                if is_relevant:
                    print(f"    [+] AI confirmed match!")
                    all_new_posts.append(post)
                    seen_ids.add(post_id)
                else:
                    print(f"    [-] AI rejected (not looking for room).")

        # Notify
        if all_new_posts:
            notifier.notify_new_posts(all_new_posts)
            save_seen_posts(seen_ids)
        else:
            print("\nNo new matching posts found.")

        context.close()
        browser.close()

if __name__ == "__main__":
    main()
