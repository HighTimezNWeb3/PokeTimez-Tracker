import os
import json
import discord
from discord.ext import tasks, commands
import requests
from bs4 import BeautifulSoup

intents = discord.Intents.default()
bot = commands.Bot(command_prefix='!', intents=intents)

CHANNEL_ID = int(os.getenv('CHANNEL_ID'))   # the room where it posts

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

@tasks.loop(minutes=30)  # checks every 30 minutes
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

            # Only Pokémon cards and TCG stuff
            keywords = ['tcg', 'card', 'booster', 'sleeves', 'pokémon', 'pixels', 'mega evolution']
            if any(kw in title.lower() for kw in keywords) and title not in seen:
                if '/products/' in href or '/product/' in href:
                    new_posts.append(f"**🃏 NEW DROP ALERT!** {title}\n{full_url}")
                    seen.add(title)
                    if len(new_posts) >= 5:  # don't spam
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

bot.run(os.getenv('DISCORD_TOKEN'))