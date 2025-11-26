import os
import requests
from http.server import BaseHTTPRequestHandler
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Environment variables
NEWS_API_KEY = os.getenv('NEWS_API_KEY')
GMAIL_ADDRESS = os.getenv('GMAIL_ADDRESS')
GMAIL_APP_PASSWORD = os.getenv('GMAIL_APP_PASSWORD')
RECIPIENT_EMAIL = os.getenv('RECIPIENT_EMAIL')
MY_SECRET_API_KEY = os.getenv('MY_SECRET_API_KEY')

# NewsAPI categories
CATEGORIES = {
    "business news": "business",
    "entertainment news": "entertainment",
    "general news": "general",
    "health news": "health",
    "science news": "science",
    "sports news": "sports",
    "technology news": "technology"
}

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
            # Fetch news data
            news_data = {}

            for label, category in CATEGORIES.items():
                url = (f"https://newsapi.org/v2/top-headlines?"
                       f"category={category}&"
                       f"country=us&"
                       f"pageSize=15&"
                       f"apiKey={NEWS_API_KEY}")

                response = requests.get(url)
                print(f"Request URL: {url}")
                print(f"Response Status Code: {response.status_code}")

                if response.status_code == 200:
                    data = response.json()
                    articles = data.get("articles", [])
                    news_data[label] = [
                        {
                            "title": article.get("title"),
                            "source": article["source"].get("name"),
                            "published_at": article.get("publishedAt"),
                            "url": article.get("url"),
                            "description": article.get("description") or "No description available."
                        }
                        for article in articles[:15]
                    ]
                else:
                    print(f"Error for {label}: {response.text}")
                    news_data[label] = []

            # Format and send email
            email_content = format_email_content(news_data)
            send_email("Your Top News Update", email_content)

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"message": "Email sent successfully!"}).encode())

        except Exception as e:
            print(f"Error in handler: {str(e)}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

def format_email_content(news_data):
    """Format the news data into a modern, responsive HTML email."""

    # Category colors - vibrant, high-contrast for dark theme
    category_colors = {
        "business news": "#00ff88",
        "entertainment news": "#ff0080",
        "general news": "#00d4ff",
        "health news": "#a855f7",
        "science news": "#06b6d4",
        "sports news": "#f97316",
        "technology news": "#8b5cf6"
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
                        </tr>
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

    content += """
                            </td>
                        </tr>
                        <tr>
                            <td bgcolor="#000000" style="background-color: #000000; border-top: 1px solid #1f1f1f; padding: 24px; text-align: center;">
                                <p style="color: #6b7280; margin: 0; font-size: 11px;">You're receiving this because you subscribed to daily news updates.</p>
                                <p style="color: #6b7280; margin: 10px 0 0 0; font-size: 11px;">Powered by NewsAPI • Delivered twice daily</p>
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
