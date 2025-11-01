import discord
import zipfile
import subprocess
import os
import shutil
import glob
import re
from flask import Flask
from threading import Thread

TOKEN = os.environ.get("DISCORD_TOKEN")
FFMPEG_PATH = "/usr/bin/ffmpeg"

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)


# ----------------------------------------
# ✅ 画像の桁数を自動判定（0001 / 001 / 01 / 1 でもOK）
# ----------------------------------------
def get_digit_format(image_files):
    digits = []
    for f in image_files:
        num = re.findall(r"(\d+)", os.path.basename(f))
        if num:
            digits.append(len(num[0]))
    return max(digits) if digits else 3   # 数字なし → 3桁にする


# ----------------------------------------
# ✅ 任意のフォルダを MP4 出力する関数
# ----------------------------------------
def create_video_from_folder(folder_path, width, height, fps, index):
    images = sorted(glob.glob(os.path.join(folder_path, "*.jpg")) +
                    sorted(glob.glob(os.path.join(folder_path, "*.png"))))

    if not images:
        return None

    # 桁数を取得
    digits = get_digit_format(images)

    # 拡張子取得
    ext = os.path.splitext(images[0])[1]

    input_pattern = os.path.join(folder_path, f"%0{digits}d{ext}")
    output_name = f"part{index}.mp4"

    cmd = [
        FFMPEG_PATH, "-y",
        "-framerate", str(fps),
        "-i", input_pattern,
        "-vf", f"scale={width}:{height}",
        output_name
    ]

    print("Running:", " ".join(cmd))
    result = subprocess.run(cmd)
    return output_name if result.returncode == 0 else None


# ----------------------------------------
# ✅ Discord Bot
# ----------------------------------------
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

            # zip 保存
            await file.save("bootanimation.zip")

            # 既存フォルダ削除
            if os.path.exists("boot"):
                shutil.rmtree("boot")

            # 解凍
            with zipfile.ZipFile("bootanimation.zip", 'r') as z:
                z.extractall("boot")

            # desc.txt があれば読む
            desc_path = os.path.join("boot", "desc.txt")
            if os.path.exists(desc_path):
                with open(desc_path, "r") as f:
                    lines = f.readlines()
                width, height, fps = lines[0].split()

            else:
                # desc.txt が無い場合 → 画像サイズから直接取る
                folders = [d for d in os.listdir("boot") if os.path.isdir(os.path.join("boot", d))]
                if not folders:
                    await message.reply("Not found folder")
                    return

                first_folder = os.path.join("boot", folders[0])
                first_image = sorted(glob.glob(os.path.join(first_folder, "*")))[0]

                # Pillow を使わないで ffmpeg からサイズ推定
                probe = subprocess.getoutput(f"{FFMPEG_PATH} -hide_banner -i '{first_image}' 2>&1")
                size = re.findall(r"(\d+)x(\d+)", probe)
                if not size:
                    width, height = "480", "960"
                else:
                    width, height = size[0]

                fps = "30"

            # part フォルダを全部探す
            part_folders = sorted([d for d in os.listdir("boot")
                                   if os.path.isdir(os.path.join("boot", d))])

            if not part_folders:
                await message.reply(Not fount photo")
                return

            mp4_list = []
            part_index = 0

            # 各フォルダを動画化
            for folder in part_folders:
                folder_path = os.path.join("boot", folder)
                part_index += 1
                output = create_video_from_folder(folder_path, width, height, fps, part_index)

                if output:
                    mp4_list.append(output)

            if not mp4_list:
                await message.reply("画像の変換に失敗しました")
                return

            # 🔗 MP4 を連結
            with open("list.txt", "w") as f:
                for mp4 in mp4_list:
                    f.write(f"file '{mp4}'\n")

            concat_cmd = [
                FFMPEG_PATH, "-y",
                "-f", "concat", "-safe", "0", "-i", "list.txt",
                "-c", "copy", "output.mp4"
            ]
            print("Running concat:", " ".join(concat_cmd))
            result = subprocess.run(concat_cmd)

            if result.returncode != 0 or not os.path.exists("output.mp4"):
                await message.reply("連結に失敗しました")
                return

            await message.reply("✅ Done!")
            await message.reply(file=discord.File("output.mp4"))


# ----------------------------------------
# ✅ Flask keep-alive
# ----------------------------------------
app = Flask('')

@app.route('/')
def home():
    return "I'm alive"

def run():
    app.run(host='0.0.0.0', port=8000)

def keep_alive():
    t = Thread(target=run)
    t.dadaemon = True
    t.start()

keep_alive()

client.run(TOKEN)
