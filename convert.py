import subprocess
import os
import re

def convert_part(folder, output, fps=30, width=720, height=1600):
    """
    フォルダ内の画像を mp4 に変換する
    folder: 画像フォルダ
    output: 出力動画ファイル名
    fps: フレームレート
    width, height: 出力解像度
    """
    if not os.path.exists(folder):
        print(f"[WARN] Not found {folder} so skip it. ")
        return False

    # 画像ファイルを取得
    files = [f for f in os.listdir(folder) if f.lower().endswith((".png", ".jpg"))]
    if not files:
        print(f"[WARN] Not found {folder} so skip it. ")
        return False

    files.sort()
    digits = len(re.search(r'\d+', files[0]).group(0))
    ext = os.path.splitext(files[0])[1]
    pattern = os.path.join(folder, f"%0{digits}d{ext}")

    cmd = ["ffmpeg", "-y", "-framerate", str(fps), "-i", pattern,
           "-vf", f"scale={width}:{height}", output]

    print(f"[INFO] Converting...")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"[ERROR] FFmpeg error in {output}")
        return False
    print(f"[INFO] {output} Done")
    return True
