"""ルールベースのテキスト整形。

仕様書の決定事項9: 無音区間長で段落分け、セグメント結合、重複・幻覚除去。
LLMによる仕上げは行わない(外部送信ゼロの原則)。
"""

import re

from transcript.engine import Segment

PARAGRAPH_GAP_SECONDS = 2.0


def format_paragraphs(segments: list[Segment], gap_seconds: float = PARAGRAPH_GAP_SECONDS) -> str:
    """セグメント間の無音ギャップが gap_seconds を超えたら段落を分ける。"""
    if not segments:
        return ""

    paragraphs: list[list[str]] = [[segments[0].text]]
    for prev, curr in zip(segments, segments[1:]):
        gap = curr.start - prev.end
        if gap > gap_seconds:
            paragraphs.append([])
        paragraphs[-1].append(curr.text)

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
