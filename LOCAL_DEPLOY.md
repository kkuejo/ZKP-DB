# ローカルデプロイ手順

ZKP-DBをローカル環境で実行する方法を説明します。

## 前提条件

以下のソフトウェアがインストールされている必要があります：

- **Docker**: バージョン 20.10 以上
- **Docker Compose**: バージョン 2.0 以上

または

- **Python**: バージョン 3.11
- **Node.js**: バージョン 18 以上
- **npm**: バージョン 9 以上

## 方法1: Docker Compose（推奨・最も簡単）

### 1. リポジトリをクローン

```bash
git clone https://github.com/kkuejo/ZKP-DB.git
cd ZKP-DB
```

### 2. Docker Composeで起動

```bash
# バックエンドを起動
docker-compose up -d

# ログを確認
docker-compose logs -f backend
```

バックエンドが起動したら、以下のURLでアクセスできます：
```
http://localhost:8080/api/health
```

### 3. 動作確認

```bash
# ヘルスチェック
curl http://localhost:8080/api/health

# 期待される応答:
# {"status": "healthy", "service": "provider-api"}
```

### 4. フロントエンドの起動（オプション）

フロントエンドもローカルで実行する場合：

```bash
# Provider App
cd frontend/provider-app
npm install
npm run dev
# http://localhost:5173 でアクセス

# Purchaser App（別ターミナル）
cd frontend/purchaser-app
npm install
npm run dev
# http://localhost:5174 でアクセス
```

**注意**: ローカルフロントエンドを使う場合、`.env.local`ファイルを作成：

```bash
# frontend/provider-app/.env.local
VITE_API_BASE=http://localhost:8080/api

# frontend/purchaser-app/.env.local
VITE_API_BASE=http://localhost:8080/api
```

### 5. 停止とクリーンアップ

```bash
# サービスを停止
docker-compose down

# データボリュームも削除する場合
docker-compose down -v
```

---

## 方法2: Dockerのみ使用

### 1. Dockerイメージをビルド

```bash
docker build -t zkp-db-backend .
```

### 2. コンテナを実行

```bash
docker run -d \
  --name zkp-db-backend \
  -p 8080:8080 \
  -e PYTHONUNBUFFERED=1 \
  -e PORT=8080 \
  zkp-db-backend
```

### 3. ログを確認

```bash
docker logs -f zkp-db-backend
```

### 4. 停止と削除

```bash
docker stop zkp-db-backend
docker rm zkp-db-backend
```

---

## 方法3: Pythonで直接実行

### 1. 依存関係のインストール

#### Node.js（ZKP処理用）

```bash
# Node.js 18のインストール
# Ubuntu/Debian:
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# macOS (Homebrew):
brew install node@18

# snarkjsをグローバルにインストール
npm install -g snarkjs
```

#### Python依存関係

```bash
cd backend

# 仮想環境を作成（推奨）
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# または
venv\Scripts\activate  # Windows

# 依存関係をインストール
pip install -r requirements.txt
```

### 2. バックエンドを起動

```bash
cd backend

# 開発モード（デバッグ有効）
python provider_api.py

# または本番モード（Gunicorn）
gunicorn provider_api:app --bind 0.0.0.0:8080 --timeout 180 --workers 1
```

バックエンドが起動したら：
```
http://localhost:8080/api/health
```

### 3. フロントエンドを起動

```bash
# Provider App
cd frontend/provider-app
npm install
npm run dev

# Purchaser App（別ターミナル）
cd frontend/purchaser-app
npm install
npm run dev
```

---

## トラブルシューティング

### ポートが使用中

**エラー**: `Address already in use`

**解決策**:
```bash
# ポート8080を使用しているプロセスを確認
lsof -i :8080

# プロセスを終了
kill -9 <PID>

# または別のポートを使用
docker-compose up -d -e PORT=8081
```

### メモリ不足

**症状**: Docker コンテナがクラッシュ

**原因**: デフォルトパラメータ（`poly_modulus_degree=8192`）は約2GB以上のメモリを使用

