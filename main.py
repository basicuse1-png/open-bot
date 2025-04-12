import discord
import requests
import asyncio
import random
import json
import os
import nest_asyncio
from datetime import datetime, timezone
from dotenv import load_dotenv
load_dotenv()

nest_asyncio.apply()

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OWNER_ID = os.getenv("OWNER_ID")
API_URL = "https://openrouter.ai/api/v1/chat/completions"
MEMORY_FILE = "memory.json"
BLOCKED_CHANNELS_FILE = "blocked_channels.json"
MAX_MEMORY_ENTRIES = 500

intents = discord.Intents.all()
client = discord.Client(intents=intents)

bot_name = "Aren"
human_name = "Alex"

def load_blocked_channels():
    if not os.path.exists(BLOCKED_CHANNELS_FILE):
        return []
    try:
        with open(BLOCKED_CHANNELS_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_blocked_channels(channels):
    with open(BLOCKED_CHANNELS_FILE, "w") as f:
        json.dump(channels, f)

blocked_channels = load_blocked_channels()

def load_memory():
    if not os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "w") as f:
            json.dump({"convos": []}, f)
    try:
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    except:
        return {"convos": []}

def save_memory(mem):
    if len(mem["convos"]) > MAX_MEMORY_ENTRIES:
        mem["convos"] = mem["convos"][-MAX_MEMORY_ENTRIES:]
    with open(MEMORY_FILE, "w") as f:
        json.dump(mem, f, indent=4)

memory = load_memory()

def get_headers():
    return {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

def create_payload(msg):
    return {
        "model": "deepseek/deepseek-chat",
        "messages": [{"role": "user", "content": msg}]
    }

async def generate_response(prompt):
    try:
        res = requests.post(API_URL, headers=get_headers(), json=create_payload(prompt))
        if res.status_code == 200:
            return res.json()['choices'][0]['message']['content'].strip()
        else:
            return "idk lol"
    except:
        return "bro i have to GTG bye"

async def simulate_typing(channel, msg):
    delay = max(len(msg.split()) * 2, 1.2)
    async with channel.typing():
        await asyncio.sleep(min(delay, 8))

@client.event
async def on_ready():
    print(f"{bot_name} aka {human_name} online")
    await client.change_presence(status=discord.Status.online, activity=discord.Game(name="just chillin"))

@client.event
async def on_message(message):
    global blocked_channels
    if message.author == client.user:
        return

    msg = message.content.lower()
    user_id = str(message.author.id)
    channel_id = message.channel.id
    response = None

    if message.content.startswith("!arenblock") and str(message.author.id) == OWNER_ID:
        if channel_id not in blocked_channels:
            blocked_channels.append(channel_id)
            save_blocked_channels(blocked_channels)
            await message.channel.send("🔕 Bot is now blocked from this channel.")
        else:
            await message.channel.send("Already blocked.")
        return

    elif message.content.startswith("!arenunblock") and str(message.author.id) == OWNER_ID:
        if channel_id in blocked_channels:
            blocked_channels.remove(channel_id)
            save_blocked_channels(blocked_channels)
            await message.channel.send("✅ Bot is now unblocked from this channel.")
        else:
            await message.channel.send("Not blocked.")
        return

    if channel_id in blocked_channels:
        return

    if human_name.lower() in msg and bot_name.lower() not in msg:
        response = f"nah i'm {bot_name}"
        await message.channel.send(response)

    elif "join vc" in msg or "join call" in msg:
        if message.author.voice and message.author.voice.channel:
            try:
                await message.author.voice.channel.connect()
                response = "yo i'm in"
            except:
                response = "can't join rn"
        if response:
            await message.channel.send(response)

    elif "discord.gg" in msg:
        response = "bet, drop the link"
        await message.channel.send(response)

    else:
        # Maintain user focus tracking
        if not hasattr(client, "focus_users"):
            client.focus_users = {}

        now = datetime.now(timezone.utc)
        last_focus_time = client.focus_users.get(user_id)

        is_recent_focus = last_focus_time and (now - last_focus_time).total_seconds() < 180  # 3 min
        mentioned_bot = bot_name.lower() in msg or human_name.lower() in msg or client.user.mentioned_in(message)

        if mentioned_bot or is_recent_focus or msg.startswith(bot_name.lower()) or msg.startswith(human_name.lower()):
            client.focus_users[user_id] = now  # update last focus time
            prompt = f"You're {bot_name}, a chill US dude. Talk like you're relaxed and real. Short replies, no emojis. Reply to: {msg}"
            response = await generate_response(prompt)
            await simulate_typing(message.channel, response)
            await message.channel.send(response)

        elif random.random() < 0.1:
            response = await generate_response(f"React casually like a real dude. Respond to: {msg}")
            await simulate_typing(message.channel, response)
            await message.channel.send(response)

    memory['convos'].append({
        "user": str(message.author),
        "message": msg,
        "response": response if response else "none",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    save_memory(memory)

@client.event
async def on_voice_state_update(member, before, after):
    if member == client.user:
        if after.channel:
            print(f"{human_name} joined VC: {after.channel.name}")
        elif before.channel:
            print(f"{human_name} left VC: {before.channel.name}")

async def start_bot():
    await client.start(DISCORD_BOT_TOKEN)

loop = asyncio.get_event_loop()
loop.create_task(start_bot())
loop.run_forever()
