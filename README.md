# ZKP-DB: ゼロ知識証明を用いた医療データベース

準同型暗号とゼロ知識証明を組み合わせた、プライバシー保護型の医療データマーケットプレイス

## 概要

このプロジェクトは、カルテ会社が保有する医療データを、**プライバシーを保護しながら外部の研究機関や企業に販売・提供する**ためのシステムのプロトタイプです。

### 主な特徴

- **準同型暗号**: データを暗号化したまま統計計算・機械学習が可能
- **ゼロ知識証明**: データの正当性を証明し、改ざんを防止
- **差分プライバシー**: 統計結果にノイズを付加し、個人の参加を秘匿
- **全患者証明（Merkle Tree）**: 全データの正当性を効率的に証明
- **プライバシー保護**: 個別の患者データは秘匿されたまま
- **有用性の維持**: 暗号化されていても統計分析やML学習が可能

## システムアーキテクチャ

```
┌─────────────────────────────────────┐
│ データ提供者（カルテ会社）            │
├─────────────────────────────────────┤
│ 1. 患者データの準同型暗号化           │
│ 2. ゼロ知識証明の生成                │
│ 3. 暗号化データ + 証明 を販売         │
└──────────────┬──────────────────────┘
               │
               ↓ 販売
┌─────────────────────────────────────┐
│ データ購入者（研究機関・企業）         │
├─────────────────────────────────────┤
│ 1. ZKPで正当性を検証                 │
│ 2. 暗号化されたまま統計分析           │
│ 3. 機械学習モデルの学習               │
│ 4. プライバシーを守りながら知見獲得   │
└─────────────────────────────────────┘
```

## 技術スタック

### 準同型暗号
- **TenSEAL**: Microsoft SEALのPythonラッパー
- **CKKS方式**: 実数値の計算に対応

### ゼロ知識証明
- **Circom**: ZKP回路記述言語
- **snarkjs**: Groth16 zkSNARK実装
- **Poseidon**: 暗号学的ハッシュ関数

### その他
- **Python (Flask)**: バックエンドAPI（暗号化/復号/計算）
- **Node.js (Vite + React)**: データ提供者/購入者フロントエンド
- **NumPy, Pandas**: データ分析

## ディレクトリ構成

```
ZKP-DB/
├── backend/             # Flask API（/api/encrypt, /api/decrypt, /api/compute など）
├── frontend/
│   ├── provider-app/    # データ提供者フロント（Vite+React）
│   └── purchaser-app/   # データ購入者フロント（Vite+React）
├── circuits/            # Circom ZKP回路
├── scripts/             # Circom/snarkjs 補助スクリプト
├── docs/                # 説明資料
├── render.yaml          # Render 用デプロイ設定
├── scripts/prepare-gh-pages.sh # GitHub Pages 用ビルドコピー
└── gh-pages/            # Pages 配信用ビルド成果物（生成物）
```

## デプロイ

### 本番環境

#### バックエンド（Render）
- **URL**: https://zkp-db.onrender.com
- **デプロイ方法**: `render.yaml`を使用して自動デプロイ
- **詳細**: [RENDER_DEPLOY.md](./RENDER_DEPLOY.md)

#### フロントエンド（GitHub Pages）
- **Provider App**: https://kkuejo.github.io/ZKP-DB/provider/
- **Purchaser App**: https://kkuejo.github.io/ZKP-DB/purchaser/
- **デプロイ方法**: `scripts/prepare-gh-pages.sh`でビルドし、gh-pagesブランチにプッシュ

### ローカル環境

#### 方法1: Docker Compose（推奨・最も簡単）

```bash
# バックエンドを起動
docker-compose up -d

# ログを確認
docker-compose logs -f backend

# ヘルスチェック
curl http://localhost:8080/api/health
```

**詳細**: [LOCAL_DEPLOY.md](./LOCAL_DEPLOY.md)

#### 方法2: Pythonで直接実行

**前提条件**:
- Python 3.11+
- Node.js 18+ / npm
- snarkjs (`npm install -g snarkjs`)

