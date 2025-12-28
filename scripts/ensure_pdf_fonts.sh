#!/bin/bash
set -euo pipefail

# ZKP-DB: md-to-pdf(Puppeteer/Chromium) で日本語が文字化けしないように
# 日本語フォント（Noto Sans JP）をローカルに用意します。
#
# - 既にシステムに日本語フォントが入っている場合は何もしません
# - システムに無い場合、scripts/fonts/ にフォントをダウンロードします
#
# 使い方:
#   bash scripts/ensure_pdf_fonts.sh

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FONT_DIR="$ROOT_DIR/scripts/fonts"

REGULAR_OTF="$FONT_DIR/NotoSansCJKjp-Regular.otf"
BOLD_OTF="$FONT_DIR/NotoSansCJKjp-Bold.otf"

have_cmd() { command -v "$1" >/dev/null 2>&1; }

system_has_jp_font() {
  if ! have_cmd fc-match; then
    return 1
  fi

  # fc-match が DejaVu 等を返す場合は日本語フォントが入っていない可能性が高い
  # Noto Sans JP / Noto Sans CJK JP / IPAex 等のいずれかにヒットすればOK扱い
  local out
  out="$(fc-match 'Noto Sans JP' 2>/dev/null || true)"
  if echo "$out" | grep -qi 'Noto'; then
    return 0
  fi
  out="$(fc-match 'Noto Sans CJK JP' 2>/dev/null || true)"
  if echo "$out" | grep -qi 'Noto'; then
    return 0
  fi
  out="$(fc-match 'IPAexGothic' 2>/dev/null || true)"
  if echo "$out" | grep -qi 'IPA'; then
    return 0
  fi
  return 1
}

download() {
  local url="$1"
  local dst="$2"

  mkdir -p "$FONT_DIR"

  if [ -f "$dst" ]; then
    return 0
  fi

  if have_cmd curl; then
    curl -L --fail --silent --show-error -o "$dst" "$url"
    return 0
  fi
  if have_cmd wget; then
    wget -O "$dst" "$url"
    return 0
  fi

  echo "エラー: curl/wget が見つかりません。フォントを自動ダウンロードできません。" >&2
  return 1
}

main() {
  # 1) システムに日本語フォントが入っているなら、それを使えるので完了
  if system_has_jp_font; then
    echo "日本語フォントがシステムに見つかりました。追加のダウンロードは不要です。"
    return 0
  fi

  # 2) ローカルフォントが揃っているなら完了
  if [ -f "$REGULAR_OTF" ] && [ -f "$BOLD_OTF" ]; then
    echo "ローカル日本語フォントが既に存在します: scripts/fonts/"
    return 0
  fi

  echo "日本語フォントが見つからないため、ローカルに Noto Sans JP を用意します..."

  # 公式配布元（googlefonts/noto-cjk）から取得
  # ※サイズが大きいので、git管理はせず scripts/fonts/ に保存します（.gitignore 済み）
  local base="https://raw.githubusercontent.com/googlefonts/noto-cjk/main/Sans/OTF/Japanese"
  download "$base/NotoSansCJKjp-Regular.otf" "$REGULAR_OTF"
  download "$base/NotoSansCJKjp-Bold.otf" "$BOLD_OTF"

  echo "フォントを保存しました:"
  echo " - $REGULAR_OTF"
  echo " - $BOLD_OTF"
  echo ""
  echo "補足: システムに入れる場合は (Ubuntu/WSL) 例: sudo apt-get install -y fonts-noto-cjk"
}

main "$@"


