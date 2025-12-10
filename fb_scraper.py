import time
import random
from playwright.sync_api import Page

def scroll_page(page: Page, passes: int = 5):
    """
    Scrolls the page down N times to load more content.
    """
    print(f"Scrolling {passes} times...")
    for i in range(passes):
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        # Random sleep to mimic human behavior and allow network requests to finish
        time.sleep(random.uniform(2, 4))
        print(f"  Scroll {i+1}/{passes} complete.")

def extract_post_data(article_element):
    """
    Extracts data from a single post element (div[role='article']).
    """
    try:
        # Get all text
        text = article_element.inner_text()
        
        # Try to find a link to the post
        # Facebook post links usually contain "/posts/" or are permalinks.
        # Often the timestamp is the link anchor.
        # We'll try a few strategies.
        
        link = "N/A"
        timestamp = "N/A"
        author = "Unknown"

        # Strategy 1: Look for the timestamp link (often has aria-label or just text relative time)
        # It's usually an 'a' tag that is not the profile link.
        # Common pattern: a tag inside the header part that links to the post.
        # The selector might be complex due to FB's obfuscated classes.
        # A generic approach: find all links, check href.
        
        links = article_element.locator("a").all()
        for a in links:
            href = a.get_attribute("href")
            if href and ("/posts/" in href or "/permalink/" in href):
                link = href
                # often the text of this link is the timestamp (e.g., "2h", "Yesterday")
                timestamp = a.inner_text()
                break
        
        # If link is still N/A, try finding a link that matches the pattern of a post ID
        if link == "N/A":
            for a in links:
                href = a.get_attribute("href")
                if href and "groups/" in href and "/user/" not in href:
                     # e.g. groups/123/posts/456
                     link = href
                     break

        # Clean up link (remove tracking params)
        if link != "N/A" and "?" in link:
            link = link.split("?")[0]
            
        # Strategy for Author: usually the first strong tag or h2/h3 or first link with specific structure
        # Often the first link in the article is the author or the group name.
        # Let's try to find an h2 or h3 or strong tag near the top.
        h2 = article_element.locator("h2").first
        h3 = article_element.locator("h3").first
        strong = article_element.locator("strong").first
        
        if h2.count() > 0:
            author = h2.inner_text().split('\n')[0] # simplistic extraction
        elif h3.count() > 0:
            author = h3.inner_text().split('\n')[0]
        elif strong.count() > 0:
            author = strong.inner_text()

        # Unique ID strategy: link is the best ID, fallback to hash of text
        post_id = link if link != "N/A" else str(hash(text))

        return {
            "id": post_id,
            "author": author,
            "text": text,
            "link": link,
            "timestamp": timestamp
        }

    except Exception as e:
        # print(f"Error parsing post: {e}")
        return None

def scrape_group(page: Page, group_url: str, scroll_passes: int = 3):
    """
    Navigates to a group, scrolls, and scrapes posts.
    """
    print(f"Navigating to {group_url}...")
    try:
        page.goto(group_url, timeout=60000)
        time.sleep(5) # wait for initial load

        # Basic check if loaded
        if "Facebook" not in page.title():
            print("  Warning: Page title does not suggest Facebook. Check login?")
        
        # Scroll
        scroll_page(page, passes=scroll_passes)

        # Find articles
        # Facebook feed posts usually have role="article"
        print("Parsing posts...")
        articles = page.locator("div[role='article']").all()
        print(f"  Found {len(articles)} potential posts.")

        posts_data = []
        for article in articles:
            data = extract_post_data(article)
            if data:
                posts_data.append(data)
        
        return posts_data

    except Exception as e:
        print(f"Error scraping {group_url}: {e}")
        return []

