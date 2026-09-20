#!/usr/bin/env bash
# ローカルPC上で pCloud の音声を文字起こし→要約し、結果を pCloud に書き戻す。
# GitHub Actions の transcribe.yml と同じ対象フォルダ・同じ出力先を使うローカル版。
#
# 使い方: bash scripts/run-local.sh [pCloud上のフォルダ]
#   フォルダ未指定時は既定値 "My Records" を使う(環境変数 PCLOUD_FOLDER で上書き可)。
#
# 先行実行中は何もせず終了する(ロックディレクトリで排他)。
# 音声のステージング先とログは %LOCALAPPDATA%\transcript 配下。リポジトリには置かない。
set -u

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
folder="${1:-${PCLOUD_FOLDER:-My Records}}"

work_root="${LOCALAPPDATA:-$HOME/AppData/Local}"
work_root="${work_root//\\//}/transcript"
audio_dir="$work_root/audio"
log_dir="$work_root/logs"
lock_dir="$work_root/run.lock"

mkdir -p "$audio_dir" "$log_dir"

# --- 排他制御: ロックを取れなければ今回はスルー ---
if ! mkdir "$lock_dir" 2>/dev/null; then
    stale=0
    if [ -f "$lock_dir/pid" ]; then
        old_pid="$(cat "$lock_dir/pid" 2>/dev/null || true)"
        if [ -n "${old_pid:-}" ] && ! kill -0 "$old_pid" 2>/dev/null; then
            stale=1
        fi
    else
        stale=1
    fi
    if [ "$stale" -eq 1 ]; then
        # 前回の実行が異常終了してロックだけ残っている場合は引き継ぐ
        echo "残骸ロックを破棄して続行します"
        rm -f "$lock_dir/pid"
        rmdir "$lock_dir" 2>/dev/null
        mkdir "$lock_dir" 2>/dev/null || { echo "ロック取得失敗。スキップします"; exit 0; }
    else
        echo "先行実行中($(cat "$lock_dir/pid" 2>/dev/null))のためスキップします"
        exit 0
    fi
fi
echo $$ > "$lock_dir/pid"
cleanup() {
    rm -f "$lock_dir/pid"
    rmdir "$lock_dir" 2>/dev/null
}
trap cleanup EXIT

log_file="$log_dir/$(date +%Y%m%d).log"
exec >> "$log_file" 2>&1
echo "================ $(date '+%Y-%m-%d %H:%M:%S') 開始 (folder=$folder) ================"

cd "$repo_dir"
export PATH="$PATH:$HOME/.local/bin"

fail=0

# --- pCloud から音声取得(transcripts/ も含めて取得し、処理済み判定をCLIに任せる) ---
if ! rclone copy "pcloud:${folder}" "$audio_dir"; then
    echo "pCloud からの取得に失敗しました" >&2
    exit 1
fi

# --- 文字起こし(直下と日付サブフォルダを順に処理) ---
shopt -s nullglob
found=0
for d in "$audio_dir" "$audio_dir"/*/; do
    d="${d%/}"
    files=("$d"/*.mp3 "$d"/*.wav "$d"/*.m4a "$d"/*.flac)
    [ ${#files[@]} -gt 0 ] || continue
    found=1
    echo "=== 文字起こし: $d ==="
    uv run transcribe "$d" || fail=1
done
if [ $found -eq 0 ]; then
    echo "音声ファイルが見つかりません — 処理対象なしとして終了"
    echo "================ $(date '+%Y-%m-%d %H:%M:%S') 終了(対象なし) ================"
    exit 0
fi

# --- 日次要約 ---
bash scripts/summarize.sh "$audio_dir" || fail=1

# --- 週次振り返り(月曜JSTのみ。FORCE_WEEKLY=true で強制) ---
if [ "${FORCE_WEEKLY:-false}" = "true" ] || [ "$(TZ=Asia/Tokyo date +%u)" = "1" ]; then
    bash scripts/weekly.sh "$audio_dir" || fail=1
else
    echo "月曜(JST)ではないため週次振り返りをスキップ"
fi

# --- pCloud へ書き戻し(Actions と同じ出力先) ---
if ! rclone copy "$audio_dir" "pcloud:${folder}" \
    --include "transcripts/**" --include "summary.md" --include "/weekly/**"; then
    echo "pCloud への書き戻しに失敗しました" >&2
    fail=1
fi

echo "================ $(date '+%Y-%m-%d %H:%M:%S') 終了(fail=$fail) ================"
exit $fail