**バックエンド**:
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python provider_api.py  # 開発モード
# または
gunicorn provider_api:app --bind 0.0.0.0:8080
```

**フロントエンド**:
```bash
# Provider App
cd frontend/provider-app
npm install
npm run dev  # http://localhost:5173

# Purchaser App
cd frontend/purchaser-app
npm install
npm run dev  # http://localhost:5174
```

### 補足
- 秘密鍵はバックエンドのみで保持し、暗号化パッケージには含めません
- 復号は常に `/api/decrypt` 経由で行います
- ローカル環境では`http://localhost:8080`、本番環境では`https://zkp-db.onrender.com`を使用

## 使い方

### クイックスタート: 統合デモの実行

すべての機能を一度に体験できる統合デモを実行：

```bash
python python/integrated_demo.py
```

このデモでは以下を実行します：
1. 100人の患者ダミーデータ生成
2. データの準同型暗号化
3. 暗号化されたまま統計計算
4. ゼロ知識証明の生成
5. 証明の検証
6. 改ざん検出のデモ

### 個別の実行

#### ステップ1: ダミーデータの生成

```bash
python python/generate_dummy_data.py
```

生成されるデータ：
- `data/patients.json`: 100人の患者データ（JSON形式）
- `data/patients.csv`: 同じデータ（CSV形式）

データ項目：
- 患者ID
- 年齢、性別
- 血圧（収縮期・拡張期）
- 血糖値
- コレステロール
- BMI
- 疾患名
- 治療法
- 入院歴

#### ステップ2: 準同型暗号化

```bash
python python/homomorphic_encryption.py
```

実行内容：
- データをCKKS方式で暗号化
- 暗号化されたまま平均値を計算
- 結果を`data/encrypted_patients.pkl`に保存
- 暗号化コンテキストを`keys/context.pkl`に保存

#### ステップ3: ZKP証明の生成

```bash
npm run generate-proof
```

または：

```bash
node scripts/generate_proof.js
```

実行内容：
- 最初の5人の患者について証明を生成
- 各患者のデータが有効範囲内にあることを証明
- 証明ファイルを`proofs/`ディレクトリに保存

特定の患者だけ証明を生成：

```bash
node scripts/generate_proof.js --patient P0001
```

#### ステップ4: 証明の検証

```bash
npm run verify-proof
```

または：

```bash
node scripts/verify_proof.js
```

実行内容：
- すべての証明を検証
- データの正当性を確認
- 改ざんがないかチェック

改ざん検出のデモ：

```bash
node scripts/verify_proof.js --demo-invalid
```

#### ステップ5: 機械学習の実行

**基本的な機械学習**:

```bash
python python/ml_encrypted.py
```

実行内容：
- 線形回帰でBMIを予測
- ロジスティック回帰で高血圧を予測
- 浅いニューラルネットワークの実行
- すべて暗号化されたまま計算

**高度な機械学習手法**:

```bash
python python/advanced_ml_techniques.py
```

実行内容：
- ハイブリッド暗号化（一部のみ暗号化）
- クライアント-サーバー対話型計算
- 知識蒸留（複雑→単純モデル）
- 各手法の比較

## ユースケース

### 1. カルテ会社（データ提供者）

**課題**:
- 大量の医療データを保有しているが活用しきれていない
- データ販売でビジネス化したいが、プライバシー保護が必須

**解決策**:
```bash
# データを暗号化
python python/homomorphic_encryption.py

# 正当性を証明
npm run generate-proof

# 販売パッケージ作成
# → 暗号化データ + 証明 + 検証鍵
```

**提供できるもの**:
- 暗号化された患者データ
- データの正当性を示すZKP証明
- 検証鍵
- 準同型暗号コンテキスト

### 2. 研究機関・製薬会社（データ購入者）

**課題**:
- 医療データが欲しいが、プライバシー規制がある
- データの信頼性を確認したい

**解決策**:
```bash
# 購入したデータの正当性を検証
npm run verify-proof

# 暗号化されたまま統計分析
python python/homomorphic_encryption.py
```

**できること**:
- データが改ざんされていないか検証
- 個別データを見ずに統計分析
- 暗号化されたままモデル学習

