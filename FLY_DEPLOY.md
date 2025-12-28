# Fly.io デプロイ手順

このドキュメントでは、ZKP-DBバックエンドをFly.ioにデプロイする手順を説明します。

## 前提条件

- Fly.ioアカウント（無料で作成可能）
- Fly.io CLIがインストール済み（✅ 完了）

## デプロイ手順

### 1. Fly.ioにログイン

ターミナルで以下のコマンドを実行：

```bash
export PATH="$HOME/.fly/bin:$PATH"
flyctl auth login
```

ブラウザが開き、Fly.ioのログイン画面が表示されます。
- 新規の場合：GitHubアカウントでサインアップ
- 既存の場合：ログイン

### 2. アプリケーションの作成とデプロイ

```bash
# プロジェクトディレクトリに移動
cd /home/kenichiuejo/src/ZKP-DB

# Fly.ioアプリを起動（初回のみ）
flyctl launch --no-deploy

# 以下の質問に答えてください：
# - App Name: zkp-db-backend (または任意の名前)
# - Region: Tokyo (nrt) を選択
# - PostgreSQL database: No
# - Redis database: No

# デプロイを実行
flyctl deploy
```

### 3. デプロイの確認

デプロイが完了すると、URLが表示されます：
```
https://zkp-db-backend.fly.dev
```

ヘルスチェック：
```bash
curl https://zkp-db-backend.fly.dev/api/health
```

期待される応答：
```json
{
  "status": "healthy",
  "service": "provider-api"
}
```

## 無料枠の制限

Fly.ioの無料枠：
- **3つの共有CPU VM**
- **256MB RAM** × 3（合計768MB）
- **3GB 永続ストレージ**
- **160GB アウトバウンド転送**

**注意**: 現在の設定では512MBのメモリを要求しています。無料枠では256MBまでなので、必要に応じて調整してください。

### メモリを256MBに下げる（オプション）

`fly.toml`を編集：
```toml
[[vm]]
  memory = '256mb'  # 512mb から 256mb に変更
  cpu_kind = 'shared'
  cpus = 1
```

その後、再デプロイ：
```bash
flyctl deploy
```

## よく使うコマンド

```bash
# アプリのステータス確認
flyctl status

# ログを表示
flyctl logs

# アプリを開く（ブラウザで）
flyctl open

# アプリを停止
flyctl apps destroy zkp-db-backend

# リソース使用状況を確認
flyctl dashboard
```

## トラブルシューティング

### メモリ不足エラー

**症状**: アプリがクラッシュ、"Out of Memory"

**解決策**:
1. `fly.toml`でメモリを増やす（有料）
2. または、`encryption_service.py`の`poly_modulus_degree`を4096→2048に下げる（セキュリティレベル低下）

### ビルドタイムアウト

**症状**: ビルドが時間切れになる

**解決策**:
```bash
flyctl deploy --remote-only
```

### デプロイが失敗する

**症状**: デプロイエラー

**解決策**:
1. ログを確認：
   ```bash
   flyctl logs
   ```
2. ローカルでDockerビルドをテスト：
   ```bash
   docker build -t zkp-db-backend .
   docker run -p 8080:8080 zkp-db-backend
   ```

### ZKP証明生成エラー

**症状**: `/api/encrypt`で証明生成が失敗

**確認事項**:
- Node.jsとsnarkjsが正しくインストールされているか
- `circuits/`と`keys/`がイメージに含まれているか

デバッグ：
```bash
flyctl ssh console
ls -la /app/circuits/
ls -la /app/keys/
which snarkjs
```

## カスタムドメインの設定（オプション）

```bash
# カスタムドメインを追加
flyctl certs add your-domain.com

# SSL証明書の状態を確認
flyctl certs show your-domain.com
```

DNSレコードを設定：
```
CNAME your-domain.com zkp-db-backend.fly.dev
```

## 自動デプロイの設定（GitHub Actions）

`.github/workflows/fly-deploy.yml`を作成：

```yaml
name: Deploy to Fly.io

on:
  push:
    branches:
      - master

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: superfly/flyctl-actions/setup-flyctl@master
      - run: flyctl deploy --remote-only
        env:
          FLY_API_TOKEN: ${{ secrets.FLY_API_TOKEN }}
```

Fly.io API トークンを取得：
```bash
flyctl auth token
```

GitHubリポジトリの Settings → Secrets → New repository secret:
- Name: `FLY_API_TOKEN`
- Value: （上記で取得したトークン）

## スケーリング

```bash
# VMの数を増やす
flyctl scale count 2

# メモリを増やす（有料）
flyctl scale memory 1024

# CPU性能を上げる（有料）
flyctl scale vm shared-cpu-2x
```

## コスト管理

無料枠を超えた場合の料金：
- RAM: $0.0000022/MB/秒
- CPU: $0.02/vCPU/時間

無料枠内に収めるコツ：
- `auto_stop_machines = true`を設定（アイドル時に自動停止）
- `min_machines_running = 0`を設定（完全停止を許可）

## セキュリティ

- 環境変数（シークレット）の設定：
  ```bash
  flyctl secrets set SECRET_KEY=your-secret-value
  ```

- 秘密鍵の管理：
  - `backend/secret_contexts/`はボリュームに保存されます
  - 本番環境では外部キー管理システムの使用を推奨

## フロントエンドの更新

GitHub Pagesのフロントエンドで、バックエンドURLを更新：

```javascript
// script.js
const API_BASE_URL = 'https://zkp-db-backend.fly.dev';
```

変更をコミット・プッシュしてGitHub Pagesを更新。

## サポート

- [Fly.io ドキュメント](https://fly.io/docs/)
- [Fly.io コミュニティフォーラム](https://community.fly.io/)
- [Discord](https://fly.io/discord)

## 次のステップ

- [ ] Fly.ioにログイン
- [ ] アプリを起動（fly launch）
- [ ] デプロイ実行（fly deploy）
- [ ] ヘルスチェック確認
- [ ] フロントエンドのAPI URL更新
- [ ] エンドツーエンドテスト
