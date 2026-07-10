# /smoke

3分サンプル(`eval/samples/`)でパイプラインを一気通貫実行し、動作確認と簡易メトリクスを表示する。
チューニングイテレーションの最速ループとして使う。フルファイルでは実行しない。

## 手順

1. `eval/samples/` に3クリップ(clip_intro / clip_mid / clip_noisy)が存在するか確認。無ければ `python eval/make_samples.py` を実行するよう案内して停止
2. 現在のパイプライン設定で3クリップを処理し、`.txt`/`.srt`/`.json` を一時出力先(`eval/_smoke_out/`)に生成
3. 各クリップについて処理時間・出力文字数・検出セグメント数を表示
4. golden set が存在すれば `python eval/metrics.py --smoke` を呼び、CER・繰り返し率を併記
5. `eval/_smoke_out/` はgit管理外(.gitignoreの `transcripts/` パターンに準拠する場所に置く、または明示的に追加)
