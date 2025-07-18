# STACK-INCOGNITO v3.8 – Autonomous Revenue Engine with OUI [Locked for Hai]

import os
import random
import sqlite3
import requests
import feedparser
import time
import tweepy
from flask import Flask, redirect, jsonify, request, render_template_string
from apscheduler.schedulers.background import BackgroundScheduler
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

# === SYSTEM METADATA ===
__OWNER__ = "Hai"
__VERSION__ = "v3.8 | OUI Enhanced"
__SYSTEM__ = "STACK-INCOGNITO-UNIT"

app = Flask(__name__)
DB_FILE = "incognito_bot.db"
ADMIN_PASSWORD = os.environ.get("INCOGNITO_ADMIN_PASS", "supersecret")
TELEGRAM_TOKEN = os.environ.get("INCOGNITO_TG_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("INCOGNITO_TG_CHAT_ID", "")
TWITTER_CONSUMER_KEY = os.environ.get("TWITTER_CONSUMER_KEY", "")
TWITTER_CONSUMER_SECRET = os.environ.get("TWITTER_CONSUMER_SECRET", "")
TWITTER_ACCESS_TOKEN = os.environ.get("TWITTER_ACCESS_TOKEN", "")
TWITTER_ACCESS_SECRET = os.environ.get("TWITTER_ACCESS_SECRET", "")

AFFILIATE_BASE = {
    'memory': ["https://www.digistore24.com/redir/xxxxxx/username/"],
    'crypto': ["https://clickbank.com/offer/xxxxxx?ref=yourref"],
    'health': ["https://www.amazon.co.uk/dp/xxxxxx?tag=yourtag"],
}
KEYWORDS = ['boost memory', 'build muscle', 'passive income', 'crypto course', 'anxiety hacks']
RSS_SOURCES = [
    'https://news.google.com/rss/search?q={}',
    'https://www.reddit.com/search.rss?q={}']
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (X11; Linux x86_64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
]

COMMISSION_MAP = {
    'memory': 10.0,
    'crypto': 20.0,
    'health': 15.0
}
CONVERSION_RATE = 0.03

# === DB Setup ===
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS links (
            slug TEXT PRIMARY KEY,
            url TEXT,
            title TEXT,
            clicks INTEGER DEFAULT 0,
            created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            source TEXT
        )
    """)
    conn.commit()
    conn.close()

# === Utilities ===
def generate_slug(title):
    return title.lower().replace(" ", "-").replace("/", "").replace("'", "")[:30]

def insert_link(slug, url, title, source):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO links (slug, url, title, source) VALUES (?, ?, ?, ?)", (slug, url, title, source))
    conn.commit()
    conn.close()
    send_telegram_message(f"[STACK-INCOGNITO] New Link: {title}\n{url}")
    tweet_link(title, slug)

def send_telegram_message(message):
    if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        try:
            requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                         params={"chat_id": TELEGRAM_CHAT_ID, "text": message})
        except Exception as e:
            print(f"[!] Telegram Error: {e}")

def tweet_link(title, slug):
    try:
        if TWITTER_CONSUMER_KEY:
            auth = tweepy.OAuth1UserHandler(
                TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET,
                TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET
            )
            api = tweepy.API(auth)
            tweet = f"{title} → http://yourdomain.com/r/{slug} #haiOnly #revenue"
            api.update_status(tweet)
    except Exception as e:
        print(f"[!] Twitter Post Failed: {e}")

# === Scraper Bot ===
def fetch_and_insert():
    print("[+] STACK-INCOGNITO fetching...")
    headers = {"User-Agent": random.choice(USER_AGENTS)}
    for kw in KEYWORDS:
        encoded_kw = quote_plus(kw)
        for rss in RSS_SOURCES:
            feed = feedparser.parse(rss.format(encoded_kw))
            for entry in feed.entries[:2]:
                title = entry.title
                slug = generate_slug(title)
                aff_key = 'memory' if 'memory' in kw else 'crypto' if 'crypto' in kw else 'health'
                aff_link = random.choice(AFFILIATE_BASE.get(aff_key, []))
                full_link = f"{aff_link}&ref={quote_plus(title[:10])}"
                insert_link(slug, full_link, title, rss)
    print("[+] STACK-INCOGNITO complete.")

# === Owner UI Route ===
@app.route('/oui')
def owner_ui():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT title, clicks FROM links")
    data = c.fetchall()
    conn.close()
    total = 0.0
    html_rows = ""
    for title, clicks in data:
        key = 'memory' if 'memory' in title.lower() else 'crypto' if 'crypto' in title.lower() else 'health'
        commission = COMMISSION_MAP.get(key, 10.0)
        conversions = round(clicks * CONVERSION_RATE, 2)
        earnings = round(conversions * commission, 2)
        total += earnings
        html_rows += f"<tr><td>{title}</td><td>{clicks}</td><td>{conversions}</td><td>£{earnings}</td></tr>"
    return f"""
        <html><body>
        <h2>Owner User Interface (OUI) – STACK-INCOGNITO</h2>
        <table border=1>
        <tr><th>Title</th><th>Clicks</th><th>Conversions (est)</th><th>Earnings</th></tr>
        {html_rows}
        </table>
        <p><b>Total Estimated Daily Revenue: £{round(total, 2)}</b></p>
        <p><b>Weekly: £{round(total*7, 2)} | Monthly: £{round(total*30, 2)}</b></p>
        </body></html>
    """

# === Core Routes ===
@app.route('/')
def index():
    return "STACK-INCOGNITO v3.8: Personal Rev Engine Active."

@app.route('/r/<slug>')
def redirect_link(slug):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT url FROM links WHERE slug = ?", (slug,))
    row = c.fetchone()
    if row:
        c.execute("UPDATE links SET clicks = clicks + 1 WHERE slug = ?", (slug,))
        conn.commit()
        conn.close()
        return redirect(row[0])
    conn.close()
    return "Invalid slug", 404

# === Admin Panel ===
@app.route('/admin', methods=['GET'])
def admin():
    pw = request.args.get("pw", "")
    if pw != ADMIN_PASSWORD:
        return "Not allowed", 403
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT slug, title, clicks, created, source FROM links ORDER BY created DESC")
    rows = c.fetchall()
    conn.close()
    html = """<html><body><h2>STACK-INCOGNITO Admin</h2><table border=1><tr><th>Slug</th><th>Title</th><th>Clicks</th><th>Created</th><th>Source</th></tr>{}</table></body></html>"""
    rows_html = ''.join([f"<tr><td>{r[0]}</td><td>{r[1]}</td><td>{r[2]}</td><td>{r[3]}</td><td>{r[4]}</td></tr>" for r in rows])
    return html.format(rows_html)

# === Scheduler Setup ===
if __name__ == '__main__':
    init_db()
    fetch_and_insert()
    scheduler = BackgroundScheduler()
    scheduler.add_job(fetch_and_insert, 'interval', hours=6)
    scheduler.start()
    app.run(host='0.0.0.0', port=5000)

