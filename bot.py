import discord
import zipfile
import subprocess
import os
import shutil
import re
from flask import Flask
from threading import Thread

# 環境変数からトークン取得
TOKEN = os.environ.get("DISCORD_TOKEN")
FFMPEG_PATH = "/usr/bin/ffmpeg"  # 環境に合わせて変更

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# 画像パターン自動検出
def find_image_pattern(folder_path):
    files = sorted([f for f in os.listdir(folder_path) if f.lower().endswith((".png", ".jpg"))])
    if not files:
        return None
    # 最初の数字を検出して桁数を取得
    match = re.search(r"(\d+)", files[0])
    if match:
        width = len(match.group(1))
        ext = os.path.splitext(files[0])[1]
        return os.path.join(folder_path, f"%0{width}d{ext}")
    else:
        # 数字なしなら単一ファイル
        return os.path.join(folder_path, files[0])

@client.event
async def on_ready():
    print("Bot is ready!")

@client.event
async def on_message(message):
    if message.author.bot:
        return

    if message.attachments:
        file = message.attachments[0]
        if file.filename.endswith(".zip"):
            await message.reply("Converting now...")

            # 以前の作業フォルダを削除
            if os.path.exists("boot"):
                shutil.rmtree("boot")

            await file.save("bootanimation.zip")

            # 解凍
            with zipfile.ZipFile("bootanimation.zip", 'r') as z:
                z.extractall("boot")

            # desc.txt を読む
            desc_path = os.path.join("boot", "desc.txt")
            if not os.path.exists(desc_path):
                await message.reply("desc.txt not found")
                return

            with open(desc_path, "r") as f:
                lines = f.readlines()

            # 幅・高さ・fps を取得
            width, height, fps = lines[0].split()
            fps = int(fps)

            inputs = []
            part_index = 0

            for line in lines[1:]:
                parts = line.strip().split()
                if len(parts) == 4 and parts[0] == "p":
                    repeat = int(parts[1])
                    folder_name = parts[3]
                    folder_path = os.path.join("boot", folder_name)
                    
                    # フォルダが無ければ自動補完
                    if not os.path.exists(folder_path):
                        subfolders = [d for d in os.listdir("boot") if os.path.isdir(os.path.join("boot", d))]
                        if not subfolders:
                            await message.reply("No folders found in boot")
                            return
                        folder_path = os.path.join("boot", subfolders[0])

                    image_pattern = find_image_pattern(folder_path)
                    if not image_pattern:
                        await message.reply(f"No images found in {folder_path}")
                        return

                    for _ in range(repeat if repeat != 0 else 1):
                        part_index += 1
                        output = f"part{part_index}.mp4"
                        cmd = [FFMPEG_PATH, "-y", "-framerate", str(fps), "-i", image_pattern,
                               "-vf", f"scale={width}:{height}", output]
                        print("Running:", " ".join(cmd))
                        result = subprocess.run(cmd)
                        if result.returncode != 0:
                            await message.reply(f"FFmpeg error in {output}")
                            return
                        inputs.append(output)

            # 全パートを連結
            list_file = "list.txt"
            with open(list_file, "w") as f:
                for mp4 in inputs:
                    f.write(f"file '{mp4}'\n")

            concat_cmd = [FFMPEG_PATH, "-y", "-f", "concat", "-safe", "0",
                          "-i", list_file, "-c", "copy", "output.mp4"]
            print("Running concat:", " ".join(concat_cmd))
            result = subprocess.run(concat_cmd)
            if result.returncode != 0 or not os.path.exists("output.mp4"):
                await message.reply("動画生成に失敗しました")
                return

            await message.reply("Done")
            await message.reply(file=discord.File("output.mp4"))

# Flask サーバーで常時稼働
app = Flask('')
@app.route('/')
def home():
    return "I'm alive"
def run():
    app.run(host='0.0.0.0', port=8000)
def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

keep_alive()
client.run(TOKEN)
