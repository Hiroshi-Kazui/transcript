#!/usr/bin/env bash
# 前週(月〜日、JST基準)の日次要約をもとに、週次振り返りと次週の目標提案を生成する。
# 使い方: weekly.sh <ルートフォルダ>
# 前提: claude CLI が PATH にあり、CLAUDE_CODE_OAUTH_TOKEN で認証済み(GitHub Actions)
set -u

root="${1:?usage: weekly.sh <folder>}"

# 前週の月曜〜日曜(JST)。月曜3時実行時: 7日前=先週月曜, 1日前=昨日(日曜)
start="$(TZ=Asia/Tokyo date -d "-7 day" +%Y%m%d)"
end="$(TZ=Asia/Tokyo date -d "-1 day" +%Y%m%d)"
out_dir="$root/weekly"
out="$out_dir/週次振り返り_${start}-${end}.md"

if [ -f "$out" ]; then
    echo "スキップ(生成済み): $out"
    exit 0
fi

input="$(mktemp)"
found=0
for i in 7 6 5 4 3 2 1; do
    day="$(TZ=Asia/Tokyo date -d "-$i day" +%Y%m%d)"
    f="$root/$day/summary.md"
    if [ -f "$f" ]; then
        found=1
        {
            echo "===== ${day} の要約 ====="
            cat "$f"
            echo
        } >> "$input"
    fi
done

if [ $found -eq 0 ]; then
    echo "対象期間(${start}〜${end})に日次要約がないため週次振り返りをスキップ"
    rm -f "$input"
    exit 0
fi

read -r -d '' PROMPT <<'PROMPT_EOF' || true
以下は1週間分の集会・大会プログラムの日次要約(日付ごとに「===== YYYYMMDD の要約 =====」で区切り)。
元は自動音声認識の文字起こしのため誤字・誤変換が残っている可能性がある。文脈から本来の語
(聖書関連の用語・書名・固有名詞を含む)を推定して補完し、誤りをそのまま引用しないこと。

次の構成のMarkdownドキュメントを日本語で作成せよ:
# 週次振り返り(<期間>)
## 今週学んだ主な点 — 週全体を貫くテーマと要点の整理
## 振り返り — 特に心に留めるべき教えと、生活への適用のヒント
## 次週の目標 — エホバの証人としての霊的目標の提案。進捗を自分で確認できる
具体的で測定可能な形(例: 個人研究の回数、集会での注解、奉仕での実践)で3〜5項目

前置き・免責・出力形式の説明は書かない。出力はMarkdown本文のみ。
PROMPT_EOF

echo "=== 週次振り返り生成: ${start}〜${end} ==="
mkdir -p "$out_dir"
if claude -p "$PROMPT" --model claude-fable-5 --output-format text \
    < "$input" > "$out.tmp"; then
    if [ -s "$out.tmp" ]; then
        mv "$out.tmp" "$out"
        echo "完了: $out"
    else
        rm -f "$out.tmp"
        echo "週次振り返り失敗(空出力)" >&2
        rm -f "$input"
        exit 1
    fi
else
    rm -f "$out.tmp" "$input"
    echo "週次振り返り失敗(claude実行エラー)" >&2
    exit 1
fi
rm -f "$input"
