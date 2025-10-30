FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# ffmpeg インストール
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# bot.py をコピー
COPY bot.py .

# 起動コマンド
CMD ["python", "bot.py"]
