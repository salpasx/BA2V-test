FROM python:3.12-slim

# ffmpeg インストール
RUN apt update && apt install -y ffmpeg

# 作業ディレクトリ
WORKDIR /app

# Python ライブラリ
COPY requirements.txt .
RUN pip install -r requirements.txt

# bot ファイルを追加
COPY . .

CMD ["python", "bot.py"]