## 技術詳細

### 準同型暗号（CKKS方式）

データを暗号化したまま以下の演算が可能：

- **加算**: `Enc(a) + Enc(b) = Enc(a + b)`
- **乗算**: `Enc(a) × Enc(b) = Enc(a × b)`
- **スカラー倍**: `Enc(a) × k = Enc(a × k)`

これにより、暗号化されたまま：
- 平均値の計算
- 分散の計算
- 線形回帰
- ロジスティック回帰（多項式近似）
- ニューラルネットワーク（2-3層程度）
- k-means クラスタリング（一部）

が可能です。

### 機械学習の可能性と制限

#### ✅ 実装可能なMLモデル

1. **線形モデル** - 完全に可能
   - 線形回帰、リッジ回帰
   - 線形SVM
   - 暗号化のまま完璧に動作

2. **ロジスティック回帰** - 多項式近似で可能
   - Sigmoid関数を多項式で近似
   - 精度は若干低下するが実用的

3. **浅いニューラルネットワーク** - 2-3層なら可能
   - 活性化関数を多項式近似
   - 乗算の深さに注意が必要

4. **k-means** - ユークリッド距離計算が可能
   - クラスタリングの一部操作

5. **決定木** - 一部の操作は可能
   - 完全な実装は困難

#### ❌ 困難なMLモデル

1. **深いニューラルネットワーク**
   - 乗算の深さ制限により実装困難
   - ノイズが蓄積して精度が低下

2. **ReLU, Sigmoid などの非線形関数**
   - 直接計算は不可能
   - 多項式近似が必要（精度低下）

3. **比較演算が必要なモデル**
   - if文、max/min が困難
   - Random Forest、XGBoost など

4. **大規模なTransformer**
   - 計算量が膨大
   - 実用的な時間では実行不可

### ゼロ知識証明（Groth16）

以下を証明します：

1. **データの完全性**: ハッシュ値が一致
2. **範囲チェック**:
   - 年齢: 0-120歳
   - 収縮期血圧: 80-200 mmHg
   - 拡張期血圧: 50-130 mmHg
   - 血糖値: 50-300 mg/dL
   - コレステロール: 100-400 mg/dL

証明の生成と検証は高速（数秒以内）で、証明サイズも小さい（約1KB）です。

## パフォーマンス

### 暗号化
- 100人のデータ: 約2秒
- メモリ使用量: 約100MB

### ZKP証明生成
- 1件の証明: 約3-5秒
- 証明サイズ: 約1KB

### ZKP検証
- 1件の検証: 約50ms
- 非常に高速

## セキュリティ

### 保護されるもの
✅ 個別の患者データ（年齢、血圧など）
✅ 患者の特定可能な情報
✅ データの改ざん
✅ 個人のデータセット参加有無（差分プライバシー）

### 公開されるもの
- データのハッシュ値（Merkle Root）
- データが有効範囲内にあるという事実
- ノイズ付加済みの統計的な集計値

### 攻撃への耐性
- **改ざん検出**: ZKP + Merkle Treeにより検出可能
- **データ復元**: 準同型暗号により秘匿鍵なしでは不可能
- **統計攻撃**: 差分プライバシー（Laplace/Gaussian機構）で対策済み
- **メンバーシップ推論攻撃**: 差分プライバシーにより防止

### 差分プライバシー（実装済み）

統計結果にノイズを付加し、個人の参加を秘匿：

```python
# 使用例
from security_checks import DifferentialPrivacy, NoiseType

dp = DifferentialPrivacy(epsilon=1.0, delta=1e-5)

# 統計結果にノイズを付加
result = dp.apply_to_result(
    result=55.2,           # 元の統計値
    operation='mean',      # 操作種類
    field='age',           # フィールド
    sample_size=100,       # サンプル数
    noise_type=NoiseType.LAPLACE
)
# result['noisy_result'] = 55.9（ノイズ付加後）
```

### 全患者ZKP証明（Merkle Tree方式）

全患者データの正当性を効率的に証明：

