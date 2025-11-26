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

    # Category colors for visual distinction
    category_colors = {
        "business news": "#2563eb",
        "entertainment news": "#dc2626",
        "general news": "#059669",
        "health news": "#7c3aed",
        "science news": "#0891b2",
        "sports news": "#ea580c",
        "technology news": "#4f46e5"
    }

    content = f"""
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                line-height: 1.6;
                color: #1f2937;
                background-color: #f9fafb;
                margin: 0;
                padding: 0;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background-color: #ffffff;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px 20px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 28px;
                font-weight: 700;
            }}
            .header p {{
                margin: 10px 0 0 0;
                opacity: 0.9;
                font-size: 14px;
            }}
            .content {{
                padding: 20px;
            }}
            .category {{
                margin-bottom: 35px;
            }}
            .category-header {{
                display: flex;
                align-items: center;
                margin-bottom: 15px;
                padding-bottom: 10px;
                border-bottom: 2px solid #e5e7eb;
            }}
            .category-badge {{
                display: inline-block;
                padding: 6px 12px;
                border-radius: 20px;
                color: white;
                font-size: 13px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            .article-card {{
                background: #f9fafb;
                border-left: 4px solid #e5e7eb;
                border-radius: 8px;
                padding: 16px;
                margin-bottom: 12px;
                transition: all 0.2s;
            }}
            .article-title {{
                font-size: 16px;
                font-weight: 600;
                color: #111827;
                margin: 0 0 8px 0;
                line-height: 1.4;
            }}
            .article-meta {{
                font-size: 13px;
                color: #6b7280;
                margin-bottom: 10px;
            }}
            .source-badge {{
                display: inline-block;
                background: #e5e7eb;
                padding: 2px 8px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: 500;
                color: #374151;
            }}
            .article-description {{
                font-size: 14px;
                color: #4b5563;
                margin: 10px 0;
                line-height: 1.5;
            }}
            .read-more {{
                display: inline-block;
                background: #4f46e5;
                color: white !important;
                text-decoration: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 600;
                margin-top: 8px;
                transition: background 0.2s;
            }}
            .read-more:hover {{
                background: #4338ca;
            }}
            .footer {{
                background: #f3f4f6;
                padding: 20px;
                text-align: center;
                font-size: 12px;
                color: #6b7280;
                border-top: 1px solid #e5e7eb;
            }}
            .no-articles {{
                color: #9ca3af;
                font-style: italic;
                padding: 20px;
                text-align: center;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📰 Your Daily News Digest</h1>
                <p>Top headlines across all major categories</p>
            </div>
            <div class="content">
    """

    for category, articles in news_data.items():
        color = category_colors.get(category, "#6b7280")
        content += f"""
            <div class="category">
                <div class="category-header">
                    <span class="category-badge" style="background-color: {color};">
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
                <div class="article-card">
                    <h3 class="article-title">{article['title']}</h3>
                    <div class="article-meta">
                        <span class="source-badge">{article['source']}</span>
                        <span style="margin-left: 8px;">{published_at}</span>
                    </div>
                    <div class="article-description">
                        {article['description']}
                    </div>
                    <a href="{article['url']}" class="read-more">Read Full Story →</a>
                </div>
                """
        else:
            content += '<div class="no-articles">No articles found for this category.</div>'

        content += "</div>"

    content += """
            </div>
            <div class="footer">
                <p>You're receiving this because you subscribed to daily news updates.</p>
                <p>Powered by NewsAPI • Delivered twice daily</p>
            </div>
        </div>
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

    # Add HTML content
    html_part = MIMEText(content, "html")
    message.attach(html_part)

    try:
        # Connect to Gmail SMTP server
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.sendmail(sender_email, recipient_email, message.as_string())
            print(f"Email sent successfully to {recipient_email}")
    except Exception as e:
        print(f"Error sending email: {e}")
