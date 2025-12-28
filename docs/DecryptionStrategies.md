# 復号戦略 - データ購入者はどうやって計算結果を知るのか？

## 問題の所在

### 現在の仕組み

```
データ提供者（病院）
  ↓ 1. データを暗号化（秘密鍵で）
  ↓ 2. 暗号化データを販売
データ購入者（製薬会社）
  ↓ 3. 暗号化データで統計計算
  ↓ 4. 結果は暗号化されたまま
  ？ 5. 結果を知るには？
```

**課題**: 計算結果（暗号化されたまま）を復号するには秘密鍵が必要だが、秘密鍵はデータ提供者が保持している。

### なぜこうなっているのか？

**セキュリティ上の理由**:
- もし秘密鍵を購入者に渡すと、**生データも復号できてしまう**
- これではプライバシー保護の意味がない
- 秘密鍵はデータ提供者が厳重に保管する必要がある

---

## 解決策の比較

### 解決策1: 復号サービス（Decryption-as-a-Service）★推奨★

#### 概要

データ提供者が**復号サービスAPI**を提供し、購入者は計算結果のみを復号してもらう。

#### フロー

```
[データ購入者]
  1. 暗号化データで統計計算
  2. 計算結果（暗号化）を得る
     ↓ API リクエスト
[復号サービス（データ提供者が運営）]
  3. 計算結果のみを復号
  4. 結果（平文）を返す
     ↓
[データ購入者]
  5. 結果を受け取る
```

#### 実装例

**データ提供者側のAPI**:
```python
from flask import Flask, request, jsonify
import pickle
import tenseal as ts

app = Flask(__name__)

# 秘密鍵を読み込み
with open('keys/context.pkl', 'rb') as f:
    context = pickle.load(f)

@app.route('/decrypt', methods=['POST'])
def decrypt_result():
    # 購入者IDを確認（認証）
    purchaser_id = request.headers.get('X-Purchaser-ID')
    api_key = request.headers.get('X-API-Key')

    # 認証チェック
    if not verify_purchaser(purchaser_id, api_key):
        return jsonify({'error': 'Unauthorized'}), 401

    # 暗号化された計算結果を受け取る
    encrypted_result = pickle.loads(request.data)

    # 復号
    decrypted_result = encrypted_result.decrypt()

    # ログ記録（監査用）
    log_decryption_request(purchaser_id, decrypted_result)

    # 結果を返す
    return jsonify({
        'result': decrypted_result.tolist(),
        'status': 'success'
    })

if __name__ == '__main__':
    app.run(ssl_context='adhoc')  # HTTPS
```

**データ購入者側**:
```python
import requests
import pickle

# 暗号化データで計算
enc_avg = compute_encrypted_average(encrypted_data)

# 復号サービスにリクエスト
response = requests.post(
    'https://hospital.example.com/api/decrypt',
    headers={
        'X-Purchaser-ID': 'pharma_company_123',
        'X-API-Key': 'secret_api_key'
    },
    data=pickle.dumps(enc_avg)
)

# 結果を取得
result = response.json()['result']
print(f"平均値: {result[0]}")
```

#### メリット

✅ **セキュリティ**: 秘密鍵は提供者が保持
✅ **監査可能**: すべての復号リクエストをログ
✅ **課金可能**: 復号リクエスト数で課金
✅ **アクセス制御**: 不正な計算結果の復号を拒否可能
✅ **実装が容易**: 既存のAPI技術で実現

#### デメリット

❌ **リアルタイム通信が必要**: オフラインでは復号できない
❌ **提供者のサービス稼働が必要**: サーバーダウンのリスク
❌ **レイテンシ**: ネットワーク遅延が発生

#### 実用性

★★★★★ **非常に高い**

現実的で最も推奨されるアプローチ。多くのクラウドサービスと同様のモデル。

---

### 解決策2: 閾値準同型暗号（Threshold Homomorphic Encryption）

#### 概要

秘密鍵を複数の**鍵シェア**に分割し、提供者と購入者が各々保持。復号には両者の協力が必要。

#### 技術

**閾値暗号（Threshold Cryptography）**:
- 秘密鍵 $s$ を $n$ 個のシェア $s_1, s_2, \ldots, s_n$ に分割
- 復号には $t$ 個以上のシェアが必要（$t$-out-of-$n$ 方式）
- 例: 3-out-of-5（5個中3個あれば復号可能）

#### フロー

```
[セットアップ]
秘密鍵 s を分割:
  提供者: s_1
  購入者: s_2
  第三者（オプション）: s_3

[復号時]
1. 購入者が s_2 で部分復号
2. 提供者が s_1 で部分復号
3. 両方の部分復号を組み合わせて完全復号
```

