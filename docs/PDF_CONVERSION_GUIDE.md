# PDF変換ガイド

## 概要

ZKP-DBプロジェクトのMarkdownドキュメントをPDFに変換する方法を説明します。

## 利用可能な変換方法

### 方法1: npm scripts（推奨）

最も簡単な方法です。

#### セットアップ

```bash
# プロジェクトルートで実行
npm install
```

これにより `md-to-pdf` が自動的にインストールされます。

#### 使い方

**すべてのドキュメントを一括変換**:

```bash
npm run pdf
```

このコマンドは以下のファイルを変換します：
- `docs/ZKP-DB_Explain.md` → `docs/ZKP-DB_Explain.pdf`
- `docs/ZKP-DB_Explain2.md` → `docs/ZKP-DB_Explain2.pdf`
- `docs/ZKP-DB-TechSpec.md` → `docs/ZKP-DB-TechSpec.pdf`
- `docs/anonymization_vs_encryption.md` → `docs/anonymization_vs_encryption.pdf`
- `README.md` → `README.pdf`

**個別のドキュメントを変換**:

```bash
# 営業向け説明資料（一般顧客向け）
npm run pdf:explain

# 共同開発提案資料（電子カルテ会社向け）
npm run pdf:explain2

# 技術仕様書
npm run pdf:techspec
```

### 方法2: シェルスクリプト直接実行

より柔軟な変換が必要な場合。

```bash
# 特定のファイルを変換
bash scripts/convert_to_pdf.sh docs/ZKP-DB_Explain.md

# すべてのファイルを変換
bash scripts/convert_to_pdf.sh all
```

### 方法3: md-to-pdf を直接使用

最もカスタマイズ性が高い方法。

```bash
# グローバルインストール
npm install -g md-to-pdf

# 変換
md-to-pdf docs/ZKP-DB_Explain.md --stylesheet scripts/pdf-style.css
```

## PDFの特徴

生成されるPDFには以下の特徴があります：

### デザイン

- ✅ **日本語対応**: 適切な日本語フォントで表示
- ✅ **A4サイズ**: 印刷に最適
- ✅ **カラー**: コードブロックやテーブルが色付き
- ✅ **見やすいレイアウト**: 適切な余白とフォントサイズ

### 構成要素

- **見出し**: 階層的で分かりやすい
- **コードブロック**: 背景色付きで読みやすい
- **テーブル**: ヘッダー強調、縞模様
- **リンク**: クリック可能
- **ページ番号**: 自動付与

### スタイル詳細

カスタムスタイルは `scripts/pdf-style.css` で定義されています：

```css
/* 主な特徴 */
- フォント: Noto Sans JP, Hiragino Kaku Gothic ProN
- 本文サイズ: 11pt
- コード: Courier New, 9pt
- 余白: 20mm
```

## トラブルシューティング

### 問題: 「md-to-pdf not found」エラー

**解決策**:

```bash
# パッケージを再インストール
npm install

# または、グローバルインストール
npm install -g md-to-pdf
```

### 問題: 日本語が文字化け

**原因（よくある）**:

- WSL / Linux 環境に **日本語フォントが入っていない**（Chromiumが日本語グリフを描けず文字化け/□になる）
- Markdownファイルが UTF-8 ではない

**解決策**:

まず Markdown ファイルが UTF-8 エンコーディングであることを確認してください。

```bash
# ファイルのエンコーディング確認
file -i docs/ZKP-DB_Explain.md

# UTF-8であることを確認
# 出力例: docs/ZKP-DB_Explain.md: text/plain; charset=utf-8
```

次に、日本語フォントを用意してください（どちらか一方でOK）:

**(A) 推奨: 付属スクリプトでローカルにフォントを用意（sudo不要）**

```bash
bash scripts/ensure_pdf_fonts.sh
```

**(B) システムにインストール（Ubuntu/WSL）**

```bash
sudo apt-get update
sudo apt-get install -y fonts-noto-cjk
```

確認（Notoが返ればOK）:

```bash
fc-match 'Noto Sans JP'
```

### 問題: CSSが適用されない

**解決策**:

スタイルシートのパスを確認してください。

```bash
# scripts/pdf-style.css が存在することを確認
ls -l scripts/pdf-style.css
```

