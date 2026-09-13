#!/usr/bin/env bash
# 1日分(=日付フォルダ)の文字起こしを活動ごとに要約し summary.md を生成する。
# 使い方: summarize.sh <ルートフォルダ>
# 前提: claude CLI が PATH にあり、CLAUDE_CODE_OAUTH_TOKEN で認証済み(GitHub Actions)
set -u
shopt -s nullglob

root="${1:?usage: summarize.sh <folder>}"
status=0

read -r -d '' PROMPT <<'PROMPT_EOF' || true
以下は1日分の講話の文字起こしで、「----- 活動: <名前> -----」で区切られている。
これは自動音声認識の出力であり、誤字・誤変換・脱落が多分に含まれる。文脈から本来の語
(聖書関連の用語・書名・固有名詞を含む)を推定して補完し、認識誤りをそのまま引用しないこと。
活動ごとに「## <名前>」の見出しを付け、その活動の内容を日本語で要約せよ。
各活動の要約は要点の箇条書き＋2〜3文の総括とする。前置き・免責・出力形式の説明は書かない。
出力はMarkdown本文のみ。
PROMPT_EOF

for d in "$root" "$root"/*/; do
    d="${d%/}"
    [ -d "$d/transcripts" ] || continue
    if [ -f "$d/summary.md" ]; then
        echo "スキップ(要約済み): $d"
        continue
    fi
    txts=("$d"/transcripts/*.txt)
    [ ${#txts[@]} -gt 0 ] || continue

    echo "=== 要約生成: $d (${#txts[@]}活動) ==="
    input="$(mktemp)"
    for f in "${txts[@]}"; do
        {
            echo "----- 活動: $(basename "$f" .txt) -----"
            cat "$f"
            echo
        } >> "$input"
    done

    if claude -p "$PROMPT" --model claude-fable-5 --output-format text \
        < "$input" > "$d/summary.md.tmp"; then
        # 空出力を成果物として残さない(次回再試行させる)
        if [ -s "$d/summary.md.tmp" ]; then
            mv "$d/summary.md.tmp" "$d/summary.md"
            echo "完了: $d/summary.md"
        else
            rm -f "$d/summary.md.tmp"
            echo "要約失敗(空出力): $d" >&2
            status=1
        fi
    else
        rm -f "$d/summary.md.tmp"
        echo "要約失敗(claude実行エラー): $d" >&2
        status=1
    fi
    rm -f "$input"
done
exit $status
