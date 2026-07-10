# PROGRESS

仕様書: `C:/Users/prove/.claude/plans/transcript-tool.md`

## 現在のフェーズ

**Phase 0: ハーネス構築 — 実行中**

## フェーズ状態

| Phase | 状態 | 備考 |
|---|---|---|
| 0 | 実行中 | CLAUDE.md / .gitignore / PROGRESS.md / ディレクトリ構造 作成済み。settings.json・コマンド・eval基盤はこれから |
| 1 | 未着手 | 技術調査(faster-whisper vs whisper.cpp Vulkan) |
| 2 | 未着手 | パイプライン骨格 |
| 3 | 未着手 | 品質チューニング |
| 4 | 未着手 | 運用機能 |
| 5 | 未着手 | 受け入れ検証 |

## 次アクション

1. `.claude/settings.json` で uv/ffmpeg/python 系コマンドを許可リスト化
2. `.claude/commands/{smoke,eval,acceptance}.md` を作成
3. `eval/make_samples.py`: 実録音(`G:\...\rec\260710_0915.mp3`)から3分クリップ3種を切り出し
4. golden set 生成(large-v3で3クリップを文字起こしし参照テキストとする)— Phase 1でエンジンが入ってから実施

## ブロッカー・懸念事項

なし(2026-07-10 時点)

## 環境確認済み事項

- ffmpeg 8.1 (full_build, --enable-whisper 含む多数のcodec対応)
- uv 0.11.7
- Python 3.12 / 3.13 両方インストール済み(`py -0`で確認)
- GPU: Intel Arc 140V、CUDAなし
