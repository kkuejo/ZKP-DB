# Railway デプロイ手順

このドキュメントでは、ZKP-DBバックエンドをRailwayにデプロイする手順を説明します。

## 前提条件

- GitHubアカウント
- このリポジトリがGitHubにプッシュされていること
- Railwayアカウント（無料プランで開始可能）

## デプロイ手順

### 1. Railwayアカウントの作成

1. [Railway](https://railway.app/)にアクセス
2. "Start a New Project"をクリック
3. GitHubアカウントでサインアップ/ログイン

### 2. プロジェクトの作成

#### オプションA: GitHubから直接デプロイ（推奨）

1. Railwayダッシュボードで "New Project" をクリック
2. "Deploy from GitHub repo" を選択
3. リポジトリ `kkuejo/ZKP-DB` を選択
4. "Deploy Now" をクリック

#### オプションB: Railway CLIを使用

```bash
# Railway CLIをインストール
npm i -g @railway/cli

# ログイン
railway login

# プロジェクトを初期化
railway init

# デプロイ
railway up
```

### 3. 環境変数の設定

Railwayダッシュボードで以下の環境変数を設定：

| 変数名 | 値 | 説明 |
|--------|-----|------|
| `PORT` | `8080` | アプリケーションポート |
| `PYTHONUNBUFFERED` | `1` | Pythonのバッファリング無効化 |

### 4. デプロイの確認

1. デプロイが完了すると、RailwayがURLを自動生成します
   - 例: `https://zkp-db-backend-production.up.railway.app`

2. ヘルスチェックエンドポイントにアクセスして確認：
   ```bash
   curl https://your-app.up.railway.app/api/health
   ```

   正常な応答：
   ```json
   {
     "status": "healthy",
     "service": "provider-api"
   }
   ```

### 5. フロントエンドの設定更新

GitHub Pagesにデプロイされたフロントエンド（`https://kkuejo.github.io/ZKP-DB/`）で、バックエンドのURLを更新：

```javascript
// script.js 内
const API_BASE_URL = 'https://your-app.up.railway.app';
```

変更をコミット・プッシュしてGitHub Pagesを更新。

## トラブルシューティング

### ビルドエラー

**症状**: Dockerビルドが失敗する

**解決策**:
1. Railwayのログを確認
2. ローカルでDockerビルドをテスト：
   ```bash
   docker build -t zkp-db-backend .
   docker run -p 8080:8080 zkp-db-backend
   ```

### メモリ不足エラー

**症状**: アプリケーションがクラッシュ、"Out of Memory"

**解決策**:
1. Railwayの無料プランは512MBまで
2. 有料プラン（Pro）にアップグレード（$5/月のクレジット）
3. または`encryption_service.py`の`poly_modulus_degree`を4096に下げる（すでに設定済み）

### ZKP証明生成エラー

**症状**: `/api/encrypt`で証明生成が失敗

**解決策**:
1. `circuits/`と`keys/`がDockerイメージに含まれているか確認
2. snarkjsが正しくインストールされているか確認：
   ```bash
   railway run bash
   which snarkjs
   snarkjs --version
   ```

### タイムアウトエラー

**症状**: リクエストがタイムアウトする

**解決策**:
- Gunicornのタイムアウトは180秒に設定済み
- Railwayのプロキシタイムアウトは300秒
- 大きなCSVファイル（100件以上）の処理には時間がかかる場合があります

## リソース使用状況の監視

Railwayダッシュボードで以下を監視：
- メモリ使用量
- CPU使用率
- ネットワーク使用量
- 月間クレジット消費

## コスト管理

### 無料プラン
- 月$5のクレジット（約500実行時間）
- 512MB RAM
- 1 vCPU
- 1GB ディスク

### 推奨設定
- 開発/テスト環境には無料プランで十分
- 本番環境では少なくとも1GB RAMを推奨

## カスタムドメインの設定（オプション）

1. Railwayダッシュボードで "Settings" → "Domains"
2. カスタムドメインを追加
3. DNSレコードを設定（RailwayがCNAMEを提供）

## 自動デプロイの設定

GitHubリポジトリのmainブランチへのプッシュで自動デプロイ：

1. Railwayダッシュボードで "Settings" → "Deploy"
2. "Automatic Deployments" を有効化
3. ブランチを `master` または `main` に設定

## セキュリティに関する注意

- 秘密鍵（`secret_contexts/`）はRailwayのストレージに保存されます
- 本番環境では、別途セキュアなキー管理システム（AWS KMS、HashiCorp Vaultなど）の使用を検討してください
- 環境変数には機密情報を含めないでください

## サポート

問題が発生した場合：
1. Railwayのログを確認
2. [Railway Discord](https://discord.gg/railway)でサポートを求める
3. GitHubリポジトリでIssueを作成

## 次のステップ

- [ ] デプロイの確認
- [ ] フロントエンドのAPI URL更新
- [ ] エンドツーエンドのテスト実行
- [ ] カスタムドメインの設定（オプション）
- [ ] 本番環境用のセキュリティ強化
