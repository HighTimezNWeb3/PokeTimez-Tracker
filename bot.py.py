import os
import json
import discord
from discord.ext import tasks, commands
import requests
from bs4 import BeautifulSoup
from flask import Flask
import threading

intents = discord.Intents.default()
bot = commands.Bot(command_prefix='!', intents=intents)

CHANNEL_ID = int(os.getenv('CHANNEL_ID'))

SEEN_FILE = 'seen_products.json'

def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, 'r') as f:
            return set(json.load(f))
    return set()

def save_seen(seen):
    with open(SEEN_FILE, 'w') as f:
        json.dump(list(seen), f)

@bot.event
async def on_ready():
    print(f'{bot.user} is awake and hunting new Pokémon cards!')
    check_new_drops.start()

@tasks.loop(minutes=30)
async def check_new_drops():
    print("Peeking at the Pokémon shop...")
    url = "https://www.pokemoncenter.com/category/new-releases"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        seen = load_seen()
        new_posts = []
        potential_links = soup.find_all('a', href=True)

        for link in potential_links:
            title = link.get_text().strip()
            if not title or len(title) < 5:
                continue
            href = link['href']
            if not href.startswith('/'):
                continue
            full_url = "https://www.pokemoncenter.com" + href

            keywords = ['tcg', 'card', 'booster', 'sleeves', 'pokémon', 'pixels', 'mega evolution']
            if any(kw in title.lower() for kw in keywords) and title not in seen:
                if '/products/' in href or '/product/' in href:
                    new_posts.append(f"**🃏 NEW DROP ALERT!** {title}\n{full_url}")
                    seen.add(title)
                    if len(new_posts) >= 5:
                        break

        if new_posts:
            channel = bot.get_channel(CHANNEL_ID)
            if channel:
                for post in new_posts:
                    await channel.send(post)
                save_seen(seen)
            else:
                print("Channel not found!")
        else:
            print("No brand-new cards this time.")
    except Exception as e:
        print(f"Oops, shop peek failed: {e}")

# Tiny "I'm alive!" door so Render stays happy
def run_keepalive():
    app = Flask(__name__)
    @app.route('/')
    def home():
        return "PokéTimez Tracker is alive and watching for new cards! 🃏"
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

if __name__ == "__main__":
    threading.Thread(target=run_keepalive).start()
    bot.run(os.getenv('DISCORD_TOKEN'))
