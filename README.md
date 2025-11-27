# NewsMonitor

Automated news digest delivery system that aggregates breaking news from multiple RSS feeds and sends beautifully formatted HTML emails twice daily.

## Features

- 📰 **Real-time news** from 50+ RSS feeds across 7 categories
- 🎯 **Smart deduplication** - prevents repeated articles across emails
- 🌑 **Dark-themed, mobile-responsive** email design
- 🔗 **Quick-jump navigation** with color-coded category links
- 📊 **Feed health monitoring** with automatic alerts and stats
- ⏰ **Automated delivery** via GitHub Actions (8 AM & 8 PM ET)
- 🔒 **Secure** - all credentials stored as environment variables
- 💰 **100% free** - no paid services required

## Tech Stack

- **Hosting**: Vercel (serverless functions)
- **Email**: Gmail SMTP (free tier: 500 emails/day)
- **News Sources**: RSS feeds from CNN, BBC, Reuters, TechCrunch, etc.
- **Scheduling**: GitHub Actions (cron jobs)
- **Language**: Python 3.x
- **Libraries**: feedparser, smtplib, email.mime

## News Categories

1. **Top News** - CNN, BBC, NPR, Reuters, NY Times, The Guardian, Al Jazeera, Washington Post
2. **Technology** - TechCrunch, The Verge, Ars Technica, Wired, Engadget, CNET, ZDNet, Techmeme
3. **AI** - MIT Tech Review, VentureBeat, AI News, MarTechPost, DeepMind, OpenAI, Google AI
4. **Arts & Entertainment** - Variety, Hollywood Reporter, CNN, BBC, Deadline, EW, Rolling Stone
5. **Science** - ScienceDaily, Scientific American, BBC, Phys.org, Nature, Space.com, New Scientist
6. **Health** - Medical News Today, Healthline, CNN Health, BBC Health, WebMD, NIH
7. **Business** - Bloomberg, CNBC, CNN Money, BBC Business, FT, WSJ, MarketWatch, Forbes

## Prerequisites

- Vercel account (free)
- Gmail account with App Password enabled
- GitHub account (for scheduling)

## Setup

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/NewsMonitor.git
cd NewsMonitor
```

### 2. Set Up Gmail SMTP

1. Go to your Google Account settings
2. Enable 2-Step Verification
3. Go to **Security** → **App passwords**
4. Generate an app password for "Mail"
5. Save the 16-character password

### 3. Deploy to Vercel

1. Install Vercel CLI: `npm i -g vercel`
2. Run: `vercel`
3. Follow the prompts to deploy
4. Add environment variables in Vercel dashboard:

```
GMAIL_ADDRESS=your-email@gmail.com
GMAIL_APP_PASSWORD=your-16-char-password
RECIPIENT_EMAIL=recipient@example.com
MY_SECRET_API_KEY=your-random-secret-key
```

**Generate a random API key:**
```bash
openssl rand -hex 32
```

### 4. Set Up Automated Scheduling

This requires the companion [news-cron-job](https://github.com/MSNYC/news-cron-job) repository.

1. Clone the cron job repo
2. Add `MY_SECRET_API_KEY` to GitHub Secrets
3. Update the Vercel URL in `run_cron.py`
4. GitHub Actions will trigger the news digest twice daily

## Customization

### Change Categories

Edit `RSS_FEEDS` dictionary in `api/send-news.py`:

```python
RSS_FEEDS = {
    "Your Category": [
        "https://example.com/feed.rss",
        "https://another-source.com/rss"
    ]
}
```

### Modify Colors

Edit `category_colors` in `format_email_content()`:

```python
category_colors = {
    "Your Category": "#00ff88",  # Bright cyan
}
```

### Adjust Timing

Edit `.github/workflows/cron.yml` in the news-cron-job repo:

```yaml
schedule:
  - cron: '0 13,1 * * *'  # 8 AM & 8 PM ET
```

### Filter by Article Age

Change the cutoff date in `api/send-news.py`:

```python
cutoff_date = datetime.now() - timedelta(days=7)  # Last 7 days
```

## Email Features

### Dark Theme
- Pure black background (#000000)
- High-contrast vibrant colors
- Optimized for Apple Mail and Gmail

### Smart Deduplication
- Tracks sent articles for 30 days to prevent repeats
- Removes duplicates within each email batch
- Uses URL and content-based hashing for accuracy
- Shows deduplication stats in email footer

### Quality Monitoring
- Feed health dashboard at bottom
- Conditional alert banner if feeds fail
- Article count and success rate displayed
- Duplicate removal statistics

### Responsive Design
- Mobile-optimized layout
- Table-based for email client compatibility
- Works on iPhone, Android, desktop

## Architecture

```
┌─────────────────┐
│ GitHub Actions  │  Triggers twice daily (cron)
└────────┬────────┘
         │ HTTP GET with API key
         ▼
┌─────────────────┐
│ Vercel Function │  Fetches RSS feeds, formats email
│ (send-news.py)  │
└────────┬────────┘
         │ SMTP
         ▼
┌─────────────────┐
│  Gmail SMTP     │  Sends email to recipient
└─────────────────┘
```

## Security

- ✅ All credentials stored as environment variables
- ✅ API key authentication for endpoint
- ✅ No secrets in code repository
- ✅ GitHub Secrets for cron job API key
- ✅ Gmail App Password (not main password)

## Cost

**$0/month** - All services used are free tier:
- Vercel: Free serverless functions
- Gmail: 500 emails/day free
- GitHub Actions: Free for public repos
- RSS feeds: Free

## Troubleshooting

### Email going to spam?

- Check Gmail settings aren't blocking it
- Ensure Gmail App Password is correct
- Verify SENDER_EMAIL and RECIPIENT_EMAIL are set

### No articles in email?

- Check Vercel function logs for RSS feed errors
- Some feeds may be temporarily down
- Look for feed health stats at bottom of email

### Repeated articles appearing?

- Deduplication system tracks articles for 30 days
- History is stored in `/tmp/sent_articles.json` on Vercel
- If running locally, history resets between sessions
- Check email footer for "Duplicates Removed" count

### Old articles appearing?

- Date filter is set to 7 days by default
- Some RSS feeds may have incorrect dates
- Check feed quality in Vercel logs

### Dark theme not working?

- Ensure you're viewing on a supported email client
- Try both light and dark system modes
- Gmail and Apple Mail are fully supported

## Contributing

Contributions welcome! Feel free to:
- Add more RSS feed sources
- Improve email design
- Add new categories
- Enhance monitoring features

## License

MIT License - feel free to use for personal or commercial projects.

## Credits

Built with Python, Vercel, and love for staying informed. Powered by RSS feeds from news organizations worldwide.
