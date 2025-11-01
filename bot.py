import discord
import zipfile
import subprocess
import os
import shutil
import re
from flask import Flask
from threading import Thread

TOKEN = os.environ.get("DISCORD_TOKEN")
FFMPEG_PATH = "/usr/bin/ffmpeg"

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# ---------------------------
# 数字抽出 → 自動連番化
# ---------------------------
def normalize_images(folder):
    files = [f for f in os.listdir(folder) if f.lower().endswith((".png", ".jpg"))]
    if not files:
        return None

    extracted = []

    for f in files:
        # ファイル名から数字をすべて抽出
        nums = re.findall(r"(\d+)", f)
        if nums:
            num = int(nums[-1])   # 最後の数字を使用（android-logo-mask30_30 など）
        else:
            num = -1  # 数字なし

        extracted.append((f, num))

    # 数字なしファイルは後ろへ
    extracted.sort(key=lambda x: x[1])

    # 桁数を 4 桁に統一 (0001.png)
    new_files = []
    index = 1
    for old_name, _ in extracted:
        ext = os.path.splitext(old_name)[1]
        new_name = f"{index:04d}{ext}"
        os.rename(os.path.join(folder, old_name),
                  os.path.join(folder, new_name))
        new_files.append(new_name)
        index += 1

    return os.path.join(folder, "%04d" + ext)


# ---------------------------
# Bot Ready
# ---------------------------
@client.event
async def on_ready():
    print("Bot is ready!")


# ---------------------------
# Main
# ---------------------------
@client.event
async def on_message(message):
    if message.author.bot:
        return

    # ZIP を受け取ったら処理開始
    if message.attachments:
        file = message.attachments[0]
        if file.filename.endswith(".zip"):
            await message.reply("Converting now...")

            # 作業用フォルダ削除
            if os.path.exists("boot"):
                shutil.rmtree("boot")

            await file.save("bootanimation.zip")

            # 解凍
            with zipfile.ZipFile("bootanimation.zip", 'r') as z:
                z.extractall("boot")

            # desc.txt 読み込み
            desc_path = os.path.join("boot", "desc.txt")
            if not os.path.exists(desc_path):
                await message.reply("desc.txt not found")
                return

            with open(desc_path, "r") as f:
                lines = f.readlines()

            width, height, fps = lines[0].split()
            fps = int(fps)

            inputs = []
            part_index = 0

            # desc.txt の行を解析
            for line in lines[1:]:
                parts = line.strip().split()
                if len(parts) == 4 and parts[0] == "p":
                    repeat = int(parts[1])
                    folder_name = parts[3]
                    folder_path = os.path.join("boot", folder_name)

                    # フォルダが無い場合 → 自動補完
                    if not os.path.exists(folder_path):
                        sub = [d for d in os.listdir("boot") if os.path.isdir(os.path.join("boot", d))]
                        if not sub:
                            await message.reply("No folders found in boot")
                            return
                        folder_path = os.path.join("boot", sub[0])

                    # ここでファイル名を完全自動解析＆リネーム
                    pattern = normalize_images(folder_path)
                    if not pattern:
                        await message.reply(f"No images in {folder_path}")
                        return

                    # 繰り返し分動画生成
                    for _ in range(repeat if repeat != 0 else 1):
                        part_index += 1
                        output = f"part{part_index}.mp4"

                        cmd = [
                            FFMPEG_PATH, "-y",
                            "-framerate", str(fps),
                            "-i", pattern,
                            "-vf", f"scale={width}:{height}",
                            output
                        ]
                        print("Running:", " ".join(cmd))

                        result = subprocess.run(cmd)
                        if result.returncode != 0:
                            await message.reply(f"FFmpeg error in {output}")
                            return

                        inputs.append(output)

            # 結合
            with open("list.txt", "w") as f:
                for mp4 in inputs:
                    f.write(f"file '{mp4}'\n")

            concat_cmd = [
                FFMPEG_PATH, "-y",
                "-f", "concat", "-safe", "0",
                "-i", "list.txt",
                "-c", "copy", "output.mp4"
            ]

            subprocess.run(concat_cmd)

            if not os.path.exists("output.mp4"):
                await message.reply("Video generation failed")
                return

            await message.reply("Done ✅")
            await message.reply(file=discord.File("output.mp4"))


# ---------------------------
# keep-alive (Koyeb 用)
# ---------------------------
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
