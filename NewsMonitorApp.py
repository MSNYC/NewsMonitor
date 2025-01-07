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

        # Construct the News API URL
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
            print(f"JSON Response for {label}: {data}")  # Debug: full JSON output for each category

            articles = data.get("articles", [])
            print(f"Number of articles retrieved for '{label}': {len(articles)}")  # Log how many articles were found

            news_data[label] = [
                {
                    "title": article.get("title", "No title"),
                    "source": article.get("source", {}).get("name", "No source"),
                    "published_at": article.get("publishedAt", "No date"),
                    "url": article.get("url", "No URL")
                }
                for article in articles[:15]
            ]

            # Debug individual articles to make sure they have content
            for i, article in enumerate(news_data[label]):
                print(f"Article {i + 1} for '{label}': {article}")

        else:
            print(f"Error for {label}: {response.text}")
            news_data[label] = []

    email_content = format_email_content(news_data)
    print(f"Generated Email Content: {email_content}")  # Debug final email content
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