import os
import requests
from flask import Flask, jsonify
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

app = Flask(__name__)

# Environment variables
NEWS_API_KEY = os.getenv('NEWS_API_KEY')  # News API key
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')  # SendGrid API key
SENDER_EMAIL = os.getenv('SENDER_EMAIL')  # Verified sender email in SendGrid
RECIPIENT_EMAIL = os.getenv('RECIPIENT_EMAIL')  # Alias or recipient email address

# Categories to pull
CATEGORIES = {
    "oncology": "cancer",
    "world": "general",
    "international": "general",
    "health": "health",
    "science": "science",
    "technology": "technology",
    "artificial intelligence": "artificial intelligence"
}

# Route to trigger email
@app.route('/', methods=['GET'])
def fetch_and_send_news():
    print("==> Fetching and sending news...")

    # Log environment variables
    print(f"NEWS_API_KEY: {'Loaded' if NEWS_API_KEY else 'Not Loaded'}")
    print(f"SENDGRID_API_KEY: {'Loaded' if SENDGRID_API_KEY else 'Not Loaded'}")
    print(f"SENDER_EMAIL: {SENDER_EMAIL if SENDER_EMAIL else 'Not Set'}")
    print(f"RECIPIENT_EMAIL: {RECIPIENT_EMAIL if RECIPIENT_EMAIL else 'Not Set'}")

    news_data = {}

    for label, category in CATEGORIES.items():
        if category == "artificial intelligence" or category == "cancer":
            # For specific queries like "AI" or "cancer", use the "everything" endpoint
            url = f"https://newsapi.org/v2/everything?q={category}&apiKey={NEWS_API_KEY}"
        else:
            # For general categories, use the "top-headlines" endpoint
            url = f"https://newsapi.org/v2/top-headlines?category={category}&country=us&apiKey={NEWS_API_KEY}"

        print(f"Requesting {label} news from {url}")
        response = requests.get(url)

        if response.status_code == 200:
            print(f"Success fetching {label} news: Status code {response.status_code}")
            data = response.json()
            articles = data.get("articles", [])
            print(f"Fetched {len(articles)} articles for {label}")
            news_data[label] = [
                {
                    "title": article.get("title"),
                    "source": article["source"].get("name"),
                    "published_at": article.get("publishedAt"),
                    "url": article.get("url")
                }
                for article in articles[:5]  # Get top 5 articles per category
            ]
        else:
            print(f"Error fetching {label} news: {response.status_code} - {response.text}")
            news_data[label] = []

    # Format email content
    email_content = format_email_content(news_data)
    print("==> Email content formatted:")
    print(email_content)

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
        print("==> Sending email...")
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        print(f"Email sent! Status code: {response.status_code}")
        print(f"Response body: {response.body}")
        print(f"Response headers: {response.headers}")
    except Exception as e:
        print(f"Error sending email: {e}")
        if hasattr(e, 'body'):
            print(f"Error body: {e.body}")


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)