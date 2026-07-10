# PROGRESS

仕様書: `C:/Users/prove/.claude/plans/transcript-tool.md`

## 現在のフェーズ

**Phase 4: 運用機能実装 — 完了 / Phase 5着手待ち**

## フェーズ状態

| Phase | 状態 | 備考 |
|---|---|---|
| 0 | 完了 | CLAUDE.md / .gitignore / PROGRESS.md / settings.json / commands(smoke,eval,acceptance) / eval/make_samples.py / eval/metrics.py 作成・commit済み(5ee8de0)。3分サンプル3クリップ(clip_intro/mid/noisy)生成済み(eval/samples/、git管理外) |
| 1 | 完了 | エンジン確定(下記)。PoC実測込み |
| 2 | 完了 | パイプライン骨格実装済み(下記)。clip_mid.mp3でend-to-end動作確認済み |
| 3 | 完了 | golden set生成・句読点補完チューニング完了(下記、詳細は eval/EVAL.md) |
| 4 | 完了 | 運用機能実装・python-reviewerレビュー対応完了(下記) |
| 5 | 未着手 | 受け入れ検証 |

## Phase 4 実施内容

- `cli.py`: 進捗表示`[i/total]`追加、1ファイル失敗が全体を止めないtry/except(エラーは
  握り潰さず表示+最後に再掲)、`find_stem_collisions()`で同名・別拡張子ファイル
  (例: meeting.mp3とmeeting.wav)の出力衝突を事前検出し明示的エラーで停止
- `transcribe.bat`: ドラッグ&ドロップ起動用ランチャー(日本語文字列はcmd.exeの
  コードページ問題で文字化けしたため英語表記に変更)
- `README.md`: セットアップ・使い方・出力形式・制約を記載

### python-reviewerレビュー対応(2026-07-10)
- [HIGH→対応済み] 同名・別拡張子ファイルの衝突でサイレントスキップされる問題
  → `find_stem_collisions()`で事前検出しエラー停止に変更
- [HIGH→対応済み] `deduplicate_repeats`/`collapse_intra_segment_repeats`が実装済みなのに
  パイプラインから未呼び出しだった問題 → `formatting.clean_segments()`を追加し
  `output.write_outputs()`から.txt/.srt/.json全てに適用するよう配線
- [MEDIUM→対応済み] `_pause_marker`の冗長分岐を整理、`deduplicate_repeats`の未使用引数を削除
- [LOW→対応済み] `_CONTINUATION_BLOCKLIST`の重複エントリ削除、エラーメッセージに例外型を追加、
  `find_audio_files`に`is_file()`チェック追加
- 回帰テスト: clip_mid.mp3で再テストし正常動作を確認。同名別拡張子ファイルでの
  衝突検出も動作確認済み(サイレントスキップではなく明示エラーで停止)

## Phase 3 実施内容

1. `eval/make_samples.py` のclip_intro位置を修正(59秒地点→736秒地点)。Phase 1 PoCで発覚した
   「開幕の歌・アナウンス等の非発話区間を捉えていた」問題への対処。複数地点プローブの結果、
   館内アナウンス区間(短い発話が点在)を新たなclip_introとして採用
2. `eval/make_golden.py` を新規作成し、large-v3でgolden set生成(`eval/golden/*.txt`)
3. `/smoke`→`/eval`ループで句読点補完ロジックを3段階チューニング(詳細はeval/EVAL.md参照):
   - ギャップ長ベースの句読点(段落末のみ有効、セグメント間ギャップの99%が0秒と判明)
   - 文末表現(です/ます/でした等)の正規表現検出を追加 → 可読性が大幅改善
   - 否定形(ません/ませんでした)パターン追加で残存の未分割を解消
4. golden set(large-v3)自体も句読点をほぼ出力しないため、句読点関連の変更はCERでの
   正誤判定ができないと判明。CERの大幅悪化がないことを自動計測の合格基準とし、
   可読性は目視で確認(CLAUDE.mdの「計測のみで判断」原則の例外としてEVAL.mdに明記)
5. `src/transcript/formatting.py`: `insert_sentence_boundaries()` 追加、`output.py`から呼び出し

## Phase 2 実装内容

