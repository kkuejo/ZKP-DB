# Render デプロイ手順

このドキュメントでは、ZKP-DBバックエンドをRenderにデプロイする手順を説明します。

## 修正内容

元々の`render.yaml`はPythonのみの環境でしたが、以下の理由で動作しませんでした：
- ❌ Node.js（ZKP処理に必要）未インストール
- ❌ `circuits/`と`keys/`ディレクトリにアクセスできない
- ❌ TenSEALのビルド依存関係がない

**解決策**: Dockerベースのデプロイに変更しました（`env: docker`）

## 前提条件

- Renderアカウント（無料で作成可能）
- GitHubリポジトリがパブリック、またはRenderとGitHubを接続済み

## デプロイ手順

### 1. Renderにサインアップ/ログイン

1. [Render](https://render.com/)にアクセス
2. GitHubアカウントでサインアップ/ログイン

### 2. 新しいWebサービスを作成

#### オプションA: render.yamlを使用（推奨）

1. Renderダッシュボードで **"New +"** → **"Blueprint"** をクリック
2. GitHubリポジトリ `kkuejo/ZKP-DB` を接続
3. `render.yaml`が自動的に検出されます
4. **"Apply"** をクリック

#### オプションB: 手動設定

1. Renderダッシュボードで **"New +"** → **"Web Service"** をクリック
2. GitHubリポジトリ `kkuejo/ZKP-DB` を選択
3. 以下の設定を入力：
   - **Name**: `zkp-db-backend`
   - **Environment**: `Docker`
   - **Region**: `Oregon (US West)` または `Frankfurt (EU Central)`
   - **Branch**: `master`
   - **Dockerfile Path**: `./Dockerfile`
   - **Docker Context**: `.`（ルートディレクトリ）

4. **Advanced** セクション:
   - **Health Check Path**: `/api/health`
   - **Auto-Deploy**: `Yes`

5. **Environment Variables**:
   ```
   PYTHONUNBUFFERED=1
   PORT=8080
   ```

6. **Create Web Service** をクリック

### 3. デプロイの監視

デプロイが開始されます（初回は10-15分かかります）：
- **Building**: Dockerイメージをビルド中
- **Deploying**: コンテナを起動中
- **Live**: デプロイ完了

ログを確認して、エラーがないか監視してください。

### 4. デプロイ完了後の確認

RenderがURLを自動生成します：
```
https://zkp-db-backend.onrender.com
```

ヘルスチェック：
```bash
curl https://zkp-db-backend.onrender.com/api/health
```

期待される応答：
```json
{
  "status": "healthy",
  "service": "provider-api"
}
```

## Render無料プランの制限

- **512MB RAM**
- **アイドルタイムアウト**: 15分間リクエストがないと自動スリープ
- **コールドスタート**: スリープ後の初回リクエストは30秒-1分かかる
- **ビルド時間**: 制限あり（通常10-20分まで）

## トラブルシューティング

### ビルドタイムアウト

**症状**: ビルドが途中で失敗する

**解決策**:
- Renderの無料プランでは長いビルドは厳しい
- ローカルでDockerビルドをテストして時間を確認：
  ```bash
  time docker build -t zkp-db-backend .
  ```
- 10分以上かかる場合は、有料プランが必要かも

### メモリ不足エラー

**症状**: アプリケーションがクラッシュ、"Out of Memory"

**解決策**:
1. Renderのログを確認
2. `encryption_service.py`の`poly_modulus_degree`を4096から2048に下げる（セキュリティレベル低下）
3. または有料プラン（Starter: $7/月、1GB RAM）にアップグレード

### コールドスタート遅延

**症状**: 15分アイドル後、初回リクエストが非常に遅い

**解決策**:
- 無料プランの仕様（回避不可）
- 有料プランでは常時起動可能
- または、定期的にヘルスチェックを送信（外部cronサービス）

### ZKP証明生成エラー

**症状**: `/api/encrypt`で証明生成が失敗

**解決策**:
1. Renderのログを確認
2. Node.jsとsnarkjsが正しくインストールされているか確認
3. `circuits/`と`keys/`がイメージに含まれているか確認

Renderのシェルで確認：
```bash
# Renderダッシュボード → Shell
ls -la /app/circuits/
ls -la /app/keys/
which snarkjs
node --version
```

### ポートエラー

**症状**: "Application failed to bind to $PORT"

**解決策**:
- Dockerfileで`ENV PORT=8080`が設定されているか確認
- Gunicornが`${PORT}`環境変数を使用しているか確認

## カスタムドメインの設定（有料プランのみ）

1. Renderダッシュボードで **"Settings"** → **"Custom Domain"**
2. ドメインを追加
3. DNSレコードを設定（RenderがCNAMEを提供）

## 自動デプロイ

GitHubの`master`ブランチにプッシュすると自動的にデプロイされます。

無効化する場合：
1. Renderダッシュボードで **"Settings"**
2. **"Auto-Deploy"** を `No` に設定

## コスト

- **Free**: $0/月（512MB RAM、アイドルスリープあり）
- **Starter**: $7/月（512MB RAM、常時起動）
- **Standard**: $25/月（2GB RAM）

## セキュリティ

環境変数（シークレット）の設定：
1. Renderダッシュボードで **"Environment"**
2. 環境変数を追加
3. 再デプロイ

## フロントエンドの更新

GitHub Pagesのフロントエンドで、バックエンドURLを更新：

```javascript
// script.js
const API_BASE_URL = 'https://zkp-db-backend.onrender.com';
```

変更をコミット・プッシュしてGitHub Pagesを更新。

## サポート

- [Renderドキュメント](https://render.com/docs)
- [Renderコミュニティフォーラム](https://community.render.com/)

## 次のステップ

- [ ] Renderにログイン
- [ ] Blueprintまたは手動でWebサービスを作成
- [ ] デプロイの監視
- [ ] ヘルスチェック確認
- [ ] フロントエンドのAPI URL更新
- [ ] エンドツーエンドテスト
