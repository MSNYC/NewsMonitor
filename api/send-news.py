import os
import requests
from http.server import BaseHTTPRequestHandler
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import feedparser
from pathlib import Path
from datetime import datetime, timedelta
import hashlib

# Environment variables
GMAIL_ADDRESS = os.getenv('GMAIL_ADDRESS')
GMAIL_APP_PASSWORD = os.getenv('GMAIL_APP_PASSWORD')
RECIPIENT_EMAIL = os.getenv('RECIPIENT_EMAIL')
MY_SECRET_API_KEY = os.getenv('MY_SECRET_API_KEY')

# RSS Feed URLs organized by category
RSS_FEEDS = {
    "Top News": [
        "http://rss.cnn.com/rss/cnn_topstories.rss",
        "http://feeds.bbci.co.uk/news/rss.xml",
        "https://feeds.npr.org/1001/rss.xml",
        "http://feeds.reuters.com/reuters/topNews",
        "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
        "https://www.theguardian.com/world/rss",
        "https://www.aljazeera.com/xml/rss/all.xml",
        "https://feeds.washingtonpost.com/rss/national"
    ],
    "Technology": [
        "https://techcrunch.com/feed/",
        "https://www.theverge.com/rss/index.xml",
        "https://arstechnica.com/feed/",
        "https://www.wired.com/feed/rss",
        "https://www.engadget.com/rss.xml",
        "https://www.cnet.com/rss/news/",
        "https://www.zdnet.com/news/rss.xml",
        "https://www.techmeme.com/feed.xml"
    ],
    "AI": [
        "https://www.technologyreview.com/topic/artificial-intelligence/feed",
        "https://venturebeat.com/category/ai/feed/",
        "https://www.artificialintelligence-news.com/feed/",
        "https://www.marktechpost.com/feed/",
        "https://deepmind.google/blog/rss.xml",
        "https://openai.com/blog/rss/",
        "https://ai.googleblog.com/feeds/posts/default"
    ],
    "Arts and Entertainment": [
        "http://rss.cnn.com/rss/cnn_showbiz.rss",
        "https://variety.com/feed/",
        "https://www.hollywoodreporter.com/feed/",
        "http://feeds.bbci.co.uk/news/entertainment_and_arts/rss.xml",
        "https://deadline.com/feed/",
        "https://ew.com/feed/",
        "https://www.rollingstone.com/feed/"
    ],
    "Science": [
        "https://www.sciencedaily.com/rss/all.xml",
        "https://www.scientificamerican.com/feed/",
        "http://feeds.bbci.co.uk/news/science_and_environment/rss.xml",
        "https://phys.org/rss-feed/",
        "https://www.nature.com/nature.rss",
        "https://www.space.com/feeds/all",
        "https://www.newscientist.com/feed/home"
    ],
    "Health": [
        "https://www.medicalnewstoday.com/rss",
        "https://www.healthline.com/rss",
        "http://rss.cnn.com/rss/cnn_health.rss",
        "http://feeds.bbci.co.uk/news/health/rss.xml",
        "https://www.health.com/syndication/feed",
        "https://www.webmd.com/rss/rss.aspx?RSSSource=RSS_PUBLIC",
        "https://www.nih.gov/news-events/news-releases/rss"
    ],
    "Business": [
        "https://feeds.bloomberg.com/markets/news.rss",
        "http://rss.cnn.com/rss/money_latest.rss",
        "https://www.cnbc.com/id/100003114/device/rss/rss.html",
        "http://feeds.bbci.co.uk/news/business/rss.xml",
        "https://www.ft.com/?format=rss",
        "https://www.wsj.com/xml/rss/3_7085.xml",
        "https://www.marketwatch.com/rss/topstories",
        "https://www.forbes.com/business/feed/"
    ]
}

# File to store sent articles history
SENT_ARTICLES_FILE = Path("/tmp/sent_articles.json")

