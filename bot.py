import os
import discord
from discord.ext import commands
from convert import convert_images_to_video

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")  # ← Koyebの環境変数に入れる

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


@bot.command()
async def convert(ctx):
    folder = "temp"

    await ctx.send("Converting...")

    try:
        output_path = convert_images_to_video(folder)
        if output_path:
            await ctx.send(file=discord.File(output_path))
        else:
            await ctx.send("Error.")
    except Exception as e:
        await ctx.send(f"Error: {e}")


bot.run(DISCORD_TOKEN)