### 問題: PDFが生成されない

**解決策1**: 権限を確認

```bash
# スクリプトに実行権限があることを確認
chmod +x scripts/convert_to_pdf.sh
```

**解決策2**: Puppeteerの依存関係

md-to-pdfは内部でPuppeteer（Chrome）を使用します。
依存関係が不足している場合があります。

```bash
# Ubuntu/Debianの場合
sudo apt-get install -y \
  gconf-service libasound2 libatk1.0-0 libcups2 \
  libdbus-1-3 libgdk-pixbuf2.0-0 libgtk-3-0 \
  libnspr4 libx11-xcb1 libxcomposite1 libxdamage1 \
  libxrandr2 fonts-liberation libappindicator1 \
  libnss3 xdg-utils

# macOSの場合
# 通常は追加のインストールは不要
```

## 代替ツール

md-to-pdfがうまく動作しない場合、以下の代替ツールもあります：

### Pandoc（最も高品質）

```bash
# インストール
# Ubuntu/Debian
sudo apt-get install pandoc texlive-latex-recommended texlive-fonts-recommended

# macOS
brew install pandoc basictex

# 使い方
pandoc docs/ZKP-DB_Explain.md -o docs/ZKP-DB_Explain.pdf \
  --pdf-engine=xelatex \
  -V CJKmainfont='Noto Sans JP' \
  -V geometry:margin=20mm
```

### wkhtmltopdf

```bash
# インストール
# Ubuntu/Debian
sudo apt-get install wkhtmltopdf

# macOS
brew install wkhtmltopdf

# まずMarkdownをHTMLに変換
# その後PDFに変換
```

## カスタマイズ

### スタイルのカスタマイズ

`scripts/pdf-style.css` を編集してPDFの見た目を変更できます。

```css
/* 例: フォントサイズを大きくする */
body {
  font-size: 12pt;  /* デフォルト: 11pt */
}

/* 例: コードブロックの背景色を変更 */
pre {
  background-color: #f0f0f0;
}
```

### ヘッダー・フッターの追加

md-to-pdfの設定ファイルを作成します：

```javascript
// pdf-config.js
module.exports = {
  stylesheet: 'scripts/pdf-style.css',
  pdf_options: {
    format: 'A4',
    margin: '20mm',
    displayHeaderFooter: true,
    headerTemplate: '<div style="font-size:10px; text-align:center; width:100%;">ZKP-DB Documentation</div>',
    footerTemplate: '<div style="font-size:10px; text-align:center; width:100%;"><span class="pageNumber"></span> / <span class="totalPages"></span></div>'
  }
};
```

使用方法：

```bash
md-to-pdf docs/ZKP-DB_Explain.md --config-file pdf-config.js
```

## ベストプラクティス

### 変換前のチェックリスト

- [ ] Markdownの文法が正しいか確認
- [ ] 画像のパスが正しいか確認
- [ ] テーブルの書式が整っているか確認
- [ ] コードブロックの言語指定があるか確認

### PDFの品質向上

1. **見出しの階層を正しく使う**
   ```markdown
   # H1: ドキュメントタイトル
   ## H2: セクション
   ### H3: サブセクション
   ```

2. **コードブロックに言語を指定**
   ```markdown
   ```python
   # Pythonコード
   ```
   ```

3. **テーブルを見やすく**
   ```markdown
   | 列1 | 列2 | 列3 |
   |-----|-----|-----|
   | データ | データ | データ |
   ```

4. **リンクは相対パスで**
   ```markdown
   [技術仕様書](ZKP-DB-TechSpec.md)
   ```

## まとめ

最も簡単な方法：

```bash
# 1. インストール（初回のみ）
npm install

# 2. すべてを変換
npm run pdf

# 3. 生成されたPDFを確認
ls -l docs/*.pdf
```

これでプレゼンテーション、提案書、ドキュメント配布に使えるPDFが生成されます！

## サポート

問題が発生した場合は、以下を確認してください：

1. Node.jsのバージョン: `node --version` (v16以上推奨)
2. npm のバージョン: `npm --version` (v8以上推奨)
3. エラーメッセージの内容

詳細なサポートが必要な場合は、Issueを作成してください。
