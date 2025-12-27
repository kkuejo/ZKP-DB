#!/bin/bash

# Markdown to PDF 変換スクリプト
# 使い方: ./scripts/convert_to_pdf.sh [ファイル名.md]

# md-to-pdfがインストールされているか確認
if ! npm list -g md-to-pdf > /dev/null 2>&1; then
    echo "md-to-pdfをインストールしています..."
    npm install -g md-to-pdf
fi

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
            md-to-pdf "$file" --stylesheet scripts/pdf-style.css
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
md-to-pdf "$1" --stylesheet scripts/pdf-style.css

if [ $? -eq 0 ]; then
    output="${1%.md}.pdf"
    echo "✓ 変換完了: $output"
else
    echo "✗ 変換に失敗しました"
    exit 1
fi
