# Facebook Group Scraper

A local Python script using Playwright to scrape Facebook groups for posts matching specific keywords.

## Features

- **Session Management**: Logs in once and saves cookies to stay logged in.
- **Scraping**: Navigates to configured groups and scrolls to load posts.
- **Filtering**: Filters posts based on keywords (e.g., "rent", "room").
- **Deduplication**: Remembers seen posts to avoid duplicate notifications.
- **Notification**: Prints new findings to the console and saves them to `results.json`.

## Prerequisites

- Python 3.7+
- Playwright

## Setup

1.  **Install Dependencies**:
    ```bash
    pip install playwright
    playwright install chromium
    ```

2.  **Configuration**:
    Edit `config.json` to add your target Facebook Group URLs and keywords.
    ```json
    {
      "groups": [
        "https://www.facebook.com/groups/YOUR_GROUP_ID"
      ],
      "keywords": ["rent", "room", "apartment"],
      "scroll_passes": 5
    }
    ```
3. **OpenAI**
   Create .env file in the main folder and add OPENAI_API_KEY=XXXXXXXXXXXXXX

## Usage

1.  **Run the script**:
    ```bash
    python main.py
    ```

2.  **First Run (Login)**:
    - If no session is saved, the script will open a browser window and prompt you to log in to Facebook.
    - Log in manually.
    - Return to the terminal and press **Enter** when you are ready.
    - The session (cookies) will be saved to `storage/session.json`.

3.  **Subsequent Runs**:
    - The script will load the saved session and start scraping immediately.
    - It will output new matching posts to the console and `results.json`.

## Files

- `main.py`: Entry point. Orchestrates loading config, session, scraping, and notifying.
- `fb_scraper.py`: Logic for navigating FB and extracting post data.
- `notifier.py`: Handles outputting results.
- `config.json`: Configuration settings.
- `storage/`: Stores session cookies and history of seen posts.

