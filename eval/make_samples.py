"""実録音から品質チューニング用の短尺サンプルを切り出す。

イテレーションは常にこのスクリプトが生成する3クリップ(各約3分)で回す。
フルファイル(数十分)でイテレーションすると改善サイクルが止まるため。

使い方:
    python eval/make_samples.py [--source <音声フォルダ>]

出力:
    eval/samples/clip_intro.mp3  — 講話冒頭(明瞭な発話)
    eval/samples/clip_mid.mp3    — 中間(通常の発話)
    eval/samples/clip_noisy.mp3  — 拍手・歌・無音などを含む区間(幻覚が出やすい)

切り出し位置はファイルごとに決め打ちではなく、ffprobeで長さを取得し
相対位置(先頭/中央/末尾寄り)から算出する。対象は既定で
"G:\\マイドライブ\\jw.org\\集会・大会\\地区大会\\2026\\大会プログラム\\１日目\\rec"
の最初のMP3ファイル(260710_0915.mp3、約49分)を使う。
"""

import argparse
import subprocess
import sys
from pathlib import Path

DEFAULT_SOURCE_DIR = (
    r"G:\マイドライブ\jw.org\集会・大会\地区大会\2026\大会プログラム\１日目\rec"
)
CLIP_SECONDS = 180  # 3分

# (出力ファイル名, 開始位置の割合[0.0-1.0])
CLIPS = [
    ("clip_intro.mp3", 0.02),   # 冒頭付近(挨拶が終わり本題に入る手前)
    ("clip_mid.mp3", 0.45),     # 中間(通常の発話が続く区間)
    ("clip_noisy.mp3", 0.90),   # 終盤寄り(拍手・締めの言葉などが混ざりやすい)
]


def probe_duration(path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        capture_output=True, text=True, check=True,
    )
    return float(result.stdout.strip())


def extract_clip(source: Path, start: float, duration: float, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg", "-y", "-loglevel", "error",
            "-ss", str(start), "-t", str(duration),
            "-i", str(source),
            "-acodec", "copy",
            str(dest),
        ],
        check=True,
    )


def find_source_file(source_dir: Path) -> Path:
    candidates = sorted(source_dir.glob("*.mp3"))
    if not candidates:
        raise FileNotFoundError(f"MP3ファイルが見つかりません: {source_dir}")
    return candidates[0]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=str, default=DEFAULT_SOURCE_DIR)
    args = parser.parse_args()

    source_dir = Path(args.source)
    if not source_dir.is_dir():
        print(f"エラー: フォルダが見つかりません: {source_dir}", file=sys.stderr)
        return 1

    source_file = find_source_file(source_dir)
    duration = probe_duration(source_file)
    print(f"ソース: {source_file.name} ({duration:.0f}秒)")

    out_dir = Path(__file__).parent / "samples"
    for name, ratio in CLIPS:
        start = max(0.0, min(duration - CLIP_SECONDS, duration * ratio))
        dest = out_dir / name
        extract_clip(source_file, start, CLIP_SECONDS, dest)
        print(f"  生成: {dest.name} (開始 {start:.0f}秒, {CLIP_SECONDS}秒間)")

    print(f"完了: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
