import os
import requests
from flask import Flask, request, jsonify, abort
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from datetime import datetime, timedelta
from urllib.parse import quote

app = Flask(__name__)

# Environment variables
NEWS_API_KEY = os.getenv('NEWS_API_KEY')
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
SENDER_EMAIL = os.getenv('SENDER_EMAIL')
RECIPIENT_EMAIL = os.getenv('RECIPIENT_EMAIL')
MY_SECRET_API_KEY = os.getenv('MY_SECRET_API_KEY')

# Simplified categories with single keywords
CATEGORIES = {
    "world news": "world",
    "New York City news": '"New York City"',
    "science news": "science",
    "technology news": "technology",
    "artificial intelligence news": '"artificial intelligence"',
    "health news": "health",
    "oncology news": "oncology"
}

@app.route('/', methods=['GET'])
def fetch_and_send_news():
    api_key = request.headers.get('X-API-KEY')
    if api_key != MY_SECRET_API_KEY:
        abort(403)

    news_data = {}
    now = datetime.utcnow()
    twelve_hours_ago = now - timedelta(hours=12)

    for label, keyword in CATEGORIES.items():
        query_string = quote(keyword)
        url = (f"https://newsapi.org/v2/everything?"
               f"q={query_string}&"
               f"from={twelve_hours_ago.isoformat()}&"
               f"to={now.isoformat()}&"
               f"sortBy=popularity&"
               f"apiKey={NEWS_API_KEY}")

        response = requests.get(url)
        print(f"Request URL: {url}")
        print(f"Response Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            articles = data.get("articles", [])
            news_data[label] = [
                {
                    "title": article.get("title", "[No Title]"),
                    "source": article["source"].get("name", "Unknown Source"),
                    "published_at": format_datetime(article.get("publishedAt")),
                    "description": article.get("description", "No Description Available"),
                    "url": article.get("url", "#")
                }
                for article in articles[:15] if article.get("title") and article.get("url") and article.get("title").lower() != "[removed]"
            ]
        else:
            print(f"Error for {label}: {response.text}")
            news_data[label] = []

    email_content = format_email_content(news_data)
    send_email("Your Top News Update", email_content)

    return jsonify({"message": "Email sent successfully!"})

def format_datetime(iso_datetime):
    """Convert ISO datetime to a more readable format."""
    if not iso_datetime:
        return "Unknown Date"
    try:
        return datetime.fromisoformat(iso_datetime.replace('Z', '')).strftime('%B %d, %Y at %I:%M %p')
    except ValueError:
        return "Unknown Date"

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
                    <p>{article['description']}</p>
                    <a href="{article['url']}">Read more</a>
                </p>
                <hr>
                """
        else:
            content += "<p>No relevant articles found for this category.</p>"
    return content

def send_email(subject, content):
    """Send the email using SendGrid."""
    sender_email = SENDER_EMAIL
    recipient_email = RECIPIENT_EMAIL

    message = Mail(
        from_email=sender_email,
        to_emails=recipient_email,
        subject=subject,
        html_content=content
    )

    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        print(f"Email sent: {response.status_code}")
    except Exception as e:
        print(f"Error sending email: {e}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)