import json
import os
from datetime import datetime

RESULTS_FILE = "results.json"

def notify_new_posts(posts):
    """
    Prints notification to console and saves to results.json.
    """
    if not posts:
        return

    print(f"\n[!] Found {len(posts)} new relevant posts:")
    
    # Load existing results if any
    existing_results = []
    if os.path.exists(RESULTS_FILE):
        try:
            with open(RESULTS_FILE, 'r', encoding='utf-8') as f:
                existing_results = json.load(f)
        except json.JSONDecodeError:
            pass

    for post in posts:
        print("-" * 50)
        print(f"Author: {post.get('author', 'Unknown')}")
        print(f"Time: {post.get('timestamp', 'Unknown')}")
        print(f"Link: {post.get('link', 'No link')}")
        print(f"Text snippet: {post.get('text', '')[:100]}...")
        
        # Add timestamp of discovery
        post['_discovered_at'] = datetime.now().isoformat()
        existing_results.append(post)

    # Save back to results.json
    with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(existing_results, f, indent=2, ensure_ascii=False)
    
    print("-" * 50)
    print(f"Saved {len(posts)} new posts to {RESULTS_FILE}")

