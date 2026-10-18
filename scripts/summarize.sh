#!/usr/bin/env bash
# 1日分(=日付フォルダ)の文字起こしを活動ごとに要約し summary.md を生成する。
# 使い方: summarize.sh <ルートフォルダ>
# 前提: claude CLI が PATH にあり、CLAUDE_CODE_OAUTH_TOKEN で認証済み(GitHub Actions)
set -u
shopt -s nullglob

root="${1:?usage: summarize.sh <folder>}"
status=0

read -r -d '' PROMPT <<'PROMPT_EOF' || true
以下は1日分の録音の文字起こしで、「----- 活動: <名前> -----」で区切られている。
録音は集会の講話に限らず、集会前後の会話、集会以外の場面での会話や活動も含みうる。
これは自動音声認識の出力であり、誤字・誤変換・脱落が多分に含まれる。文脈から本来の語
(固有名詞や、話題が聖書・集会に関するときは聖書関連の用語・書名を含む)を推定して補完し、
認識誤りをそのまま引用しないこと。
活動ごとに「## <名前>」の見出しを付け、その活動の内容を日本語で要約せよ。
講話・発表などの本題だけでなく、その前後や合間の会話・やり取りも省略せず要約に含めること。
本題と前後の会話が混在する活動では、それぞれを小見出し(### 本題 / ### 前後の会話 など)で分けてよい。
会話については、誰がどんな話題で何を話したか、どんな態度・言葉遣いだったかが分かるように書く。
各活動の要約は要点の箇条書き＋2〜3文の総括とする。

要約の目的は、録音者がクリスチャンとしての在り方を見直し改善することにある。
すべての活動の後に「## クリスチャンとしての振り返り」の見出しを設け、次を書く。
- 良かった点: 会話や行動の中で、愛・親切・謙遜・励まし・聖書の原則に沿っていた言動
- 改善できる点: 批判・不満・陰口・いらだち・自慢・無関心など、改める余地のある言動。
  発言と推定できる箇所を根拠として示し、なぜそう言えるかを添える
- 講話から生活に当てはめられる点: 講話・発表で学んだ内容のうち、具体的に実践できること
- 次に取り組むこと: 上記を踏まえた具体的な行動目標を1〜3個
聖書の原則を挙げる場合は、確信のある聖句のみ書名・章節を添え、不確かなら聖句を示さない。
文字起こしから読み取れない事柄を推測で付け加えず、該当がなければその項目は「特になし」とする。
責めるのではなく、励ましつつ率直に指摘する口調で書く。
前置き・免責・出力形式の説明は書かない。出力はMarkdown本文のみ。
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
