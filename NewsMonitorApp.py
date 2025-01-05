import os
import requests
from flask import Flask, request, jsonify, abort
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from datetime import datetime, timedelta

app = Flask(__name__)

# Environment variables
NEWS_API_KEY = os.getenv('NEWS_API_KEY')  # News API key
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')  # SendGrid API key
SENDER_EMAIL = os.getenv('SENDER_EMAIL')  # Verified sender email in SendGrid
RECIPIENT_EMAIL = os.getenv('RECIPIENT_EMAIL')  # Alias or recipient email address
MY_SECRET_API_KEY = os.getenv('MY_SECRET_API_KEY')  # Custom API key for security

# Categories with multiple keywords
CATEGORIES = {
    "world news": ["world", "international"],
    "oncology news": ["oncology", "cancer", "cancer research"],
    "health news": ["health", "wellness", "public health"],
    "science news": ["science", "space", "scientific discovery"],
    "technology news": ["technology", "tech industry", "gadgets"],
    "artificial intelligence news": ["AI", "artificial intelligence", "machine learning"]
}

# Route to trigger email
@app.route('/', methods=['GET'])
def fetch_and_send_news():
    # Check for API key in headers
    api_key = request.headers.get('X-API-KEY')
    if api_key != MY_SECRET_API_KEY:
        abort(403)  # Forbidden if the API key is incorrect

    news_data = {}

    # Current time and 12 hours ago
    now = datetime.utcnow()
    twelve_hours_ago = now - timedelta(hours=12)

    # Fetch news for each category
    for label, keywords in CATEGORIES.items():
        # Combine keywords into a single query string
        query_string = " OR ".join(keywords)
        url = (f"https://newsapi.org/v2/everything?"
               f"q={query_string}&"
               f"from={twelve_hours_ago.strftime('%Y-%m-%dT%H:%M:%S')}&"
               f"to={now.strftime('%Y-%m-%dT%H:%M:%S')}&"
               f"sortBy=popularity&"
               f"apiKey={NEWS_API_KEY}")

        # Make the request to News API
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            articles = data.get("articles", [])
            news_data[label] = [
                {
                    "title": article.get("title"),
                    "source": article["source"].get("name"),
                    "published_at": article.get("publishedAt"),
                    "url": article.get("url")
                }
                for article in articles[:15]  # Get top 15 popular articles
            ]
        else:
            news_data[label] = []

    # Format email content
    email_content = format_email_content(news_data)

    # Send the email
    send_email("Your Top News Update", email_content)

    return jsonify({"message": "Email sent successfully!"})


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
                    <a href="{article['url']}">Read more</a>
                </p>
                """
        else:
            content += "<p>No articles found for this category.</p>"
    return content


def send_email(subject, content):
    """Send email using SendGrid."""
    sender_email = SENDER_EMAIL  # Verified email in SendGrid
    recipient_email = RECIPIENT_EMAIL  # Alias or recipient email

    message = Mail(
        from_email=sender_email,
        to_emails=recipient_email,
        subject=subject,
        html_content=content
    )

    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        sg.send(message)
    except Exception as e:
        pass  # Do nothing on errors for now


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)