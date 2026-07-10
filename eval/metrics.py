"""品質チューニングの計測ロジック。

golden set(参照文字起こし)と実際の出力を比較し、以下を算出する:
  - CER (Character Error Rate): golden との文字誤り率
  - 繰り返し率: n-gram の異常な反復(幻覚検出の proxy)
  - VADカバレッジ: 発話区間のうちテキスト化できた割合(取りこぼし検出)
  - 句読点密度: 100文字あたりの句読点数(整形品質の proxy)

「読んだ感じ良くなった」ではなくこの数値で採用可否を判断する(CLAUDE.md鉄則)。

使い方:
    python eval/metrics.py                 # eval/golden/ 全体と eval/_smoke_out/ を比較
    python eval/metrics.py --smoke          # /smoke からの簡易呼び出し(同上、フォーマットのみ簡略)
"""

import argparse
import re
from pathlib import Path

EVAL_DIR = Path(__file__).parent
GOLDEN_DIR = EVAL_DIR / "golden"
SMOKE_OUT_DIR = EVAL_DIR / "_smoke_out"

PUNCTUATION = "。、,.!?"


def levenshtein(a: str, b: str) -> int:
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i] + [0] * len(b)
        for j, cb in enumerate(b, 1):
            cost = 0 if ca == cb else 1
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost)
        prev = cur
    return prev[-1]


def cer(reference: str, hypothesis: str) -> float:
    reference = reference.strip()
    hypothesis = hypothesis.strip()
    if not reference:
        return 0.0 if not hypothesis else 1.0
    return levenshtein(reference, hypothesis) / len(reference)


def repetition_rate(text: str, n: int = 8) -> float:
    """n文字のngramのうち、直後に同一ngramが連続する箇所の割合(幻覚の典型パターン)。"""
    if len(text) < n * 2:
        return 0.0
    grams = [text[i:i + n] for i in range(len(text) - n)]
    repeats = sum(1 for i in range(len(grams) - 1) if grams[i] == grams[i + 1])
    return repeats / len(grams) if grams else 0.0


def punctuation_density(text: str) -> float:
    if not text:
        return 0.0
    count = sum(1 for ch in text if ch in PUNCTUATION)
    return count / len(text) * 100


def vad_coverage(segments_json: dict) -> float:
    """segments_json は {"vad_speech_seconds": float, "transcribed_seconds": float} を期待。
    無ければ 計測不能として None を返す(呼び出し側で表示をスキップ)。
    """
    speech = segments_json.get("vad_speech_seconds")
    transcribed = segments_json.get("transcribed_seconds")
    if not speech:
        return None
    return min(1.0, transcribed / speech) if transcribed else 0.0


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def evaluate_clip(name: str, hypothesis_dir: Path) -> dict:
    golden_path = GOLDEN_DIR / f"{name}.txt"
    hyp_path = hypothesis_dir / f"{name}.txt"

    golden_text = load_text(golden_path)
    hyp_text = load_text(hyp_path)

    result = {
        "clip": name,
        "golden_exists": golden_path.exists(),
        "hypothesis_exists": hyp_path.exists(),
        "cer": None,
        "repetition_rate": None,
        "punctuation_density": None,
    }
    if golden_path.exists() and hyp_path.exists():
        result["cer"] = round(cer(golden_text, hyp_text), 4)
    if hyp_text:
        result["repetition_rate"] = round(repetition_rate(hyp_text), 4)
        result["punctuation_density"] = round(punctuation_density(hyp_text), 2)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true", help="/smoke からの簡易呼び出し")
    parser.add_argument("--hypothesis-dir", type=str, default=str(SMOKE_OUT_DIR))
    args = parser.parse_args()

    hypothesis_dir = Path(args.hypothesis_dir)
    clip_names = sorted(p.stem for p in GOLDEN_DIR.glob("*.txt"))

    if not clip_names:
        print("golden set が見つかりません(eval/golden/*.txt)。先に golden set を作成してください。")
        return 1

    print(f"{'clip':<14} {'CER':>8} {'繰り返し率':>10} {'句読点密度':>10}")
    for name in clip_names:
        r = evaluate_clip(name, hypothesis_dir)
        cer_str = f"{r['cer']:.4f}" if r["cer"] is not None else "N/A"
        rep_str = f"{r['repetition_rate']:.4f}" if r["repetition_rate"] is not None else "N/A"
        pd_str = f"{r['punctuation_density']:.2f}" if r["punctuation_density"] is not None else "N/A"
        print(f"{name:<14} {cer_str:>8} {rep_str:>10} {pd_str:>10}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
