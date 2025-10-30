# ベースイメージ
FROM python:3.13-slim

# ffmpeg をインストール
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# 作業ディレクトリ
WORKDIR /app

# ファイルをコピー
COPY requirements.txt .
COPY bot.py .

# 依存ライブラリインストール
RUN pip install --no-cache-dir -r requirements.txt

# 環境変数からトークンを取得する
ENV DISCORD_TOKEN=""

# コンテナ起動時に bot.py を実行
CMD ["python", "bot.py"]