- `pyproject.toml`: Python 3.12固定、faster-whisper依存、`transcribe`エントリポイント
- `src/transcript/engine.py`: kotoba-whisper-v2.0-faster(int8/CPU)のロード・文字起こし。Phase 1確定パラメータ(vad_filter, condition_on_previous_text=False, compression_ratio_threshold=2.4, no_speech_threshold=0.6, avg_logprob<-1.0破棄)を実装
- `src/transcript/formatting.py`: 無音ギャップ2秒で段落分け、連続セグメントの重複畳み込み、セグメント内反復の正規表現除去(幻覚対策の補助)
- `src/transcript/output.py`: `.txt`(段落テキスト)/`.srt`(標準字幕形式)/`.json`(構造化、segments配列にstart/end/text/avg_logprob)を生成
- `src/transcript/cli.py`: `transcribe <フォルダ>` エントリポイント。フォルダ内音声を走査し、`transcripts/`配下の3ファイル全存在チェックでスキップ判定

## Phase 2 動作確認結果

`eval/_smoke_out/`(一時テストフォルダ、cleanup済み)に`eval/samples/clip_mid.mp3`をコピーしてCLI実行:
- 初回実行: 59.7秒で処理完了、`.txt`/`.srt`/`json/.json`の3ファイルとも正しい内容・構造で生成確認
- 再実行: 「スキップ(処理済み)」が即座に表示され、モデル再ロードなしでスキップ動作を確認
- 出力内容は品質面でも自然な日本語(Phase 1 PoCの結果と一致)

## Phase 1 決定事項: エンジン確定

**採用: faster-whisper (CPU) + kotoba-whisper-v2.0-faster のみ。whisper.cpp(Vulkan)は不採用。**

### 確定した実装パラメータ
- モデルID: `kotoba-tech/kotoba-whisper-v2.0-faster`(HuggingFace公式CTranslate2変換版、自前変換不要)
- `compute_type="int8"`, `device="cpu"`
- VADは faster-whisper **内蔵**の `vad_filter=True` を使う。外部silero-vadの別導入は不要(仕様書のVAD前処理はこれで満たせる)
- 幻覚対策の既定値: `condition_on_previous_text=False` / `compression_ratio_threshold=2.4`(既定) / `no_speech_threshold=0.6`(既定) / `avg_logprob < -1.0` のセグメントは破棄
- **Python 3.12固定**(3.13ではWindows向けCTranslate2のwheelが無く `pip install` が失敗する。uv venvを `--python 3.12` で明示作成する)

### whisper.cpp(Vulkan)を不採用とした根拠(PoC実測、2026-07-10)
実際の発話区間(clip_mid.mp3, 180秒)で公平比較を実施:

| エンジン | 処理時間 | RTF | 品質 |
|---|---|---|---|
| faster-whisper (CPU int8) | 60.7秒 | 0.34 | 良好、文章として自然 |
| whisper.cpp Vulkan (Intel Arc 140V GPU, q5_0量子化) | 25.0秒 | 0.14 | 誤認識が多い(「大会」を「対岩」「タイガル」と誤変換連発、文意が反転する誤りも1箇所) |

速度は whisper.cpp が約2.4倍優位だが、品質はfaster-whisperが明確に優位。ユーザーは精度を優先し、faster-whisperのみ採用を選択(2026-07-10確認済み)。
4時間の実データはfaster-whisper単体で約1.5時間の見込み(60.7s/180s × 14400s ≈ 4860s ≈ 81分)、受け入れ基準(一晩以内)を余裕を持って満たす。

whisper.cppのPoC環境(Vulkan SDK, whisper.cpp build, GGML重み)は `eval/_poc/`(git管理外)に残置。将来速度が課題になった場合の再検証用に保持可能、不要なら削除してよい。

### Phase 1で判明した副次的な問題(Phase 3で対応)
`eval/make_samples.py` の `clip_intro`(録音開始から59秒地点, ratio=0.02)が、実際には開幕の歌・アナウンス等の非発話区間を捉えていたことが判明(VAD有効時は正しく11文字程度に抑制されたが、VAD無効での検証時に激しい幻覚が発生し発覚)。golden set作成時にclip_introの切り出し位置を発話が確実にある区間に調整するか、非発話サンプルとして意図的に残すか、Phase 3で判断する。

## 次アクション

1. Phase 2: パイプライン骨格実装(音声→VAD→文字起こし→整形→.txt/.srt/.json出力)を3分サンプルで動作させる
2. golden set 生成(large-v3で eval/samples/ の3クリップを文字起こしし eval/golden/*.txt として保存)— Phase 2実装後に実施

## ブロッカー・懸念事項

なし(2026-07-10 時点)

## 環境確認済み事項

- ffmpeg 8.1 (full_build, --enable-whisper 含む多数のcodec対応)
- uv 0.11.7
- Python 3.12 / 3.13 両方インストール済み(`py -0`で確認)
- GPU: Intel Arc 140V、CUDAなし
