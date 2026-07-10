# PROGRESS

仕様書: `C:/Users/prove/.claude/plans/transcript-tool.md`

## 現在のフェーズ

**Phase 0: ハーネス構築 — 完了 / Phase 1着手待ち**

## フェーズ状態

| Phase | 状態 | 備考 |
|---|---|---|
| 0 | 完了 | CLAUDE.md / .gitignore / PROGRESS.md / settings.json / commands(smoke,eval,acceptance) / eval/make_samples.py / eval/metrics.py 作成・commit済み(5ee8de0)。3分サンプル3クリップ(clip_intro/mid/noisy)生成済み(eval/samples/、git管理外) |
| 1 | 未着手 | 技術調査(faster-whisper vs whisper.cpp Vulkan) |
| 2 | 未着手 | パイプライン骨格 |
| 3 | 未着手 | 品質チューニング |
| 4 | 未着手 | 運用機能 |
| 5 | 未着手 | 受け入れ検証 |

## 次アクション

1. Phase 1: サブエージェント並列調査(faster-whisper+kotoba-whisper系 / whisper.cpp Vulkan系 / 新技術有無)を時間制限付きで実施
2. エンジン確定後、golden set 生成(large-v3で eval/samples/ の3クリップを文字起こしし eval/golden/*.txt として保存)

## ブロッカー・懸念事項

なし(2026-07-10 時点)

## 環境確認済み事項

- ffmpeg 8.1 (full_build, --enable-whisper 含む多数のcodec対応)
- uv 0.11.7
- Python 3.12 / 3.13 両方インストール済み(`py -0`で確認)
- GPU: Intel Arc 140V、CUDAなし
