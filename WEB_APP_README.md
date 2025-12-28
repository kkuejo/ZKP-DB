# ZKP-DB Webアプリケーション セットアップガイド

準同型暗号とゼロ知識証明を使用したプライバシー保護医療データマーケットプレイス

## システム構成

```
ZKP-DB/
├── backend/                    # バックエンドAPI (Flask)
│   ├── provider_api.py        # データ提供者API
│   ├── encryption_service.py  # 暗号化・ZKPサービス
│   ├── security_checks.py     # セキュリティチェック
│   └── requirements.txt
│
├── frontend/
│   ├── provider-app/          # データ提供者側フロントエンド (Vite + React)
│   │   └── src/
│   │       ├── App.jsx
│   │       └── ...
│   │
│   └── purchaser-app/         # データ購入者側フロントエンド (Vite + React)
│       └── src/
│           ├── App.jsx
│           └── ...
│
├── circuits/                   # ZKP回路
│   └── data_verification.circom
│
└── keys/                       # 暗号鍵
```

## 前提条件

### 必須ソフトウェア

- **Python 3.8+**
- **Node.js 18+** & npm
- **Circom 2.x** (ZKP回路コンパイラ)
- **snarkjs** (ZKP証明生成/検証)

### インストール

#### 1. Circom のインストール

```bash
# Rustをインストール (未インストールの場合)
curl --proto '=https' --tlsv1.2 https://sh.rustup.rs -sSf | sh
source ~/.cargo/env

# Circomをインストール
git clone https://github.com/iden3/circom.git
cd circom
cargo build --release
cargo install --path circom
cd ..
```

#### 2. snarkjs のインストール

```bash
npm install -g snarkjs
```

## セットアップ手順

### ステップ1: ZKP回路のコンパイルとセットアップ

```bash
# プロジェクトルートで実行

# 1. 回路をコンパイル
cd circuits
mkdir -p build
circom data_verification.circom --r1cs --wasm --sym -o build/

# 2. Powers of Tau セットアップ
cd build
snarkjs powersoftau new bn128 14 pot14_0000.ptau
snarkjs powersoftau contribute pot14_0000.ptau pot14_0001.ptau \
  --name="First contribution" -e="random text"
snarkjs powersoftau prepare phase2 pot14_0001.ptau pot14_final.ptau

# 3. Groth16 セットアップ
snarkjs groth16 setup data_verification.r1cs pot14_final.ptau data_verification_0000.zkey

# 4. 検証鍵を生成
snarkjs zkey export verificationkey data_verification_0000.zkey ../../keys/verification_key.json

# 5. zkey を keys/ にコピー
cp data_verification_0000.zkey ../../keys/

cd ../..
```

### ステップ2: バックエンドのセットアップ

```bash
# Python仮想環境を作成
cd backend
python3 -m venv venv
source venv/bin/activate  # Windowsの場合: venv\Scripts\activate

# 依存関係をインストール
pip install -r requirements.txt

# バックエンドAPIを起動
python provider_api.py
```

バックエンドは `http://localhost:5000` で起動します。

### ステップ3: データ提供者側フロントエンドのセットアップ

```bash
# 新しいターミナルを開く
cd frontend/provider-app

# 依存関係をインストール
npm install

# 開発サーバーを起動
npm run dev
```

データ提供者アプリは `http://localhost:3000` で起動します。

### ステップ4: データ購入者側フロントエンドのセットアップ

```bash
# さらに新しいターミナルを開く
cd frontend/purchaser-app

# 依存関係をインストール
npm install

# 開発サーバーを起動
npm run dev
```

データ購入者アプリは `http://localhost:3001` で起動します。

## 使用方法

### データ提供者側 (http://localhost:3000)

1. **CSVファイルをアップロード**
   - 患者データのCSVファイル（最低100件必要）
   - 必須フィールド: age, blood_pressure_systolic, blood_pressure_diastolic, blood_sugar, cholesterol

2. **暗号化パッケージを作成**
   - 「暗号化して販売パッケージを作成」ボタンをクリック
   - `encrypted_package.zip` がダウンロードされます

3. **パッケージの内容**
   - `encrypted_data.pkl` - 暗号化された患者データ
   - `public_context.pkl` - 公開鍵
   - `proof.json` - ZKP証明
   - `public_signals.json` - 公開信号
   - `verification_key.json` - 検証鍵
   - `metadata.json` - メタデータ

### データ購入者側 (http://localhost:3001)

#### 1. ZKP証明の検証

1. `proof.json` と `public_signals.json` をアップロード
2. 「証明書を検証」ボタンをクリック
3. データの正当性が確認されます

#### 2. 計算結果の復号

1. **Provider ID** を入力 (例: `provider_0`)
2. **Purchaser ID** を入力 (例: `pharma_company_123`)
3. **操作** を選択 (mean, sum, std, count)
4. **フィールド** を入力 (例: `age`)
5. **サンプルサイズ** を入力 (最低100)
6. **暗号化された結果** (16進数) を入力
7. 「復号リクエストを送信」ボタンをクリック