#### 実装（概念）

```python
# セットアップ（秘密鍵分割）
sk = generate_secret_key()
sk_share1, sk_share2 = split_key(sk, threshold=2)

# 提供者が保持
provider_share = sk_share1

# 購入者に配布
purchaser_share = sk_share2

# 復号時
partial_decrypt1 = purchaser.partial_decrypt(enc_result, purchaser_share)
partial_decrypt2 = provider.partial_decrypt(enc_result, provider_share)

# 組み合わせて完全復号
result = combine_partial_decryptions(partial_decrypt1, partial_decrypt2)
```

#### メリット

✅ **分散信頼**: 単独では復号できない
✅ **柔軟性**: 複数の関係者で鍵を分割可能
✅ **秘密鍵漏洩に強い**: 1つのシェアが漏れても復号不可

#### デメリット

❌ **実装が複雑**: 閾値暗号の実装が難しい
❌ **通信が必要**: 復号時に協力プロトコルが必要
❌ **TenSEALは非対応**: 現在の実装では使えない

#### 実用性

★★★☆☆ **中程度**

技術的に高度。将来的な拡張として検討の価値あり。

---

### 解決策3: プロキシ再暗号化（Proxy Re-encryption）

#### 概要

データ提供者の暗号文を、プロキシが**購入者の公開鍵で再暗号化**。購入者が自分の秘密鍵で復号。

#### フロー

```
[セットアップ]
提供者の鍵ペア: (pk_provider, sk_provider)
購入者の鍵ペア: (pk_purchaser, sk_purchaser)
再暗号化鍵: rk = generate_re_key(sk_provider, pk_purchaser)

[データ暗号化]
提供者: c = Encrypt(data, pk_provider)

[プロキシ再暗号化]
プロキシ: c' = ReEncrypt(c, rk)
  ↓ c' は pk_purchaser で暗号化された暗号文

[購入者が復号]
購入者: data = Decrypt(c', sk_purchaser)
```

#### メリット

✅ **購入者が独立して復号可能**: 提供者への通信不要
✅ **プロキシは生データを見られない**: 再暗号化のみ

#### デメリット

❌ **準同型暗号との組み合わせが困難**: CKKSは非対応
❌ **再暗号化後は準同型性を失う**: 計算できなくなる
❌ **実装が存在しない**: TenSEALでは不可能

#### 実用性

★☆☆☆☆ **低い**

準同型暗号との組み合わせは研究段階。実用化は困難。

---

### 解決策4: ハイブリッドアプローチ

#### 概要

**集計結果**は暗号化せず、**個別データ**のみ準同型暗号で保護。

#### フロー

```
[データ提供者]
1. 個別患者データを暗号化
2. 集計結果（平均など）は平文で計算し、デジタル署名

[データ購入者]
3. 暗号化データで詳細分析（個別データアクセスは不可）
4. 集計結果は直接利用可能（署名で正当性確認）
```

#### 実装

**提供者側**:
```python
# 個別データは暗号化
encrypted_data = [encrypt(patient) for patient in patients]

# 集計結果は平文で計算し、署名
summary_stats = {
    'average_age': np.mean([p['age'] for p in patients]),
    'average_bp': np.mean([p['bp'] for p in patients])
}

# デジタル署名
signature = sign(summary_stats, private_key)

# 提供
provide_to_purchaser(encrypted_data, summary_stats, signature)
```

**購入者側**:
```python
# 集計結果を直接利用
verify_signature(summary_stats, signature, public_key)
print(f"平均年齢: {summary_stats['average_age']}")

# 詳細分析が必要な場合は暗号化データで計算 → 復号サービスへ
```

#### メリット

✅ **実用的**: ほとんどのユースケースをカバー
✅ **効率的**: 平文計算は高速
✅ **柔軟性**: 用途に応じて使い分け

#### デメリット

❌ **集計結果の柔軟性が低い**: 事前定義された統計のみ
❌ **カスタム計算には不向き**: 新しい分析は復号サービス経由

#### 実用性

★★★★☆ **高い**

多くのユースケースで十分。コストパフォーマンスが良い。

---

### 解決策5: 計算結果の事前定義（プリコンピューテーション）

#### 概要

購入者が実行できる**計算を事前に定義**し、その結果のみ提供。

#### フロー

```
[契約時]
購入者: 「平均年齢、平均血圧、相関係数を計算したい」
提供者: 「了解しました。これらの結果を提供します」

[データ提供]
提供者:
  1. 暗号化データ（詳細分析用）
  2. 事前計算された統計（平文）

を提供

[購入者]
必要な統計は直接利用
追加の計算は復号サービス経由でリクエスト
```