```
┌─────────────────────────────┐
│         Merkle Root         │  ← 全患者のハッシュを集約
└─────────────────────────────┘
              ↑
    ┌─────────┴─────────┐
    │                   │
Hash(P1-P50)     Hash(P51-P100)
    │                   │
┌───┴───┐          ┌───┴───┐
│       │          │       │
P1     P2         P51     P52
```

- **全データの改ざん検出**: Merkle Rootで全患者をカバー
- **サンプルZKP証明**: 10人のサンプルでZKP検証
- **効率的な検証**: 計算コストを抑制

## 制限事項

### 準同型暗号の制限
- 乗算の深さに制限（ノイズが蓄積）
- 比較演算（>, <）は困難
- 非線形関数（ReLU, Sigmoid）は近似が必要

### ZKPの制限
- 回路の複雑さに応じてセットアップ時間が増加
- 大規模データセットでは証明生成時間が長い
- 回路の変更には再セットアップが必要

## 制限を回避する高度な手法

準同型暗号の制限を克服して、複雑な機械学習を実現する手法を実装しています。

### 1. ハイブリッド暗号化

**概念**: 機密性の高いデータだけを暗号化し、他は平文で処理

```python
# 年齢と血糖値のみ暗号化、他は平文
sensitive_indices = [0, 2]  # 年齢、血糖値
hybrid.setup(sensitive_indices, total_features=4)
```

**利点**:
- Random Forest、XGBoostなど複雑なモデルが使用可能
- 計算速度が速い
- プライバシーと性能のバランスを調整可能

**ユースケース**: 一部のフィールドのみ機密性が高い場合

### 2. クライアント-サーバー対話型計算

**概念**:
- サーバー: 線形演算を暗号化のまま実行
- クライアント: 非線形演算を復号して実行、再暗号化

```
サーバー側: y = Wx + b (暗号化のまま)
    ↓
クライアント側: activation(y) (復号→計算→再暗号化)
    ↓
サーバー側: 次の層の計算...
```

**利点**:
- ReLU、Sigmoidなどの非線形関数が正確に計算可能
- 深いニューラルネットワークも実装可能
- 精度の低下なし

**欠点**: 通信コストがかかる

**ユースケース**: 高精度が必要で、通信コストを許容できる場合

### 3. 知識蒸留

**概念**: 複雑な教師モデルの知識を、単純な生徒モデルに転移

```
教師モデル（複雑）: Random Forest, Deep NN
    ↓ 知識蒸留
生徒モデル（単純）: 線形モデル, 浅いNN
    ↓
暗号化データで推論可能
```

**利点**:
- 複雑なモデルの性能を保ちつつ、暗号化推論が可能
- 推論速度が速い

**ユースケース**: 訓練は平文、推論は暗号化データで行う場合

### 4. Federated Learning

**概念**: データを各所に残したまま、モデルのみを共有して学習

```
病院A, B, C:
  - ローカルでモデル訓練
  - 勾配のみを共有
  - ZKPで正当性を証明

中央サーバー:
  - 勾配を集約
  - 全体モデルを更新
```

**利点**:
- データを外部に出さない
- プライバシー保護が強力

**ユースケース**: 複数の医療機関でデータを共有できない場合

### 各手法の比較表

```
┌──────────────┬──────────┬────────┬────────┬────────┐
│   手法       │プライバシー│ 精度  │  速度  │ 実装難度│
├──────────────┼──────────┼────────┼────────┼────────┤
│ 純粋HE       │ ★★★★★ │ ★★☆☆☆│ ★☆☆☆☆│ ★★★☆☆│
│ ハイブリッド  │ ★★★☆☆ │ ★★★★☆│ ★★★★☆│ ★★☆☆☆│
│ 対話型       │ ★★★★☆ │ ★★★★★│ ★★★☆☆│ ★★★★☆│
│ 知識蒸留     │ ★★★☆☆ │ ★★★★☆│ ★★★★★│ ★★★☆☆│
│ Federated    │ ★★★★☆ │ ★★★★☆│ ★★★☆☆│ ★★★★★│
└──────────────┴──────────┴────────┴────────┴────────┘
```

