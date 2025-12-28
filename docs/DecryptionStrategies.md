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

## まとめ

### 結論

**毎回データ提供者にアクセスする必要がある** が、これは**意図的な設計**です。

### 理由

1. **セキュリティ**: 秘密鍵を共有すると生データも復号可能になる
2. **監査**: すべての復号リクエストをログ記録
3. **アクセス制御**: 不正な利用を防止
4. **課金**: 利用量に応じた課金が可能

### 実用性の担保

✅ **復号サービスAPI**: HTTP/REST APIで簡単にアクセス
✅ **低レイテンシ**: 数十〜数百ミリ秒で復号
✅ **スケーラビリティ**: クラウドで自動スケール
✅ **高可用性**: 99.9%以上のアップタイム

### 最終的な推奨

**復号サービス（DaaS: Decryption-as-a-Service）+ ハイブリッドアプローチ**

- 基本統計: 事前計算して提供（平文+署名）
- カスタム分析: 暗号化データで計算 → 復号サービスで復号
- セキュリティ、実用性、コスト効率のバランスが最良

これにより、プライバシー保護と実用性の両立が実現できます。