#### メリット

✅ **シンプル**: 技術的複雑性が低い
✅ **コスト効率**: 事前計算で無駄がない

#### デメリット

❌ **柔軟性がない**: 予期しない分析には対応困難

#### 実用性

★★★☆☆ **中程度**

限定的なユースケースに有効。

---

## 推奨アーキテクチャ

### ベストプラクティス: 復号サービス + ハイブリッドアプローチ

```
┌─────────────────────────────────────────────────────────┐
│            データ提供者（病院）                          │
│                                                         │
│  ┌──────────────┐        ┌──────────────┐              │
│  │ 暗号化データ │        │  集計結果    │              │
│  │ (個別患者)   │        │  (平文+署名) │              │
│  └──────┬───────┘        └──────┬───────┘              │
│         │                       │                      │
│         │   ┌───────────────────┴───────────────┐      │
│         │   │  復号サービスAPI                   │      │
│         │   │  - 認証・認可                      │      │
│         │   │  - ログ記録                        │      │
│         │   │  - レート制限                      │      │
│         │   │  - 課金                            │      │
│         │   └───────────────────┬───────────────┘      │
└─────────┼───────────────────────┼─────────────────────┘
          │                       │
          ▼                       ▼
┌─────────────────────────────────────────────────────────┐
│         データ購入者（製薬会社）                         │
│                                                         │
│  ┌────────────────┐    ┌────────────────────────┐      │
│  │ 基本的な統計   │    │ 詳細分析                │      │
│  │ （集計結果利用）│    │ （暗号化データで計算）  │      │
│  └────────────────┘    └───────┬────────────────┘      │
│                                │                        │
│                                │ 計算結果（暗号化）      │
│                                ▼                        │
│                        ┌───────────────┐                │
│                        │ 復号リクエスト │                │
│                        │ （APIコール）  │                │
│                        └───────────────┘                │
└─────────────────────────────────────────────────────────┘
```

### 実装例

#### 1. データ提供時

```python
# 提供者側
def prepare_data_package(patients):
    # 個別データを暗号化
    encrypted_data = encrypt_patients(patients)

    # 基本的な集計結果を計算
    summary_stats = {
        'count': len(patients),
        'average_age': np.mean([p['age'] for p in patients]),
        'average_bp_systolic': np.mean([p['bp_sys'] for p in patients]),
        'std_age': np.std([p['age'] for p in patients]),
        'percentiles_age': np.percentile([p['age'] for p in patients], [25, 50, 75])
    }

    # 署名
    signature = sign(summary_stats, private_key)

    return {
        'encrypted_data': encrypted_data,
        'summary_stats': summary_stats,
        'signature': signature,
        'decryption_api_endpoint': 'https://hospital.example.com/api/decrypt',
        'api_documentation': 'https://hospital.example.com/api/docs'
    }
```

#### 2. 購入者の利用

```python
# 購入者側
data_package = download_from_marketplace(dataset_id='medical_dataset_001')

# 基本統計は直接利用
verify_signature(data_package['summary_stats'], data_package['signature'])
print(f"患者数: {data_package['summary_stats']['count']}")
print(f"平均年齢: {data_package['summary_stats']['average_age']:.1f}歳")

# カスタム分析が必要な場合
enc_result = compute_custom_statistic(data_package['encrypted_data'])

# 復号サービスにリクエスト
decrypted_result = request_decryption(
    endpoint=data_package['decryption_api_endpoint'],
    encrypted_result=enc_result,
    api_key=my_api_key
)

print(f"カスタム統計結果: {decrypted_result}")
```

---

## 課金モデル

### 復号サービスの課金

```python
# 料金体系の例
pricing = {
    'base_dataset': 10000,  # USD
    'decryption_requests': {
        'tier1': {  # 0-100リクエスト
            'price_per_request': 10,
            'included_in_base': 10
        },
        'tier2': {  # 101-1000リクエスト
            'price_per_request': 5
        },
        'tier3': {  # 1001+リクエスト
            'price_per_request': 2
        }
    }
}
```

### ビジネスモデル

**データ提供者の収益**:
1. データセット販売: 基本料金
2. 復号リクエスト: 従量課金
3. プレミアムサポート: 高速レスポンス

**購入者のコスト**:
1. 初期費用: データセット購入
2. 運用コスト: 復号リクエスト料金
3. 最適化のインセンティブ: 無駄な計算を減らす

---

