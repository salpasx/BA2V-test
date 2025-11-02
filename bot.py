import discord
from discord.ext import commands
from convert import convert_part
import subprocess

# ここにあなたの Discord Bot トークンを入れる
DISCORD_TOKEN = "YOUR_DISCORD_TOKEN"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot {bot.user} が起動しました。")

# 例: !convert コマンドで動画変換を実行
@bot.command()
async def convert(ctx):
    await ctx.send("Converting...")
    
    parts = [f"boot/part{i}" for i in range(5)]
    outputs = []

    for i, folder in enumerate(parts):
        output_file = f"part{i}.mp4"
        success = convert_part(folder, output_file, fps=30, width=720, height=1600)
        if success:
            outputs.append(output_file)

    if outputs:
        with open("list.txt", "w") as f:
            for mp4 in outputs:
                f.write(f"file '{mp4}'\n")
        subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "list.txt",
                        "-c", "copy", "output.mp4"])
        await ctx.send("動画変換完了: output.mp4")
    else:
        await ctx.send("有効な動画がありません。")

bot.run(DISCORD_TOKEN)
