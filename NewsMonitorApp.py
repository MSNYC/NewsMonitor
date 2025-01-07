import os
import requests
from flask import Flask, request, jsonify, abort
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

app = Flask(__name__)

# Environment variables
NEWS_API_KEY = os.getenv('NEWS_API_KEY')
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
SENDER_EMAIL = os.getenv('SENDER_EMAIL')
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

@app.route('/', methods=['GET'])
def fetch_and_send_news():
    api_key = request.headers.get('X-API-KEY')
    if api_key != MY_SECRET_API_KEY:
        abort(403)

    news_data = {}

    for label, category in CATEGORIES.items():
        # Construct the News API URL for top headlines
        url = (f"https://newsapi.org/v2/top-headlines?"
               f"category={category}&"
               f"country=us&"
               f"pageSize=15&"
               f"apiKey={NEWS_API_KEY}")

        response = requests.get(url)
        print(f"Request URL: {url}")
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Content: {response.text}")

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
                for article in articles[:15]  # Limit to top 15 articles
            ]
        else:
            print(f"Error for {label}: {response.text}")
            news_data[label] = []

    email_content = format_email_content(news_data)
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
                    {article['description']}<br>
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