**解決策**:
1. Dockerのメモリ制限を増やす（Docker Desktop設定で4GB以上を推奨）
2. または暗号化パラメータを軽量化：
   ```python
   # backend/encryption_service.py の _get_shared_context() 関数
   poly_modulus_degree=2048,  # 8192→2048に軽量化
   coeff_mod_bit_sizes=[30, 20, 20],  # [60,40,40,60]→軽量化
   ctx.global_scale = 2**20  # 2**40→軽量化
   ```
   ⚠️ セキュリティレベルは低下しますが、1GB以下で動作可能

### ZKP証明生成エラー

**症状**: `/api/encrypt`で証明生成が失敗

**確認事項**:
```bash
# snarkjsがインストールされているか
which snarkjs
snarkjs --version

# Node.jsのバージョン
node --version  # v18以上必要

# 必要なファイルが存在するか
ls -la circuits/build/data_verification_js/
ls -la keys/
```

### TenSEALインストールエラー

**症状**: `pip install tenseal`が失敗

**解決策**:
```bash
# ビルドツールをインストール
# Ubuntu/Debian:
sudo apt-get install build-essential cmake

# macOS:
xcode-select --install
brew install cmake
```

---

## 開発用の便利なコマンド

### ログの監視

```bash
# Docker Compose
docker-compose logs -f backend

# Docker
docker logs -f zkp-db-backend

# Python直接実行の場合
tail -f backend/provider_api.log
```

### コンテナ内でコマンド実行

```bash
# シェルに入る
docker-compose exec backend bash

# Pythonインタプリタ
docker-compose exec backend python

# ファイル確認
docker-compose exec backend ls -la /app/circuits/
```

### データベース/ストレージの確認

```bash
# 秘密鍵コンテキストの確認
docker-compose exec backend ls -la /app/backend/secret_contexts/
```

---

## 環境変数

以下の環境変数を設定できます：

| 変数名 | デフォルト値 | 説明 |
|--------|-------------|------|
| `PORT` | `8080` | バックエンドAPIのポート番号 |
| `PYTHONUNBUFFERED` | `1` | Pythonのバッファリング無効化 |
| `VITE_API_BASE` | `http://localhost:8080/api` | フロントエンドのAPI URL |

---

## API エンドポイント

ローカル環境で利用可能なAPIエンドポイント：

### ヘルスチェック
```bash
GET http://localhost:8080/api/health
```

### データ暗号化
```bash
POST http://localhost:8080/api/encrypt
Content-Type: multipart/form-data

file: <CSVファイル>
```

### 準同型演算
```bash
POST http://localhost:8080/api/compute
Content-Type: multipart/form-data

encrypted_package: <暗号化パッケージZIP>
operation: mean
field: age
```

### 復号化
```bash
POST http://localhost:8080/api/decrypt
Content-Type: application/json

{
  "provider_id": "provider_0",
  "purchaser_id": "test_purchaser",
  "encrypted_result": "<hex encoded data>",
  "metadata": {
    "operation": "mean",
    "field": "age",
    "sample_size": 100
  }
}
```

### ZKP証明検証
```bash
POST http://localhost:8080/api/verify-proof
Content-Type: application/json

{
  "proof": {...},
  "public_signals": [...]
}
```

---

## テストデータ

サンプルCSVファイルを作成してテスト：

```csv
age,blood_pressure_systolic,blood_pressure_diastolic,blood_sugar,cholesterol
45,120,80,95,180
52,135,85,105,200
38,115,75,88,165
...
```

**注意**: k-匿名性のため、最低100件のレコードが必要です。

---

## 次のステップ

- [ ] ローカル環境でバックエンドを起動
- [ ] ヘルスチェックAPIで動作確認
- [ ] テストデータで暗号化を試す
- [ ] フロントエンドをローカルで起動（オプション）
- [ ] エンドツーエンドのフローをテスト

---

## 本番環境との違い

| 項目 | ローカル | 本番（Render） |
|------|---------|---------------|
| URL | `http://localhost:8080` | `https://zkp-db.onrender.com` |
| HTTPS | なし | あり |
| メモリ制限 | なし（Dockerデフォルト） | 512MB |
| 永続化 | Dockerボリューム | Renderストレージ |
| 自動再起動 | `restart: unless-stopped` | Render自動管理 |
