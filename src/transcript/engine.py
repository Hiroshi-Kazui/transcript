"""faster-whisper + kotoba-whisper による文字起こしエンジン。

Phase 1 のPoCで確定したパラメータをここに集約する:
- kotoba-tech/kotoba-whisper-v2.0-faster を int8/CPU で実行
- 内蔵 vad_filter で無音・非発話区間をスキップ
- 幻覚(繰り返し)対策の既定パラメータ
"""

from dataclasses import dataclass, field

from faster_whisper import WhisperModel

MODEL_ID = "kotoba-tech/kotoba-whisper-v2.0-faster"


@dataclass
class Segment:
    start: float
    end: float
    text: str
    avg_logprob: float


@dataclass
class TranscriptionResult:
    segments: list[Segment] = field(default_factory=list)
    language: str = "ja"
    duration: float = 0.0
    discarded_count: int = 0  # avg_logprob閾値・空テキストで破棄したセグメント数(監査用)


_model_cache: dict[str, WhisperModel] = {}


def load_model(model_id: str = MODEL_ID) -> WhisperModel:
    if model_id not in _model_cache:
        _model_cache[model_id] = WhisperModel(model_id, device="cpu", compute_type="int8")
    return _model_cache[model_id]


def transcribe_file(audio_path: str, model_id: str = MODEL_ID) -> TranscriptionResult:
    model = load_model(model_id)

    raw_segments, info = model.transcribe(
        audio_path,
        language="ja",
        vad_filter=True,
        condition_on_previous_text=False,
        compression_ratio_threshold=2.4,
        no_speech_threshold=0.6,
    )

    segments: list[Segment] = []
    discarded_count = 0
    for seg in raw_segments:
        # avg_logprob が極端に低い(モデルが自信のない)セグメントは破棄する。
        # Phase 1 PoC で確認した幻覚対策の定石の一つ。破棄件数は監査用に記録する。
        if seg.avg_logprob < -1.0:
            discarded_count += 1
            continue
        text = seg.text.strip()
        if not text:
            discarded_count += 1
            continue
        segments.append(Segment(start=seg.start, end=seg.end, text=text, avg_logprob=seg.avg_logprob))

    return TranscriptionResult(
        segments=segments, language=info.language, duration=info.duration, discarded_count=discarded_count
    )