## セキュリティ上の重大な脆弱性と防御メカニズム

### 🚨 脆弱性: 個別データ復号攻撃

#### 問題点

現在の設計では、データ購入者が以下のような攻撃を行える可能性があります：

```python
# ❌ 脆弱な使い方の例
# 購入者が個別患者データを1件ずつ復号依頼

for patient_id in range(1, 101):
    # 患者IDを指定して年齢を取得
    enc_age = encrypted_data.filter(id=patient_id).get_age()
    age = request_decryption(enc_age)  # 課金して復号

    # 血圧を取得
    enc_bp = encrypted_data.filter(id=patient_id).get_bp()
    bp = request_decryption(enc_bp)  # 課金して復号

    # 結果: すべての個別データを取得できてしまう
    print(f"患者{patient_id}: {age}歳, {bp}mmHg")
```

**結果**: 課金さえすれば、全ての患者の生データを復元可能。暗号化の意味がなくなります。

---

### ✅ 防御メカニズム

#### 1. **集約統計のみ許可** ★最重要★

個別患者データの復号は**一切許可せず**、集約統計（平均、合計、標準偏差など）のみ復号可能にする。

**実装例**:

```python
from flask import Flask, request, jsonify
import pickle
import tenseal as ts
import numpy as np

app = Flask(__name__)

# 秘密鍵を読み込み
with open('keys/context.pkl', 'rb') as f:
    context = pickle.load(f)

@app.route('/decrypt', methods=['POST'])
def decrypt_result():
    purchaser_id = request.headers.get('X-Purchaser-ID')
    api_key = request.headers.get('X-API-Key')

    # 認証チェック
    if not verify_purchaser(purchaser_id, api_key):
        return jsonify({'error': 'Unauthorized'}), 401

    # 暗号化された計算結果を受け取る
    request_data = request.get_json()
    encrypted_result = pickle.loads(bytes.fromhex(request_data['encrypted_data']))
    query_metadata = request_data['metadata']

    # ✅ セキュリティチェック1: 集約統計かどうか確認
    if not is_aggregate_query(query_metadata):
        return jsonify({
            'error': 'Individual data decryption not allowed',
            'message': 'Only aggregate statistics can be decrypted'
        }), 403

    # ✅ セキュリティチェック2: k-匿名性チェック
    sample_size = query_metadata.get('sample_size', 0)
    MIN_K = 10  # 最低10人のデータを含む必要がある

    if sample_size < MIN_K:
        return jsonify({
            'error': 'k-anonymity violation',
            'message': f'Query must include at least {MIN_K} individuals',
            'provided': sample_size
        }), 403

    # ✅ セキュリティチェック3: クエリ監査（類似クエリ検出）
    if detect_reconstruction_attack(purchaser_id, query_metadata):
        return jsonify({
            'error': 'Potential data reconstruction attack detected',
            'message': 'Too many similar queries detected'
        }), 403

    # 復号
    decrypted_result = encrypted_result.decrypt()

    # ✅ セキュリティチェック4: 差分プライバシーノイズ追加
    noisy_result = add_differential_privacy_noise(
        decrypted_result,
        epsilon=query_metadata.get('privacy_budget', 1.0)
    )

    # ログ記録（監査用）
    log_decryption_request(
        purchaser_id=purchaser_id,
        query_metadata=query_metadata,
        result=noisy_result,
        timestamp=datetime.now()
    )

    # 結果を返す
    return jsonify({
        'result': noisy_result.tolist(),
        'sample_size': sample_size,
        'privacy_epsilon': query_metadata.get('privacy_budget', 1.0),
        'status': 'success'
    })

def is_aggregate_query(metadata):
    """集約統計かどうかをチェック"""
    allowed_operations = [
        'mean', 'average', 'sum', 'std', 'variance',
        'median', 'percentile', 'correlation', 'regression'
    ]

    operation = metadata.get('operation', '')
    return operation in allowed_operations

def detect_reconstruction_attack(purchaser_id, query_metadata):
    """データ再構成攻撃を検出"""
    # 過去24時間のクエリ履歴を取得
    recent_queries = get_recent_queries(purchaser_id, hours=24)

    # 類似クエリの数をカウント
    similar_queries = 0
    for past_query in recent_queries:
        if queries_are_similar(past_query, query_metadata):
            similar_queries += 1

    # 閾値を超えたら攻撃の可能性
    SIMILARITY_THRESHOLD = 5
    return similar_queries > SIMILARITY_THRESHOLD

def queries_are_similar(query1, query2, threshold=0.8):
    """2つのクエリが類似しているかチェック"""
    # フィルタ条件の重複度を計算
    filters1 = set(query1.get('filters', {}).items())
    filters2 = set(query2.get('filters', {}).items())

    if not filters1 or not filters2:
        return False

    intersection = len(filters1 & filters2)
    union = len(filters1 | filters2)

    jaccard_similarity = intersection / union
    return jaccard_similarity > threshold

def add_differential_privacy_noise(result, epsilon=1.0):
    """差分プライバシーノイズを追加"""
    # Laplace mechanism
    sensitivity = 1.0  # データ感度（データセット依存）
    scale = sensitivity / epsilon

    noise = np.random.laplace(0, scale, size=result.shape)
    return result + noise

if __name__ == '__main__':
    app.run(ssl_context='adhoc')  # HTTPS
```

