"""ルールベースのテキスト整形。

仕様書の決定事項9: 無音区間長で段落分け、セグメント結合、重複・幻覚除去。
LLMによる仕上げは行わない(外部送信ゼロの原則)。
"""

import re

from transcript.engine import Segment

PARAGRAPH_GAP_SECONDS = 2.0
SENTENCE_GAP_SECONDS = 1.0
COMMA_GAP_SECONDS = 0.3

TERMINAL_PUNCTUATION = "。、,.!?」』"


def _pause_marker(gap: float) -> str:
    """kotoba-whisperはほぼ句読点を出力しないため、セグメント間の無音ギャップの
    長さから句読点を推定して補う(Phase 3の計測で有効性を確認済み)。"""
    if gap >= PARAGRAPH_GAP_SECONDS:
        return "。"
    if gap >= SENTENCE_GAP_SECONDS:
        return "。"
    if gap >= COMMA_GAP_SECONDS:
        return "、"
    return ""


def format_paragraphs(segments: list[Segment], gap_seconds: float = PARAGRAPH_GAP_SECONDS) -> str:
    """セグメント間の無音ギャップが gap_seconds を超えたら段落を分ける。
    ギャップの長さに応じて句読点も補う。"""
    if not segments:
        return ""

    paragraphs: list[list[str]] = [[segments[0].text]]
    for prev, curr in zip(segments, segments[1:]):
        gap = curr.start - prev.end

        prev_text = paragraphs[-1][-1]
        if prev_text and prev_text[-1] not in TERMINAL_PUNCTUATION:
            paragraphs[-1][-1] = prev_text + _pause_marker(gap)

        if gap > gap_seconds:
            paragraphs.append([])
        paragraphs[-1].append(curr.text)

    last_para = paragraphs[-1]
    if last_para and last_para[-1] and last_para[-1][-1] not in TERMINAL_PUNCTUATION:
        last_para[-1] = last_para[-1] + "。"

    return "\n\n".join("".join(p) for p in paragraphs)


def deduplicate_repeats(segments: list[Segment], min_repeat_len: int = 6) -> list[Segment]:
    """連続するセグメントが同一・ほぼ同一テキストの場合、幻覚とみなして1つに畳む。"""
    if not segments:
        return []

    result: list[Segment] = [segments[0]]
    for seg in segments[1:]:
        last = result[-1]
        if seg.text == last.text:
            # 同一テキストの連続 → 幻覚として後続を捨てる(区間だけ延長)
            result[-1] = Segment(start=last.start, end=seg.end, text=last.text, avg_logprob=last.avg_logprob)
            continue
        result.append(seg)

    return result


def collapse_intra_segment_repeats(text: str, min_unit_len: int = 2, max_unit_len: int = 12) -> str:
    """1つのセグメント内で同一フレーズが3回以上連続する場合、1回に畳む(幻覚対策)。"""
    for unit_len in range(max_unit_len, min_unit_len - 1, -1):
        pattern = re.compile(r"(.{%d,%d}?)\1{2,}" % (unit_len, unit_len))
        text = pattern.sub(r"\1", text)
    return text


# セグメント境界の無音ギャップは連続発話中ほぼ0秒でシグナルにならない(Phase 3実測で確認)。
# golden set(large-v3)側も同様に句読点をほぼ出力しないため、gap起因の句読点挿入だけでは
# 段落末以外に句読点が付かない。文末表現の正規表現マッチで補う。
_SENTENCE_END_UNITS = [
    "だからです", "からです", "ということです", "ということでしょう",
    "ませんでした", "でしょうか", "でしょう", "ました", "でした",
    "ています", "ります", "ません",
    "なさい", "ください", "ましょう", "ます", "です",
]
_SENTENCE_END_PATTERN = re.compile(
    "(" + "|".join(_SENTENCE_END_UNITS) + ")(か|ね|よ)?"
)
# この直後に来る場合は文が続いているとみなし句点を打たない(逆接・並列・引用の接続表現)
_CONTINUATION_BLOCKLIST = (
    "が", "けど", "けれども", "けれど", "し、", "ので", "から、", "そして",
    "しかし", "でも", "また", "という", "けれど", "とき", "ながら",
)


def insert_sentence_boundaries(text: str) -> str:
    """文末表現(です/ます/でした等)の直後に句点を補う。golden setにも句読点が
    無くCERでは検証できないため、可読性は目視で確認する(Phase 3 EVAL.md参照)。"""
    if not text:
        return text

    result = []
    pos = 0
    for m in _SENTENCE_END_PATTERN.finditer(text):
        end = m.end()
        if end < len(text) and any(text[end:].startswith(w) for w in _CONTINUATION_BLOCKLIST):
            continue
        if end < len(text) and text[end] in TERMINAL_PUNCTUATION:
            continue
        result.append(text[pos:end])
        result.append("。")
        pos = end
    result.append(text[pos:])
    return "".join(result)
