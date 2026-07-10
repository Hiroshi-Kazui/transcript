"""文字起こし結果を .txt / .srt / .json の3形式で書き出す。

仕様書の決定事項2(3形式同時出力)・決定事項10(出力先)に対応。
"""

import json
from pathlib import Path

from transcript.engine import Segment, TranscriptionResult
from transcript.formatting import format_paragraphs


def _format_srt_timestamp(seconds: float) -> str:
    total_ms = round(seconds * 1000)
    hours, rem = divmod(total_ms, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    secs, ms = divmod(rem, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"


def build_srt(segments: list[Segment]) -> str:
    lines = []
    for i, seg in enumerate(segments, start=1):
        lines.append(str(i))
        lines.append(f"{_format_srt_timestamp(seg.start)} --> {_format_srt_timestamp(seg.end)}")
        lines.append(seg.text)
        lines.append("")
    return "\n".join(lines)


def build_json(result: TranscriptionResult, audio_file: str) -> str:
    payload = {
        "audio_file": audio_file,
        "language": result.language,
        "duration": result.duration,
        "segments": [
            {"start": s.start, "end": s.end, "text": s.text, "avg_logprob": s.avg_logprob}
            for s in result.segments
        ],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def write_outputs(result: TranscriptionResult, audio_path: Path, transcripts_dir: Path) -> dict[str, Path]:
    """audio_path のbasenameを継承し、transcripts_dir(直下に.txt/.srt, json/配下に.json)へ書き出す。"""
    transcripts_dir.mkdir(parents=True, exist_ok=True)
    json_dir = transcripts_dir / "json"
    json_dir.mkdir(parents=True, exist_ok=True)

    base = audio_path.stem
    txt_path = transcripts_dir / f"{base}.txt"
    srt_path = transcripts_dir / f"{base}.srt"
    json_path = json_dir / f"{base}.json"

    txt_path.write_text(format_paragraphs(result.segments), encoding="utf-8")
    srt_path.write_text(build_srt(result.segments), encoding="utf-8")
    json_path.write_text(build_json(result, audio_path.name), encoding="utf-8")

    return {"txt": txt_path, "srt": srt_path, "json": json_path}
