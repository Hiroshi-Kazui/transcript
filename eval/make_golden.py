"""eval/samples/ の3クリップを large-v3 (最高精度) で文字起こしし、
eval/golden/*.txt として保存する。以後の /eval でのCER計測の参照基準として使う。

large-v3 はCPUだと低速(RTF目安3前後)なので、3分クリップ×3本の実行に
数分〜十数分かかることを想定する。1回きりのセットアップ作業。
"""

from pathlib import Path

from faster_whisper import WhisperModel

SAMPLES_DIR = Path(__file__).parent / "samples"
GOLDEN_DIR = Path(__file__).parent / "golden"

print("Loading large-v3 (int8, CPU)... これは数分かかる場合があります")
model = WhisperModel("large-v3", device="cpu", compute_type="int8")

GOLDEN_DIR.mkdir(parents=True, exist_ok=True)

for clip_path in sorted(SAMPLES_DIR.glob("*.mp3")):
    print(f"文字起こし中: {clip_path.name}")
    segments, info = model.transcribe(
        str(clip_path),
        language="ja",
        vad_filter=True,
        condition_on_previous_text=False,
    )
    text = "".join(seg.text for seg in segments).strip()
    out_path = GOLDEN_DIR / f"{clip_path.stem}.txt"
    out_path.write_text(text, encoding="utf-8")
    print(f"  保存: {out_path.name} ({len(text)}文字)")

print("golden set 生成完了")
