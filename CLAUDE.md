# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

NewsMonitor is an automated news digest delivery system that aggregates breaking news from 50+ RSS feeds across 7 categories and sends beautifully formatted HTML emails twice daily via GitHub Actions cron scheduling.

**Tech Stack:**
- Hosting: Vercel (serverless functions)
- Email: Gmail SMTP (free tier)
- Scheduling: GitHub Actions (separate [news-cron-job](https://github.com/MSNYC/news-cron-job) repository)
- Language: Python 3.x
- Libraries: feedparser, smtplib, email.mime, requests

## Architecture

The system has a simple flow:
1. **GitHub Actions** in a separate repository triggers the Vercel function via HTTP GET with API key authentication twice daily (8 AM & 8 PM ET)
2. **Vercel Function** (`api/send-news.py`) fetches RSS feeds, deduplicates articles, formats HTML email, and sends via Gmail SMTP
3. **Gmail SMTP** delivers the formatted email to the recipient

### Key Files

- **`api/send-news.py`**: Core serverless function that handles everything - RSS parsing, deduplication, email formatting, and SMTP delivery. This is the main file you'll work with.
- **`NewsMonitorApp.py`**: Legacy Flask implementation using NewsAPI and SendGrid (no longer actively used - current implementation uses RSS feeds and Gmail SMTP)
- **`requirements.txt`**: Python dependencies (requests, feedparser)

## Core Systems

### RSS Feed System
- Feeds are organized by category in the `RSS_FEEDS` dictionary (api/send-news.py:20-87)
- Each category contains 5-8 feed URLs from major news sources
- Top 5 articles are fetched from each feed, limited to 15 unique articles per category
- Articles older than 7 days are automatically filtered out (cutoff_date logic at api/send-news.py:193)

### Smart Deduplication System
- **Location**: Functions at api/send-news.py:92-158
- **Persistent Storage**: `/tmp/sent_articles.json` on Vercel (30-day history)
- **How it works**:
  - Tracks sent article URLs for 30 days to prevent repeats across multiple email batches
  - Uses MD5 hash of URL or title as unique identifier
  - Removes duplicates within the current batch before sending
  - Automatically cleans up entries older than 30 days
- **Stats tracking**: Counts removed duplicates and displays in email footer

### Email Formatting
- **Function**: `format_email_content()` at api/send-news.py:314-668
- **Design**: Dark-themed, mobile-responsive HTML using table-based layout for email client compatibility
- **Features**:
  - Pure black background (#000000) with high-contrast vibrant category colors
  - Quick-jump table of contents with color-coded category links
  - Article cards with left-border color coding matching categories
  - Conditional alert banner if RSS feeds fail
  - Feed health dashboard in footer with stats (success rate, article count, duplicates removed)
- **Color Scheme**: Each category has a distinct color defined in `category_colors` dict (api/send-news.py:322-330)

### Feed Health Monitoring
- Tracks feed parsing success/failure for all 50+ sources
- Builds `feed_stats` dictionary with counts and error details (api/send-news.py:183-190)
- Displays alert banner at top of email if any feeds fail
- Shows detailed stats dashboard at bottom: total articles, feed success rate, duplicates removed, failed feeds

## Development Commands

### Local Testing
```bash
# Install dependencies
pip install -r requirements.txt

# Test RSS feed parsing (requires environment variables)
python -c "from api.send_news import *; print('Imports successful')"
```

### Vercel Deployment
```bash
# Deploy to Vercel
vercel

# Deploy to production
vercel --prod
```

### Required Environment Variables
Set these in Vercel dashboard:
- `GMAIL_ADDRESS`: Gmail account for sending emails
- `GMAIL_APP_PASSWORD`: 16-character app password from Google Account settings
- `RECIPIENT_EMAIL`: Email address to receive news digests
- `MY_SECRET_API_KEY`: Random secret key for API authentication (generate with: `openssl rand -hex 32`)

## Common Modifications

### Adding/Removing RSS Feeds
Edit the `RSS_FEEDS` dictionary in `api/send-news.py`:
```python
RSS_FEEDS = {
    "New Category": [
        "https://example.com/feed.rss",
        "https://another-source.com/rss"
    ]
}
```

### Changing Category Colors
Modify `category_colors` in `format_email_content()` (api/send-news.py:322-330):
```python
category_colors = {
    "New Category": "#00ff88",  # Use high-contrast colors for dark theme
}
```

### Adjusting Article Age Filter
Change the cutoff date at api/send-news.py:193:
```python
cutoff_date = datetime.now() - timedelta(days=7)  # Default is 7 days
```

### Modifying Articles Per Category
Change the slice limits:
- Per feed: `entry in feed.entries[:5]` at api/send-news.py:206
- Per category: `unique_articles = articles[:15]` at api/send-news.py:270

## API Authentication

The Vercel endpoint requires API key authentication via `X-API-KEY` header (checked at api/send-news.py:165-172). The GitHub Actions cron job in the companion repository sends this header with each request.

## Deduplication File Location

Note that `/tmp/sent_articles.json` persists on Vercel's serverless infrastructure between invocations (within the same instance), but may reset if the function cold-starts on a new instance. This is acceptable for the 30-day deduplication window.

## Email Client Compatibility

The HTML email uses table-based layout with inline styles to ensure compatibility with:
- Apple Mail (iOS, macOS)
- Gmail (web, mobile)
- Outlook (limited dark theme support)
- Other major email clients

Dark mode is enforced using meta tags and inline bgcolor attributes (api/send-news.py:336-337, 539).