## セキュリティ機能

### 実装済みのセキュリティチェック

✅ **k-匿名性チェック**
- 最低100件のデータを含む統計のみ許可
- 個別データの復号を拒否

✅ **集約統計のみ許可**
- 許可される操作: mean, sum, std, variance, count, min, max
- 個別患者データへのアクセスは拒否

✅ **レート制限**
- 1時間あたり100リクエストまで
- 超過するとHTTP 429エラー

✅ **データ再構成攻撃検出**
- 類似クエリを検出 (Jaccard類似度)
- 24時間以内に5回以上の類似クエリで拒否

✅ **プライバシーバジェット管理**
- 累積的なプライバシー損失を追跡
- 将来の差分プライバシー導入に対応

✅ **監査ログ**
- すべてのリクエストを記録
- セキュリティイベントを分類 (INFO/WARNING/ERROR/CRITICAL)

### セキュリティ制限の例

```python
# ❌ 拒否されるクエリ例

# 1. k-匿名性違反 (サンプルサイズ < 100)
{
  "operation": "mean",
  "sample_size": 50  # ← エラー
}

# 2. 個別データクエリ
{
  "operation": "get_value",  # ← 許可されていない操作
  "patient_id": "P0001"
}

# 3. レート制限超過
# 1時間に101回目のリクエスト → HTTP 429

# 4. 類似クエリ攻撃
# 同じようなクエリを6回繰り返す → 拒否
```

## API エンドポイント

### バックエンド API (http://localhost:5000)

#### POST /api/encrypt
患者データを暗号化してZKP証明を生成

**Request:**
- `multipart/form-data`
- `file`: CSVファイル

**Response:**
- `application/zip`: 暗号化パッケージ (encrypted_package.zip)

#### POST /api/decrypt
暗号化された計算結果を復号

**Request:**
```json
{
  "provider_id": "provider_0",
  "purchaser_id": "pharma_company_123",
  "encrypted_result": "hex string",
  "metadata": {
    "operation": "mean",
    "field": "age",
    "sample_size": 100,
    "filters": {}
  }
}
```

**Response:**
```json
{
  "result": [55.2],
  "metadata": {...},
  "remaining_budget": 10.0,
  "remaining_requests": 95,
  "status": "success"
}
```

#### POST /api/verify-proof
ZKP証明を検証

**Request:**
```json
{
  "proof": {...},
  "public_signals": [...]
}
```

**Response:**
```json
{
  "valid": true,
  "message": "Proof verification successful"
}
```

## トラブルシューティング

### Circom not found

```bash
# Circomへのパスを追加
export PATH="$PATH:~/.cargo/bin"
```

### snarkjs not found

```bash
# グローバルにインストール
npm install -g snarkjs
```

### CORS エラー

バックエンド (`provider_api.py`) で CORS が有効になっていることを確認:
```python
from flask_cors import CORS
CORS(app)
```

### k-anonymity violation

CSVファイルに最低100行のデータが含まれていることを確認してください。

## 開発モード

### バックエンドのホットリロード

```bash
cd backend
source venv/bin/activate
export FLASK_ENV=development
python provider_api.py
```

### フロントエンドのホットリロード

Viteが自動的にファイル変更を検出してリロードします。

## プロダクションビルド

### フロントエンド

```bash
# データ提供者側
cd frontend/provider-app
npm run build
# dist/ フォルダに本番用ファイルが生成されます

# データ購入者側
cd frontend/purchaser-app
npm run build
# dist/ フォルダに本番用ファイルが生成されます
```

### バックエンド

```bash
cd backend
# Gunicornを使用 (本番環境)
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 provider_api:app
```

## セキュリティ考慮事項

### 本番環境での推奨事項

1. **HTTPS を使用**
   - すべての通信を暗号化

2. **認証・認可を追加**
   - API キーの管理
   - JWT トークン認証

3. **秘密鍵の安全な保管**
   - Hardware Security Module (HSM) の使用
   - Azure Key Vault / AWS KMS などのクラウドサービス

4. **レート制限の強化**
   - IP ベースの制限
   - 購入者ごとの厳格なクォータ

5. **監査ログの永続化**
   - データベースへの保存
   - セキュリティ分析ツールとの連携

6. **侵入検知システム (IDS)**
   - 異常なアクセスパターンの検出
   - 自動ブロック機能

## 参考ドキュメント

プロジェクト内の `docs/` フォルダに詳細なドキュメントがあります：

- `DecryptionStrategies.md` - 復号戦略と防御メカニズム
- `ModelParameterPrivacy.md` - モデルパラメータのプライバシーリスク
- `KAnonymityLimitations.md` - k-匿名性の限界
- `DifferentialPrivacyExplained.md` - 差分プライバシーの解説
- `HomomorphicEncryption.md` - 準同型暗号の技術背景
- `ZKP.md` - ゼロ知識証明の技術背景

## ライセンス

このプロジェクトはデモンストレーション目的で作成されています。

## サポート

問題が発生した場合は、GitHubのIssuesを確認してください。