def load_sent_articles():
    """Load the history of sent articles from file."""
    try:
        if SENT_ARTICLES_FILE.exists():
            with open(SENT_ARTICLES_FILE, 'r') as f:
                data = json.load(f)
                # Clean up old entries (older than 30 days)
                cutoff_date = (datetime.now() - timedelta(days=30)).isoformat()
                data['articles'] = {
                    url: timestamp for url, timestamp in data.get('articles', {}).items()
                    if timestamp > cutoff_date
                }
                return data
    except Exception as e:
        print(f"Error loading sent articles: {e}")

    return {'articles': {}, 'last_updated': datetime.now().isoformat()}

def save_sent_articles(sent_articles):
    """Save the history of sent articles to file."""
    try:
        sent_articles['last_updated'] = datetime.now().isoformat()
        SENT_ARTICLES_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(SENT_ARTICLES_FILE, 'w') as f:
            json.dump(sent_articles, f, indent=2)
        print(f"Saved {len(sent_articles['articles'])} article URLs to history")
    except Exception as e:
        print(f"Error saving sent articles: {e}")

def get_article_hash(article):
    """Generate a unique hash for an article based on URL or title."""
    # Use URL as primary identifier, fallback to title
    identifier = article.get('url', '') or article.get('title', '')
    return hashlib.md5(identifier.encode()).hexdigest()

def deduplicate_articles(articles, sent_articles_history):
    """Remove duplicate articles and filter out previously sent ones."""
    seen_urls = set()
    seen_hashes = set()
    deduplicated = []

    for article in articles:
        url = article.get('url', '')
        article_hash = get_article_hash(article)

        # Skip if we've seen this URL in current batch
        if url and url in seen_urls:
            print(f"  Skipping duplicate in current batch: {article.get('title', 'No title')[:50]}")
            continue

        # Skip if we've seen this article hash in current batch
        if article_hash in seen_hashes:
            print(f"  Skipping duplicate by hash: {article.get('title', 'No title')[:50]}")
            continue

        # Skip if we've sent this article before (within last 30 days)
        if url and url in sent_articles_history.get('articles', {}):
            print(f"  Skipping previously sent: {article.get('title', 'No title')[:50]}")
            continue

        # This is a new, unique article
        if url:
            seen_urls.add(url)
        seen_hashes.add(article_hash)
        deduplicated.append(article)

    return deduplicated