#### 2. **メタデータの必須提出**

購入者は復号リクエスト時に、クエリのメタデータを提出する必要があります。

```python
# 購入者側の実装例

# ✅ 正しい使い方
def compute_average_age_by_gender(encrypted_data, gender):
    # フィルタリングして平均を計算（暗号化されたまま）
    filtered_data = encrypted_data.filter(gender=gender)
    enc_avg = filtered_data.compute_average('age')

    # メタデータを準備
    metadata = {
        'operation': 'mean',
        'field': 'age',
        'filters': {'gender': gender},
        'sample_size': filtered_data.count(),  # 重要: サンプルサイズ
        'privacy_budget': 1.0
    }

    # 復号リクエスト
    result = request_decryption(
        encrypted_result=enc_avg,
        metadata=metadata,
        api_key=my_api_key
    )

    return result

# 使用例
avg_age_male = compute_average_age_by_gender(encrypted_data, 'male')
print(f"男性の平均年齢: {avg_age_male:.1f}歳")
```

#### 3. **k-匿名性の強制**

すべてのクエリは最低 $k$ 人（例: $k=10$）のデータを含む必要があります。

```python
# k-匿名性チェックの詳細実装

def enforce_k_anonymity(query_metadata, min_k=10):
    """
    k-匿名性を強制

    Args:
        query_metadata: クエリのメタデータ
        min_k: 最小のk値（デフォルト10）

    Returns:
        bool: k-匿名性を満たす場合True
    """
    sample_size = query_metadata.get('sample_size', 0)

    if sample_size < min_k:
        raise ValueError(
            f"k-anonymity violation: Query includes only {sample_size} individuals, "
            f"minimum {min_k} required."
        )

    return True

# 適用例
MIN_K = 10  # 病院のプライバシーポリシーで定義

# ❌ 拒否される例
metadata_bad = {
    'operation': 'mean',
    'field': 'age',
    'filters': {'patient_id': 'P0001'},  # 1人だけ
    'sample_size': 1
}
# → エラー: k-anonymity violation

# ✅ 許可される例
metadata_good = {
    'operation': 'mean',
    'field': 'age',
    'filters': {'gender': 'male', 'age_range': '40-50'},
    'sample_size': 23  # 23人含む
}
# → OK
```

#### 4. **差分プライバシー**

復号結果にノイズを加えて、個別データの推測を防止します。

**差分プライバシーの数学的定義**:

メカニズム $\mathcal{M}$ が $\epsilon$-差分プライバシーを満たす ⇔

