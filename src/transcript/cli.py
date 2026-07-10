"""transcribe <フォルダ> エントリポイント。

仕様書の決定事項7: フォルダを渡すと一括処理。処理済み自動スキップ・中断後の再実行で再開。
"""

import argparse
import sys
import time
from collections import Counter
from pathlib import Path

from transcript.engine import transcribe_file
from transcript.output import write_outputs

AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".flac"}


def find_audio_files(folder: Path) -> list[Path]:
    return sorted(
        p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in AUDIO_EXTENSIONS
    )


def find_stem_collisions(audio_files: list[Path]) -> dict[str, list[Path]]:
    """出力ファイル名は拡張子を除いたstemで決まるため、同名・別拡張子のファイル
    (例: meeting.mp3 と meeting.wav)があると出力が衝突しサイレントにスキップされる。
    事前に検出して呼び出し側で明示的にエラーにする。"""
    by_stem = Counter(p.stem for p in audio_files)
    colliding_stems = {stem for stem, count in by_stem.items() if count > 1}
    if not colliding_stems:
        return {}
    return {
        stem: [p for p in audio_files if p.stem == stem]
        for stem in colliding_stems
    }


def is_already_processed(audio_path: Path, transcripts_dir: Path) -> bool:
    base = audio_path.stem
    txt_path = transcripts_dir / f"{base}.txt"
    srt_path = transcripts_dir / f"{base}.srt"
    json_path = transcripts_dir / "json" / f"{base}.json"
    return txt_path.exists() and srt_path.exists() and json_path.exists()


def process_folder(folder: Path) -> int:
    """処理対象フォルダ内の音声を一括処理する。戻り値は失敗件数(0なら全件成功)。

    1ファイルの失敗が全体を止めないよう、ファイル単位でエラーを捕捉して続行する。
    エラーは握りつぶさず、都度表示した上で最後にまとめて再掲する。
    """
    audio_files = find_audio_files(folder)
    if not audio_files:
        print(f"音声ファイルが見つかりません: {folder}")
        return 0

    collisions = find_stem_collisions(audio_files)
    if collisions:
        print("エラー: 同名(拡張子違い)のファイルが見つかりました。出力ファイル名が衝突するため処理を中止します:", file=sys.stderr)
        for stem, paths in collisions.items():
            names = ", ".join(p.name for p in paths)
            print(f"  - {stem}: {names}", file=sys.stderr)
        print("どちらか一方をリネームまたは移動してから再実行してください。", file=sys.stderr)
        return len(collisions)

    transcripts_dir = folder / "transcripts"
    total = len(audio_files)
    failures: list[tuple[Path, str]] = []

    for i, audio_path in enumerate(audio_files, start=1):
        progress = f"[{i}/{total}]"
        if is_already_processed(audio_path, transcripts_dir):
            print(f"{progress} スキップ(処理済み): {audio_path.name}")
            continue

        print(f"{progress} 処理中: {audio_path.name}")
        t0 = time.time()
        try:
            result = transcribe_file(str(audio_path))
            outputs = write_outputs(result, audio_path, transcripts_dir)
        except Exception as e:
            print(f"  エラー: {audio_path.name}: {type(e).__name__}: {e}", file=sys.stderr)
            failures.append((audio_path, f"{type(e).__name__}: {e}"))
            continue
        elapsed = time.time() - t0
        print(f"  完了 ({elapsed:.1f}秒): {outputs['txt'].name}, {outputs['srt'].name}, {outputs['json'].relative_to(transcripts_dir)}")

    if failures:
        print(f"\n{len(failures)}件のファイルで処理に失敗しました:", file=sys.stderr)
        for path, err in failures:
            print(f"  - {path.name}: {err}", file=sys.stderr)

    return len(failures)


def main() -> int:
    parser = argparse.ArgumentParser(description="日本語講話録音の一括文字起こし")
    parser.add_argument("folder", type=str, help="音声ファイルが入っているフォルダ")
    args = parser.parse_args()

    folder = Path(args.folder)
    if not folder.is_dir():
        print(f"エラー: フォルダが見つかりません: {folder}", file=sys.stderr)
        return 1

    failure_count = process_folder(folder)
    return 1 if failure_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