class handler(BaseHTTPRequestHandler):
    """Vercel serverless function handler"""

    def do_GET(self):
        # Check API key authentication
        api_key = self.headers.get('X-API-KEY') or self.headers.get('x-api-key')

        if api_key != MY_SECRET_API_KEY:
            self.send_response(403)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Forbidden: Invalid API key"}).encode())
            return

        try:
            # Load history of sent articles
            sent_articles_history = load_sent_articles()
            new_articles_sent = []

            # Fetch news data from RSS feeds
            import time as time_module

            news_data = {}
            feed_stats = {
                'total_feeds': 0,
                'successful_feeds': 0,
                'failed_feeds': [],
                'total_articles': 0,
                'duplicates_removed': 0,
                'previously_sent': 0
            }

            # Only include articles from last 7 days
            cutoff_date = datetime.now() - timedelta(days=7)

            for category, feed_urls in RSS_FEEDS.items():
                print(f"Fetching {category}...")
                articles = []

                # Fetch from each RSS feed in the category
                for feed_url in feed_urls:
                    feed_stats['total_feeds'] += 1
                    try:
                        print(f"  Parsing feed: {feed_url}")
                        feed = feedparser.parse(feed_url)

                        for entry in feed.entries[:5]:  # Get top 5 from each feed
                            # Check article date - skip old articles
                            published = entry.get('published', entry.get('updated', ''))

                            # Parse the date
                            article_date = None
                            if published:
                                try:
                                    # Try parsing with feedparser's time
                                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                                        article_date = datetime(*entry.published_parsed[:6])
                                    elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                                        article_date = datetime(*entry.updated_parsed[:6])
                                except:
                                    pass

                            # Skip articles older than 7 days
                            if article_date and article_date < cutoff_date:
                                print(f"    Skipping old article from {article_date.strftime('%Y-%m-%d')}")
                                continue

                            # Extract article data
                            title = entry.get('title', 'No title')
                            description = entry.get('summary', entry.get('description', 'No description available.'))

                            # Clean up description (remove HTML tags if present)
                            import re
                            description = re.sub('<[^<]+?>', '', description)
                            description = description.strip()[:300]  # Limit length

                            link = entry.get('link', '')

                            # Extract source name from feed
                            source = feed.feed.get('title', 'Unknown Source')

                            articles.append({
                                "title": title,
                                "source": source,
                                "published_at": published,
                                "url": link,
                                "description": description if description else "No description available."
                            })

                        feed_stats['successful_feeds'] += 1

                    except Exception as e:
                        print(f"  Error parsing {feed_url}: {str(e)}")
                        feed_stats['failed_feeds'].append({
                            'url': feed_url,
                            'error': str(e),
                            'category': category
                        })
                        continue

                # Deduplicate articles before limiting
                original_count = len(articles)
                articles = deduplicate_articles(articles, sent_articles_history)
                duplicates_removed = original_count - len(articles)
                feed_stats['duplicates_removed'] += duplicates_removed

                if duplicates_removed > 0:
                    print(f"  Removed {duplicates_removed} duplicate/previously-sent articles")

                # Take top 15 unique articles for this category
                unique_articles = articles[:15]
                news_data[category] = unique_articles
                feed_stats['total_articles'] += len(unique_articles)

                # Track new articles for saving to history
                for article in unique_articles:
                    if article.get('url'):
                        new_articles_sent.append(article['url'])

                print(f"  Found {len(unique_articles)} unique articles for {category}")

            # Format and send email with stats
            email_content = format_email_content(news_data, feed_stats)
            send_email("Your Top News Update", email_content)

            # Save sent articles to history to prevent future duplicates
            for url in new_articles_sent:
                sent_articles_history['articles'][url] = datetime.now().isoformat()
            save_sent_articles(sent_articles_history)

            print(f"Total articles sent: {len(new_articles_sent)}")
            print(f"Total duplicates removed: {feed_stats['duplicates_removed']}")

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response_data = {
                "message": "Email sent successfully!",
                "stats": {
                    "articles_sent": len(new_articles_sent),
                    "duplicates_removed": feed_stats['duplicates_removed'],
                    "total_feeds": feed_stats['total_feeds'],
                    "successful_feeds": feed_stats['successful_feeds']
                }
            }
            self.wfile.write(json.dumps(response_data).encode())

        except Exception as e:
            print(f"Error in handler: {str(e)}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

def format_email_content(news_data, feed_stats=None):
    """Format the news data into a modern, responsive HTML email."""

    # Default stats if not provided
    if feed_stats is None:
        feed_stats = {'total_feeds': 0, 'successful_feeds': 0, 'failed_feeds': [], 'total_articles': 0}

    # Category colors - vibrant, high-contrast for dark theme
    category_colors = {
        "Top News": "#00d4ff",          # Electric blue
        "Technology": "#8b5cf6",         # Violet
        "AI": "#ff0080",                 # Hot magenta
        "Arts and Entertainment": "#f97316",  # Orange
        "Science": "#00ff88",            # Bright cyan/green
        "Health": "#a855f7",             # Purple
        "Business": "#06b6d4"            # Cyan
    }

    content = f"""
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta name="color-scheme" content="dark">
        <meta name="supported-color-schemes" content="dark">
        <style>
            :root {{
                color-scheme: dark;
            }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                line-height: 1.6;
                color: #e5e7eb;
                background-color: #000000;
                margin: 0;
                padding: 0;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background-color: #0a0a0a;
                border: 1px solid #1f1f1f;
            }}
            .header {{
                background: #000000;
                border-bottom: 2px solid #00ff88;
                color: white;
                padding: 40px 20px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 32px;
                font-weight: 900;
                letter-spacing: -1px;
                color: #ffffff;
            }}
            .header p {{
                margin: 12px 0 0 0;
                color: #9ca3af;
                font-size: 14px;
                font-weight: 500;
            }}
            .content {{
                padding: 24px;
                background: #0a0a0a;
            }}
            .category {{
                margin-bottom: 40px;
            }}
            .category-header {{
                display: flex;
                align-items: center;
                margin-bottom: 16px;
                padding-bottom: 12px;
                border-bottom: 1px solid #1f1f1f;
            }}
            .category-badge {{
                display: inline-block;
                padding: 8px 16px;
                border-radius: 4px;
                color: #000000;
                font-size: 12px;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            .article-card {{
                background: #0f0f0f;
                border: 1px solid #1a1a1a;
                border-left: 3px solid;
                border-radius: 4px;
                padding: 20px;
                margin-bottom: 14px;
            }}
            .article-title {{
                font-size: 17px;
                font-weight: 700;
                color: #ffffff;
                margin: 0 0 10px 0;
                line-height: 1.3;
            }}
            .article-meta {{
                font-size: 13px;
                color: #6b7280;
                margin-bottom: 12px;
            }}
            .source-badge {{
                display: inline-block;
                background: #1a1a1a;
                border: 1px solid #2a2a2a;
                padding: 3px 10px;
                border-radius: 3px;
                font-size: 11px;
                font-weight: 600;
                color: #9ca3af;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            .article-description {{
                font-size: 14px;
                color: #d1d5db;
                margin: 12px 0;
                line-height: 1.6;
            }}
            .read-more {{
                display: inline-block;
                background: transparent;
                border: 2px solid;
                color: inherit !important;
                text-decoration: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-size: 13px;
                font-weight: 700;
                margin-top: 10px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            .footer {{
                background: #000000;
                border-top: 1px solid #1f1f1f;
                padding: 24px;
                text-align: center;
                font-size: 11px;
                color: #6b7280;
            }}
            .no-articles {{
                color: #4b5563;
                font-style: italic;
                padding: 20px;
                text-align: center;
            }}
            .toc {{
                background: #0f0f0f;
                border: 1px solid #1f1f1f;
                border-radius: 6px;
                padding: 24px;
                margin-bottom: 32px;
            }}
            .toc-title {{
                font-size: 13px;
                font-weight: 700;
                color: #9ca3af;
                text-transform: uppercase;
                letter-spacing: 1px;
                margin: 0 0 16px 0;
            }}
            .toc-links {{
                display: flex;
                flex-wrap: wrap;
                gap: 10px;
            }}
            .toc-link {{
                display: inline-block;
                text-decoration: none;
                padding: 10px 18px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: 700;
                color: #000000;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            .alert-banner {{
                background: #1a1a1a;
                border-left: 4px solid #f97316;
                padding: 12px 16px;
                margin: 16px 24px;
                border-radius: 4px;
            }}
            .alert-banner-text {{
                color: #f97316;
                font-size: 13px;
                font-weight: 600;
                margin: 0;
            }}
            .stats-dashboard {{
                background: #0a0a0a;
                border: 1px solid #1f1f1f;
                border-radius: 4px;
                padding: 16px;
                margin: 16px 0 0 0;
                font-size: 11px;
            }}
            .stats-title {{
                color: #6b7280;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin: 0 0 8px 0;
                font-size: 10px;
            }}
            .stats-row {{
                color: #9ca3af;
                margin: 4px 0;
                font-size: 11px;
            }}
            .stats-success {{
                color: #00ff88;
            }}
            .stats-error {{
                color: #ff0080;
            }}
        </style>
    </head>
    <body bgcolor="#000000" style="background-color: #000000 !important; margin: 0; padding: 0;">
        <table width="100%" border="0" cellpadding="0" cellspacing="0" bgcolor="#000000" style="background-color: #000000 !important;">
            <tr>
                <td align="center" bgcolor="#000000" style="padding: 10px; background-color: #000000 !important;">
                    <table width="100%" style="max-width: 600px;" border="0" cellpadding="0" cellspacing="0" bgcolor="#0a0a0a" style="background-color: #0a0a0a !important; border: 1px solid #1f1f1f;">
                        <tr>
                            <td bgcolor="#000000" style="background-color: #000000; border-bottom: 2px solid #00ff88; padding: 40px 20px; text-align: center;">
                                <h1 style="color: #ffffff; margin: 0; font-size: 32px; font-weight: 900;">📰 Your Daily News Digest</h1>
                                <p style="color: #9ca3af; margin: 12px 0 0 0;">Top headlines across all major categories</p>
                            </td>
                        </tr>"""

    # Add alert banner if any feeds failed
    if feed_stats['failed_feeds']:
        failed_count = len(feed_stats['failed_feeds'])
        content += f"""
                        <tr>
                            <td bgcolor="#0a0a0a" style="background-color: #0a0a0a;">
                                <div class="alert-banner" style="background: #1a1a1a; border-left: 4px solid #f97316; padding: 12px 16px; margin: 16px 24px; border-radius: 4px;">
                                    <p class="alert-banner-text" style="color: #f97316; font-size: 13px; font-weight: 600; margin: 0;">
                                        ⚠️ {failed_count} news feed{"s" if failed_count > 1 else ""} temporarily unavailable
                                    </p>
                                </div>
                            </td>
                        </tr>"""

    content += """
                        <tr>
                            <td bgcolor="#0a0a0a" style="background-color: #0a0a0a; padding: 24px;">
                                <table width="100%" border="0" cellpadding="0" cellspacing="0" bgcolor="#0f0f0f" style="background-color: #0f0f0f; border: 1px solid #1f1f1f; border-radius: 6px; padding: 24px;">
                                    <tr>
                                        <td bgcolor="#0f0f0f" style="background-color: #0f0f0f;">
                                            <div class="toc-title" style="color: #9ca3af; font-weight: 700; text-transform: uppercase; margin-bottom: 16px;">Quick Jump to Category:</div>
                                            <div class="toc-links">
    """

    # First pass: Create table of contents
    for category in news_data.keys():
        color = category_colors.get(category, "#6b7280")
        category_id = category.replace(" ", "-").lower()
        content += f"""
                        <a href="#{category_id}" class="toc-link" style="background-color: {color};">
                            {category.title()}
                        </a>
        """

    content += """
                                            </div>
                                        </td>
                                    </tr>
                                </table>
    """

    # Second pass: Create category sections with anchor IDs
    for category, articles in news_data.items():
        color = category_colors.get(category, "#6b7280")
        category_id = category.replace(" ", "-").lower()
        content += f"""
            <div class="category" id="{category_id}" style="margin-bottom: 40px;">
                <div class="category-header" style="border-bottom: 1px solid #1f1f1f;">
                    <span class="category-badge" style="background-color: {color}; color: #000000; padding: 8px 16px; border-radius: 4px; font-weight: 700; text-transform: uppercase;">
                        {category.upper()}
                    </span>
                </div>
        """

        if articles:
            for article in articles:
                # Format the date nicely
                published_at = article.get('published_at', '')
                if published_at:
                    try:
                        from datetime import datetime
                        date_obj = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                        published_at = date_obj.strftime('%b %d, %Y at %I:%M %p')
                    except:
                        pass

                content += f"""
                <div class="article-card" style="background-color: #0f0f0f; border: 1px solid #1a1a1a; border-left: 3px solid {color}; border-radius: 4px; padding: 20px; margin-bottom: 14px;">
                    <h3 class="article-title" style="color: #ffffff; font-weight: 700; margin: 0 0 10px 0;">{article['title']}</h3>
                    <div class="article-meta" style="color: #6b7280; margin-bottom: 12px;">
                        <span class="source-badge" style="background-color: #1a1a1a; border: 1px solid #2a2a2a; padding: 3px 10px; border-radius: 3px; color: #9ca3af;">{article['source']}</span>
                        <span style="margin-left: 8px;">{published_at}</span>
                    </div>
                    <div class="article-description" style="color: #d1d5db; margin: 12px 0;">
                        {article['description']}
                    </div>
                    <a href="{article['url']}" class="read-more" style="display: inline-block; background: transparent; border: 2px solid {color}; color: {color}; text-decoration: none; padding: 10px 20px; border-radius: 4px; font-weight: 700;">READ FULL STORY</a>
                </div>
                """
        else:
            content += '<div class="no-articles">No articles found for this category.</div>'

        content += "</div>"

    # Build stats dashboard
    success_rate = (feed_stats['successful_feeds'] / feed_stats['total_feeds'] * 100) if feed_stats['total_feeds'] > 0 else 0

    content += f"""
                            </td>
                        </tr>
                        <tr>
                            <td bgcolor="#000000" style="background-color: #000000; border-top: 1px solid #1f1f1f; padding: 24px; text-align: center;">
                                <p style="color: #6b7280; margin: 0; font-size: 11px;">You're receiving this because you subscribed to daily news updates.</p>
                                <p style="color: #6b7280; margin: 10px 0 0 0; font-size: 11px;">Delivered via RSS feeds • Twice daily</p>

                                <div class="stats-dashboard" style="background: #0a0a0a; border: 1px solid #1f1f1f; border-radius: 4px; padding: 16px; margin: 16px 0 0 0;">
                                    <div class="stats-title" style="color: #6b7280; font-weight: 700; text-transform: uppercase; font-size: 10px; margin-bottom: 8px;">Feed Status</div>
                                    <div class="stats-row" style="color: #9ca3af; margin: 4px 0; font-size: 11px;">
                                        Unique Articles: <span class="stats-success" style="color: #00ff88;">{feed_stats['total_articles']}</span>
                                    </div>
                                    <div class="stats-row" style="color: #9ca3af; margin: 4px 0; font-size: 11px;">
                                        Feeds: <span class="stats-success" style="color: #00ff88;">{feed_stats['successful_feeds']}</span>/{feed_stats['total_feeds']}
                                        ({success_rate:.0f}%)
                                    </div>
                                    {f'<div class="stats-row" style="color: #9ca3af; margin: 4px 0; font-size: 11px;">Duplicates Removed: <span style="color: #8b5cf6;">{feed_stats["duplicates_removed"]}</span></div>' if feed_stats.get('duplicates_removed', 0) > 0 else ''}
                                    {f'<div class="stats-row" style="color: #9ca3af; margin: 4px 0; font-size: 11px;">Failed Feeds: <span class="stats-error" style="color: #ff0080;">{len(feed_stats["failed_feeds"])}</span></div>' if feed_stats['failed_feeds'] else ''}
                                </div>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

    return content

def send_email(subject, content):
    sender_email = GMAIL_ADDRESS
    recipient_email = RECIPIENT_EMAIL

    # Create message
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = sender_email
    message["To"] = recipient_email

    # Create plain text version to help avoid spam filters
    plain_text = """
Your Daily News Digest

View this email in a browser that supports HTML for the best experience.

To unsubscribe or manage your preferences, reply to this email.
    """

    # Add both plain text and HTML
    text_part = MIMEText(plain_text.strip(), "plain")
    html_part = MIMEText(content, "html")
    message.attach(text_part)
    message.attach(html_part)

    try:
        # Connect to Gmail SMTP server
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.sendmail(sender_email, recipient_email, message.as_string())
            print(f"Email sent successfully to {recipient_email}")
    except Exception as e:
        print(f"Error sending email: {e}")
