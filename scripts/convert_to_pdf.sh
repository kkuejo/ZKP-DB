#!/bin/bash
set -euo pipefail

# Markdown to PDF 変換スクリプト
# 使い方: ./scripts/convert_to_pdf.sh [ファイル名.md]

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

MD_TO_PDF_BIN=""
if [ -x "$ROOT_DIR/node_modules/.bin/md-to-pdf" ]; then
    MD_TO_PDF_BIN="$ROOT_DIR/node_modules/.bin/md-to-pdf"
else
    # npm install 未実行でも動くように（npx が都度取得）
    MD_TO_PDF_BIN="npx --yes md-to-pdf"
fi

# 日本語フォントを用意（WSL/Linuxで文字化けしやすいため）
bash "$ROOT_DIR/scripts/ensure_pdf_fonts.sh" || true

COMMON_ARGS=(
    --basedir "$ROOT_DIR"
    --stylesheet "$ROOT_DIR/scripts/pdf-style.css"
    --md-file-encoding "utf-8"
    --stylesheet-encoding "utf-8"
    --pdf-options '{ "format": "A4", "printBackground": true, "margin": { "top": "20mm", "bottom": "20mm", "left": "20mm", "right": "20mm" } }'
)

# 引数のチェック
if [ $# -eq 0 ]; then
    echo "使い方: $0 <markdown-file.md>"
    echo ""
    echo "例:"
    echo "  $0 docs/ZKP-DB_Explain.md"
    echo "  $0 docs/ZKP-DB-TechSpec.md"
    echo ""
    echo "すべてのドキュメントを変換する場合:"
    echo "  $0 all"
    exit 1
fi

# すべてのドキュメントを変換
if [ "$1" = "all" ]; then
    echo "すべてのMarkdownファイルをPDFに変換します..."

    for file in docs/*.md README.md; do
        if [ -f "$file" ]; then
            echo "変換中: $file"
            $MD_TO_PDF_BIN "$file" "${COMMON_ARGS[@]}"
            echo "✓ 完了: ${file%.md}.pdf"
        fi
    done

    echo ""
    echo "すべての変換が完了しました！"
    exit 0
fi

# 指定されたファイルを変換
if [ ! -f "$1" ]; then
    echo "エラー: ファイル '$1' が見つかりません"
    exit 1
fi

echo "PDFに変換中: $1"
$MD_TO_PDF_BIN "$1" "${COMMON_ARGS[@]}"

if [ $? -eq 0 ]; then
    output="${1%.md}.pdf"
    echo "✓ 変換完了: $output"
else
    echo "✗ 変換に失敗しました"
    exit 1
fi
