import os
import requests
from flask import Flask, jsonify
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

app = Flask(__name__)

# Environment variables
NEWS_API_KEY = os.getenv('NEWS_API_KEY')
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
RECIPIENT_EMAIL = os.getenv('RECIPIENT_EMAIL')

# Categories to pull
CATEGORIES = {
    "world": "general",
    "health": "health",
    "technology": "technology",
    "artificial intelligence": "artificial intelligence",
    "oncology": "cancer",
    "science": "science"
}

# Route to trigger email
@app.route('/', methods=['GET'])
def fetch_and_send_news():
    news_data = {}

    for label, category in CATEGORIES.items():
        if category == "artificial intelligence" or category == "cancer":
            # For custom queries like "AI" or "cancer", use "everything" endpoint
            url = f"https://newsapi.org/v2/everything?q={category}&apiKey={NEWS_API_KEY}"
        else:
            # For general categories, use "top-headlines" endpoint
            url = f"https://newsapi.org/v2/top-headlines?category={category}&country=us&apiKey={NEWS_API_KEY}"

        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            news_data[label] = [
                {
                    "title": article["title"],
                    "source": article["source"]["name"],
                    "published_at": article["publishedAt"],
                    "url": article["url"]
                }
                for article in data.get("articles", [])[:5]  # Get top 5 articles per category
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
    sender_email = os.getenv('RECIPIENT_EMAIL')  # Use the recipient email as the sender email
    recipient_email = os.getenv('RECIPIENT_EMAIL')  # Reuse for sending to yourself

    message = Mail(
        from_email=sender_email,  # Sender email (must be verified in SendGrid)
        to_emails=recipient_email,
        subject=subject,
        html_content=content
    )

    try:
        sg = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
        response = sg.send(message)
        print(f"Email sent! Status code: {response.status_code}")
    except Exception as e:
        print(f"Error sending email: {e}")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)