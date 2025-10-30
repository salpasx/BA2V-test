# 公式 Python イメージを使用
FROM python:3.13-slim

# ffmpeg をインストール
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# 作業ディレクトリ
WORKDIR /app

# 必要なライブラリをコピー
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Bot のコードをコピー
COPY bot.py .

# 起動
CMD ["python", "bot.py"]
