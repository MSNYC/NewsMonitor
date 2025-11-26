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
    """Format the news data into HTML for the email."""
    content = "<h1>Your Top News Update</h1>"
    for category, articles in news_data.items():
        content += f"<h2>{category.capitalize()}</h2>"
        if articles:
            for article in articles:
                content += f"""
                <p>
                    <strong>{article['title']}</strong><br>
                    <em>{article['source']} - {article['published_at']}</em><br>
                    {article['description']}<br>
                    <a href="{article['url']}">Read more</a>
                </p>
                """
        else:
            content += "<p>No articles found for this category.</p>"
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
