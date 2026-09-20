# transcript

日本語講話録音の一括文字起こしCLIツール。完全ローカル・完全オフラインで動作します
(音声もテキストも外部送信ゼロ)。

## セットアップ(初回のみ)

前提: [uv](https://docs.astral.sh/uv/) がインストール済みであること。

```powershell
uv venv --python 3.12
uv sync
```

Python 3.12を明示的に使う必要があります。3.13ではCTranslate2(推論エンジン)の
Windows向けwheelが提供されておらず、依存解決に失敗します。

初回の文字起こし実行時、`kotoba-tech/kotoba-whisper-v2.0-faster`モデル(HuggingFace)が
自動ダウンロードされます(以降はキャッシュされ、ネットワーク接続は不要になります)。

## 使い方

### コマンドラインから

```powershell
.venv\Scripts\python.exe -m transcript.cli "<音声フォルダのパス>"
```

または `uv run transcribe "<音声フォルダのパス>"`

### ドラッグ&ドロップから

`transcribe.bat` に音声ファイルの入ったフォルダをドラッグ&ドロップしてください。

## 出力

指定フォルダ内に `transcripts/` サブフォルダが作成され、各音声ファイルごとに:

- `transcripts/<ファイル名>.txt` — 段落分け・句読点補完済みのプレーンテキスト
- `transcripts/<ファイル名>.srt` — タイムスタンプ付き字幕形式
- `transcripts/json/<ファイル名>.json` — セグメント単位の構造化データ(タイムスタンプ・信頼度含む)

が生成されます。対応する3ファイルが既に存在するファイルは自動的にスキップされるため、
処理を中断しても再実行すれば未処理分だけが処理されます。

## このPCでの定期実行(毎時 *:07)

pCloud 上の音声フォルダを取得 → 文字起こし → 日次要約(月曜は週次振り返りも)→ 結果を
pCloud の同じ場所に書き戻す一連の処理を、このPCで毎時 7 分に実行します。処理対象フォルダと
出力先は GitHub Actions の `transcribe` ワークフローと同一です。

```bash
# 手動実行(フォルダ省略時は "My Records")
bash scripts/run-local.sh
```

- Windows タスクスケジューラのタスク名: `transcript-local`(毎時 *:07、PCの電源が入って
  ログオンしている間だけ動作)
- 前の実行がまだ走っている回は何もせずスキップします(スクリプト側のロックと、
  タスク側の「既に実行中なら新しいインスタンスを開始しない」設定の二重化)
- 音声の一時置き場とログ: `%LOCALAPPDATA%\transcript\`(`audio\`、`logs\<日付>.log`)
- 前提: `rclone` に `pcloud` リモートが設定済み、`claude` CLI がログイン済み

タスクの状態確認・停止:

```powershell
Get-ScheduledTask -TaskName transcript-local
Get-ScheduledTaskInfo -TaskName transcript-local   # 次回・前回実行時刻
Disable-ScheduledTask -TaskName transcript-local   # 一時停止
```

## 品質チューニング(開発者向け)

`eval/` 配下に品質計測用のハーネスがあります。詳細は `CLAUDE.md` および
`.claude/commands/{smoke,eval,acceptance}.md` を参照してください。

```powershell
# 3分サンプルクリップの生成(実録音から)
uv run python eval/make_samples.py

# golden set(参照文字起こし)の生成
uv run python eval/make_golden.py

# 品質計測
uv run python eval/metrics.py --hypothesis-dir <文字起こし結果のあるフォルダ>
```

## 制約・既知の限界

- 話者分離(誰が話しているかのラベル付け)は未実装です
- 句読点はルールベースの推定(文末表現の検出)で補っており、完全ではありません
- 処理はCPUのみで行われます(GPU非対応)。4時間程度の音声で1.5〜2時間程度を見込んでください