$$
\Pr[\mathcal{M}(D) \in S] \leq e^\epsilon \cdot \Pr[\mathcal{M}(D') \in S]
$$

任意のデータセット $D, D'$（1レコードのみ異なる）と任意の出力集合 $S$ について。

**実装**:

```python
def add_laplace_noise(value, sensitivity, epsilon):
    """
    Laplace機構で差分プライバシーノイズを追加

    Args:
        value: 真の値
        sensitivity: データ感度（1レコード変更時の最大変化量）
        epsilon: プライバシーバジェット（小さいほど高いプライバシー）

    Returns:
        ノイズ付き値
    """
    scale = sensitivity / epsilon
    noise = np.random.laplace(0, scale)
    return value + noise

# 例: 平均年齢の計算
true_avg_age = 55.2
sensitivity = (120 - 0) / 100  # (最大年齢 - 最小年齢) / データ数
epsilon = 1.0  # プライバシーバジェット

noisy_avg_age = add_laplace_noise(true_avg_age, sensitivity, epsilon)
print(f"真の平均年齢: {true_avg_age:.1f}歳")
print(f"ノイズ付き: {noisy_avg_age:.1f}歳")
# 出力例: "真の平均年齢: 55.2歳"
#         "ノイズ付き: 55.7歳"  ← わずかにずれている
```

**プライバシーバジェットの管理**:

```python
class PrivacyBudgetManager:
    """購入者ごとのプライバシーバジェットを管理"""

    def __init__(self, total_budget=10.0):
        self.total_budget = total_budget
        self.used_budget = {}

    def check_budget(self, purchaser_id, required_epsilon):
        """バジェットが十分か確認"""
        used = self.used_budget.get(purchaser_id, 0.0)
        remaining = self.total_budget - used

        if required_epsilon > remaining:
            raise ValueError(
                f"Privacy budget exceeded. "
                f"Required: {required_epsilon}, Remaining: {remaining:.2f}"
            )

        return True

    def consume_budget(self, purchaser_id, epsilon):
        """バジェットを消費"""
        if purchaser_id not in self.used_budget:
            self.used_budget[purchaser_id] = 0.0

        self.used_budget[purchaser_id] += epsilon

    def get_remaining_budget(self, purchaser_id):
        """残りバジェットを取得"""
        used = self.used_budget.get(purchaser_id, 0.0)
        return self.total_budget - used

# 使用例
budget_manager = PrivacyBudgetManager(total_budget=10.0)

# クエリ1: epsilon=1.0
budget_manager.check_budget('pharma_123', 1.0)  # OK
budget_manager.consume_budget('pharma_123', 1.0)

# クエリ2: epsilon=1.0
budget_manager.check_budget('pharma_123', 1.0)  # OK
budget_manager.consume_budget('pharma_123', 1.0)

# ... 8回クエリ実行後 ...

# クエリ11: epsilon=1.0
budget_manager.check_budget('pharma_123', 1.0)  # エラー: バジェット超過
```

#### 5. **クエリ監査システム**

類似したクエリを繰り返すことで、データ再構成攻撃を行う可能性を検出します。

```python
class QueryAuditor:
    """クエリを監査してデータ再構成攻撃を検出"""

    def __init__(self, similarity_threshold=5, time_window_hours=24):
        self.similarity_threshold = similarity_threshold
        self.time_window_hours = time_window_hours
        self.query_log = []

    def audit_query(self, purchaser_id, query_metadata):
        """
        クエリを監査

        Returns:
            bool: 安全な場合True、攻撃の可能性がある場合False
        """
        # 最近のクエリを取得
        recent_queries = self._get_recent_queries(
            purchaser_id,
            hours=self.time_window_hours
        )

        # 類似クエリをカウント
        similar_count = sum(
            1 for q in recent_queries
            if self._queries_similar(q['metadata'], query_metadata)
        )

        # 閾値チェック
        if similar_count > self.similarity_threshold:
            self._log_alert(
                purchaser_id,
                f"Potential reconstruction attack: {similar_count} similar queries"
            )
            return False

        # クエリをログに記録
        self._log_query(purchaser_id, query_metadata)
        return True

    def _queries_similar(self, q1, q2, threshold=0.8):
        """Jaccard類似度で判定"""
        filters1 = set(str(q1.get('filters', {})).split())
        filters2 = set(str(q2.get('filters', {})).split())

        if not filters1 or not filters2:
            return False

        intersection = len(filters1 & filters2)
        union = len(filters1 | filters2)

        return (intersection / union) > threshold

    def _get_recent_queries(self, purchaser_id, hours):
        """指定時間内のクエリを取得"""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [
            q for q in self.query_log
            if q['purchaser_id'] == purchaser_id and q['timestamp'] > cutoff
        ]

    def _log_query(self, purchaser_id, metadata):
        """クエリをログに記録"""
        self.query_log.append({
            'purchaser_id': purchaser_id,
            'metadata': metadata,
            'timestamp': datetime.now()
        })

    def _log_alert(self, purchaser_id, message):
        """アラートを記録"""
        print(f"🚨 SECURITY ALERT [{purchaser_id}]: {message}")
        # 実際の実装ではセキュリティチームに通知

# 使用例
auditor = QueryAuditor(similarity_threshold=5, time_window_hours=24)

# クエリ1
metadata1 = {'operation': 'mean', 'field': 'age', 'filters': {'gender': 'male'}}
auditor.audit_query('pharma_123', metadata1)  # OK

# クエリ2（類似）
metadata2 = {'operation': 'mean', 'field': 'age', 'filters': {'gender': 'male', 'age': '>40'}}
auditor.audit_query('pharma_123', metadata2)  # OK

# ... 類似クエリを6回繰り返す ...

# クエリ7（類似）
metadata7 = {'operation': 'mean', 'field': 'age', 'filters': {'gender': 'male', 'age': '>45'}}
auditor.audit_query('pharma_123', metadata7)  # False（攻撃検出）
```

#### 6. **レート制限**

短時間に大量のクエリを実行することを防止します。

```python
from collections import defaultdict
from datetime import datetime, timedelta

class RateLimiter:
    """API呼び出しのレート制限"""

    def __init__(self, max_requests=100, time_window_minutes=60):
        self.max_requests = max_requests
        self.time_window = timedelta(minutes=time_window_minutes)
        self.request_log = defaultdict(list)

    def allow_request(self, purchaser_id):
        """リクエストを許可するか判定"""
        now = datetime.now()
        cutoff = now - self.time_window

        # 古いリクエストを削除
        self.request_log[purchaser_id] = [
            timestamp for timestamp in self.request_log[purchaser_id]
            if timestamp > cutoff
        ]

        # リクエスト数をチェック
        if len(self.request_log[purchaser_id]) >= self.max_requests:
            return False

        # リクエストを記録
        self.request_log[purchaser_id].append(now)
        return True

    def get_remaining_requests(self, purchaser_id):
        """残りリクエスト数を取得"""
        now = datetime.now()
        cutoff = now - self.time_window

        recent_requests = [
            ts for ts in self.request_log[purchaser_id]
            if ts > cutoff
        ]

        return self.max_requests - len(recent_requests)

# 使用例
rate_limiter = RateLimiter(max_requests=100, time_window_minutes=60)

# APIエンドポイントで使用
@app.route('/decrypt', methods=['POST'])
def decrypt_result():
    purchaser_id = request.headers.get('X-Purchaser-ID')

    # レート制限チェック
    if not rate_limiter.allow_request(purchaser_id):
        remaining = rate_limiter.get_remaining_requests(purchaser_id)
        return jsonify({
            'error': 'Rate limit exceeded',
            'message': f'Maximum {rate_limiter.max_requests} requests per hour',
            'remaining_requests': remaining,
            'retry_after': 3600  # 秒
        }), 429

    # ... 通常の処理 ...
```

---

### 📋 セキュリティチェックリスト

復号サービスAPIは以下のチェックをすべて実施する必要があります：

- [ ] **認証・認可**: API keyの検証
- [ ] **集約統計のみ許可**: 個別データ復号を拒否
- [ ] **k-匿名性チェック**: 最低k人のデータを含むか確認
- [ ] **差分プライバシー**: 結果にノイズ追加
- [ ] **プライバシーバジェット管理**: 累積プライバシー損失を追跡
- [ ] **クエリ監査**: 類似クエリによる再構成攻撃を検出
- [ ] **レート制限**: 短時間の大量クエリを防止
- [ ] **ログ記録**: すべてのリクエストを監査ログに記録
- [ ] **アラート**: 異常なパターンをセキュリティチームに通知

---

### 🎯 実装例: 完全版セキュアAPI

```python
from flask import Flask, request, jsonify
from datetime import datetime
import pickle
import tenseal as ts
import numpy as np

app = Flask(__name__)

# セキュリティコンポーネント
budget_manager = PrivacyBudgetManager(total_budget=10.0)
auditor = QueryAuditor(similarity_threshold=5, time_window_hours=24)
rate_limiter = RateLimiter(max_requests=100, time_window_minutes=60)

# 秘密鍵
with open('keys/context.pkl', 'rb') as f:
    context = pickle.load(f)

@app.route('/decrypt', methods=['POST'])
def decrypt_result():
    """セキュアな復号API"""

    # === 1. 認証 ===
    purchaser_id = request.headers.get('X-Purchaser-ID')
    api_key = request.headers.get('X-API-Key')

    if not verify_purchaser(purchaser_id, api_key):
        return jsonify({'error': 'Unauthorized'}), 401

    # === 2. レート制限 ===
    if not rate_limiter.allow_request(purchaser_id):
        return jsonify({
            'error': 'Rate limit exceeded',
            'remaining_requests': rate_limiter.get_remaining_requests(purchaser_id)
        }), 429

    # === 3. リクエストデータ取得 ===
    request_data = request.get_json()
    encrypted_result = pickle.loads(bytes.fromhex(request_data['encrypted_data']))
    metadata = request_data['metadata']

    # === 4. 集約統計チェック ===
    if not is_aggregate_query(metadata):
        return jsonify({'error': 'Individual data decryption not allowed'}), 403

    # === 5. k-匿名性チェック ===
    sample_size = metadata.get('sample_size', 0)
    MIN_K = 10
    if sample_size < MIN_K:
        return jsonify({
            'error': 'k-anonymity violation',
            'required_minimum': MIN_K,
            'provided': sample_size
        }), 403

    # === 6. クエリ監査 ===
    if not auditor.audit_query(purchaser_id, metadata):
        return jsonify({'error': 'Potential data reconstruction attack detected'}), 403

    # === 7. プライバシーバジェットチェック ===
    epsilon = metadata.get('privacy_budget', 1.0)
    try:
        budget_manager.check_budget(purchaser_id, epsilon)
    except ValueError as e:
        return jsonify({
            'error': 'Privacy budget exceeded',
            'message': str(e),
            'remaining_budget': budget_manager.get_remaining_budget(purchaser_id)
        }), 403

    # === 8. 復号 ===
    decrypted_result = encrypted_result.decrypt()

    # === 9. 差分プライバシーノイズ追加 ===
    sensitivity = calculate_sensitivity(metadata)
    noisy_result = add_laplace_noise(decrypted_result, sensitivity, epsilon)

    # === 10. バジェット消費 ===
    budget_manager.consume_budget(purchaser_id, epsilon)

    # === 11. ログ記録 ===
    log_decryption_request(
        purchaser_id=purchaser_id,
        metadata=metadata,
        result=noisy_result,
        epsilon=epsilon,
        timestamp=datetime.now()
    )

    # === 12. 結果返却 ===
    return jsonify({
        'result': noisy_result.tolist(),
        'sample_size': sample_size,
        'privacy_epsilon': epsilon,
        'remaining_budget': budget_manager.get_remaining_budget(purchaser_id),
        'status': 'success'
    })

if __name__ == '__main__':
    app.run(ssl_context='adhoc')
```

---

## まとめ

### 結論

**毎回データ提供者にアクセスする必要がある** が、これは**意図的な設計**です。

### 理由

1. **セキュリティ**: 秘密鍵を共有すると生データも復号可能になる
2. **監査**: すべての復号リクエストをログ記録
3. **アクセス制御**: 不正な利用を防止
4. **課金**: 利用量に応じた課金が可能

### ⚠️ 重要: 個別データ復号攻撃への対策

**脆弱性**: 課金しながら個別患者データを1件ずつ復号依頼すれば、全ての生データを取得可能

**必須の防御メカニズム**:

1. ✅ **集約統計のみ許可**: 個別データ復号を拒否
2. ✅ **k-匿名性チェック**: 最低k人（例: 10人）のデータを含むクエリのみ許可
3. ✅ **差分プライバシー**: 復号結果にノイズを追加
4. ✅ **クエリ監査**: 類似クエリによるデータ再構成攻撃を検出
5. ✅ **レート制限**: 短時間の大量クエリを防止
6. ✅ **プライバシーバジェット管理**: 累積プライバシー損失を追跡

**セキュリティチェックリスト**:
- [ ] 認証・認可
- [ ] 集約統計のみ許可
- [ ] k-匿名性チェック
- [ ] 差分プライバシー
- [ ] プライバシーバジェット管理
- [ ] クエリ監査
- [ ] レート制限
- [ ] ログ記録
- [ ] アラート

### 実用性の担保

✅ **復号サービスAPI**: HTTP/REST APIで簡単にアクセス
✅ **低レイテンシ**: 数十〜数百ミリ秒で復号
✅ **スケーラビリティ**: クラウドで自動スケール
✅ **高可用性**: 99.9%以上のアップタイム
✅ **セキュリティ**: 多層防御で個別データ復号攻撃を防止

### 最終的な推奨

**復号サービス（DaaS: Decryption-as-a-Service）+ ハイブリッドアプローチ + 多層セキュリティ**

#### データ提供

- 基本統計: 事前計算して提供（平文+署名）
- カスタム分析: 暗号化データで計算 → 復号サービスで復号

#### セキュリティ対策

1. **集約統計のみ復号可能**: 個別データは復号不可
2. **k-匿名性の強制**: 最低10人のデータを含む統計のみ
3. **差分プライバシー**: 復号結果にLaplaceノイズ追加
4. **クエリ監査**: 類似クエリを検出してデータ再構成攻撃を防止
5. **レート制限**: 1時間あたり100リクエストまで
6. **プライバシーバジェット**: 累積epsilon=10.0まで

#### ビジネス価値

- **セキュリティ**: プライバシー保護の完全性を担保
- **実用性**: 統計分析に必要な機能を提供
- **コスト効率**: 事前計算統計で無駄な復号を削減
- **監査可能性**: すべての復号リクエストをログ記録
- **課金モデル**: 利用量に応じた従量課金

これにより、**プライバシー保護、実用性、セキュリティ**の三位一体が実現できます。