### 実装済みの高度な機能

`python/advanced_ml_techniques.py` で以下を実装：

```bash
python python/advanced_ml_techniques.py
```

1. ハイブリッド暗号化のデモ
2. クライアント-サーバー対話型計算のデモ
3. 知識蒸留のデモ
4. 各手法の性能比較

## 今後の拡張

### 実装済み
- [x] 差分プライバシー（Laplace/Gaussian機構）
- [x] 全患者ZKP証明（Merkle Tree方式）
- [x] Webインターフェース（React + Flask API）
- [x] 準同型暗号計算API

### 短期的な改善
- [ ] より複雑な機械学習モデル（ニューラルネットワーク）
- [ ] FHIR（医療データ標準）対応
- [ ] より効率的なZKP回路
- [ ] HSM/KMS連携（鍵管理強化）

### 長期的なビジョン
- [ ] ブロックチェーンとの統合（スマートコントラクト）
- [ ] 分散型データマーケットプレイス
- [ ] Federated Learningとの統合
- [ ] zkMLの本格実装

## トラブルシューティング

### Circomのコンパイルエラー

```bash
# circomlibが見つからない場合
npm install

# 手動でcircomをインストール
npm install -g circom
```

### TenSEALのインストールエラー

```bash
# Ubuntuの場合
sudo apt-get install build-essential cmake

# macOSの場合
brew install cmake
```

### Powers of Tauが遅い

初回のセットアップは時間がかかります（5-10分程度）。
生成されたファイル（`keys/pot12_final.ptau`）は再利用されます。

## プログラミング言語の使い分け

| 言語 | 用途 | ファイル |
|------|------|----------|
| **Python** | データ生成、準同型暗号化、統計分析、ML | `python/*.py` |
| **Circom** | ZKP回路の定義 | `circuits/*.circom` |
| **JavaScript** | ZKP証明の生成・検証、回路コンパイル | `scripts/*.js` |

PythonとJavaScriptは`subprocess`を通じて連携します。

## ドキュメントのPDF変換

MarkdownドキュメントをPDFに変換できます。

### セットアップ

```bash
# 依存パッケージのインストール
npm install
```

### WSL / Linux で日本語が文字化けする場合

`md-to-pdf`（内部でChromium使用）は環境に日本語フォントが無いと文字化けします。
以下を実行してローカルにフォントを用意してください（sudo不要）:

```bash
bash scripts/ensure_pdf_fonts.sh
```

### 使い方

**すべてのドキュメントを一括変換**:

```bash
npm run pdf
```

**個別のドキュメントを変換**:

```bash
# 営業向け説明資料
npm run pdf:explain

# 共同開発提案資料
npm run pdf:explain2

# 技術仕様書
npm run pdf:techspec
```

**特定のファイルを変換**:

```bash
bash scripts/convert_to_pdf.sh docs/ZKP-DB_Explain.md
```

### 生成されるPDF

変換されたPDFは元のMarkdownファイルと同じディレクトリに生成されます：

```
docs/
├── ZKP-DB_Explain.md
├── ZKP-DB_Explain.pdf          ← 生成される
├── ZKP-DB_Explain2.md
├── ZKP-DB_Explain2.pdf         ← 生成される
├── ZKP-DB-TechSpec.md
└── ZKP-DB-TechSpec.pdf         ← 生成される
```

PDFは日本語対応、目次付き、見やすいレイアウトで生成されます。

## ライセンス

MIT License

## 参考文献

- [TenSEAL Documentation](https://github.com/OpenMined/TenSEAL)
- [Circom Documentation](https://docs.circom.io/)
- [snarkjs](https://github.com/iden3/snarkjs)
- [Zero-Knowledge Proofs: An Illustrated Primer](https://blog.cryptographyengineering.com/2014/11/27/zero-knowledge-proofs-illustrated-primer/)

## お問い合わせ

質問や提案がありましたら、Issueを作成してください。

---

**注意**: このプロジェクトは教育・研究目的のプロトタイプです。
本番環境での使用には、さらなるセキュリティ監査と最適化が必要です。
