"""transcribe <フォルダ> エントリポイント。

仕様書の決定事項7: フォルダを渡すと一括処理。処理済み自動スキップ・中断後の再実行で再開。
"""

import argparse
import sys
import time
from pathlib import Path

from transcript.engine import transcribe_file
from transcript.output import write_outputs

AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".flac"}


def find_audio_files(folder: Path) -> list[Path]:
    return sorted(p for p in folder.iterdir() if p.suffix.lower() in AUDIO_EXTENSIONS)


def is_already_processed(audio_path: Path, transcripts_dir: Path) -> bool:
    base = audio_path.stem
    txt_path = transcripts_dir / f"{base}.txt"
    srt_path = transcripts_dir / f"{base}.srt"
    json_path = transcripts_dir / "json" / f"{base}.json"
    return txt_path.exists() and srt_path.exists() and json_path.exists()


def process_folder(folder: Path) -> None:
    audio_files = find_audio_files(folder)
    if not audio_files:
        print(f"音声ファイルが見つかりません: {folder}")
        return

    transcripts_dir = folder / "transcripts"

    for audio_path in audio_files:
        if is_already_processed(audio_path, transcripts_dir):
            print(f"スキップ(処理済み): {audio_path.name}")
            continue

        print(f"処理中: {audio_path.name}")
        t0 = time.time()
        result = transcribe_file(str(audio_path))
        outputs = write_outputs(result, audio_path, transcripts_dir)
        elapsed = time.time() - t0
        print(f"  完了 ({elapsed:.1f}秒): {outputs['txt'].name}, {outputs['srt'].name}, {outputs['json'].relative_to(transcripts_dir)}")


def main() -> int:
    parser = argparse.ArgumentParser(description="日本語講話録音の一括文字起こし")
    parser.add_argument("folder", type=str, help="音声ファイルが入っているフォルダ")
    args = parser.parse_args()

    folder = Path(args.folder)
    if not folder.is_dir():
        print(f"エラー: フォルダが見つかりません: {folder}", file=sys.stderr)
        return 1

    process_folder(folder)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
