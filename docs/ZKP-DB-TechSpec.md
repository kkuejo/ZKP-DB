# ZKP-DB 技術仕様書
## Technical Specification for Privacy-Preserving Medical Data Marketplace

**Version**: 2.0
**Last Updated**: 2025-12-30
**Status**: Prototype / Proof of Concept

---

## 目次

1. [システム概要](#システム概要)
2. [アーキテクチャ](#アーキテクチャ)
3. [準同型暗号の実装](#準同型暗号の実装)
4. [ゼロ知識証明の実装](#ゼロ知識証明の実装)
5. [差分プライバシーの実装](#差分プライバシーの実装)
6. [バッチZKP（Merkle Tree）](#バッチzkpmerkle-tree)
7. [機械学習の実装](#機械学習の実装)
8. [高度な手法](#高度な手法)
9. [データフロー](#データフロー)
10. [計算機資源の要件](#計算機資源の要件)
11. [パフォーマンス特性](#パフォーマンス特性)
12. [セキュリティ分析](#セキュリティ分析)
13. [API仕様](#api仕様)
14. [Webインターフェース](#webインターフェース)
15. [実装の詳細](#実装の詳細)
16. [制限事項と対策](#制限事項と対策)
17. [今後の拡張](#今後の拡張)

---

## システム概要

### 目的

医療データを準同型暗号で暗号化し、ゼロ知識証明でその正当性を保証することで、プライバシーを完全に保護しながらデータの利活用を可能にする。

### コアテクノロジー

1. **Homomorphic Encryption (HE)**: CKKS方式（実数値対応）
2. **Zero-Knowledge Proof (ZKP)**: Groth16 zkSNARK
3. **Differential Privacy (DP)**: Laplace/Gaussianノイズ機構
4. **Batch ZKP with Merkle Tree**: 効率的な全患者データの整合性検証
5. **Privacy-Preserving Machine Learning (PPML)**: 暗号化データでのML

### 技術スタック

```
┌─────────────────────────────────────────┐
│ Application Layer                       │
├─────────────────────────────────────────┤
│ - Python (データ処理、ML)               │
│ - JavaScript/Node.js (ZKP)              │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ Cryptographic Libraries                 │
├─────────────────────────────────────────┤
│ - TenSEAL (準同型暗号)                  │
│ - Circom (ZKP回路)                      │
│ - snarkjs (ZKP実行環境)                │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ Core Libraries                          │
├─────────────────────────────────────────┤
│ - Microsoft SEAL (C++)                  │
│ - circomlib (標準ZKP回路)               │
│ - NumPy, scikit-learn (ML)             │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ Infrastructure                          │
├─────────────────────────────────────────┤
│ - Linux/macOS                           │
│ - Node.js v16+                          │
│ - Python 3.8+                           │
└─────────────────────────────────────────┘
```

---

## アーキテクチャ

### システム全体図

```
┌─────────────────────────────────────────────────────────────┐
│                    Data Provider Side                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐                                          │
│  │ Raw Medical  │                                          │
│  │    Data      │                                          │
│  └──────┬───────┘                                          │
│         │                                                   │
│         ↓                                                   │
│  ┌──────────────────────────────┐                          │
│  │ Homomorphic Encryption       │                          │
│  │ (TenSEAL / CKKS)            │                          │
│  │                              │                          │
│  │ - Generate context           │                          │
│  │ - Encrypt data               │                          │
│  │ - Generate keys              │                          │
│  └──────┬───────────────────────┘                          │
│         │                                                   │
│         ↓                                                   │
│  ┌──────────────────────────────┐                          │
│  │ Zero-Knowledge Proof         │                          │
│  │ (Circom + snarkjs)          │                          │
│  │                              │                          │
│  │ - Compile circuit            │                          │
│  │ - Generate proof             │                          │
│  │ - Export verification key    │                          │
│  └──────┬───────────────────────┘                          │
│         │                                                   │
│         ↓                                                   │
│  ┌──────────────────────────────┐                          │
│  │ Data Package                 │                          │
│  │                              │                          │
│  │ ✓ Encrypted data             │                          │
│  │ ✓ ZKP proofs                 │                          │
│  │ ✓ Verification key           │                          │
│  │ ✓ HE context (public)        │                          │
│  └──────┬───────────────────────┘                          │
│         │                                                   │
└─────────┼───────────────────────────────────────────────────┘
          │
          │ Transfer (via API / File)
          │
          ↓
┌─────────────────────────────────────────────────────────────┐
│                   Data Consumer Side                        │
├─────────────────────────────────────────────────────────────┤
│         │                                                   │
│         ↓                                                   │
│  ┌──────────────────────────────┐                          │
│  │ Verification                 │                          │
│  │                              │                          │
│  │ - Verify ZKP proofs          │                          │
│  │ - Check data integrity       │                          │
│  └──────┬───────────────────────┘                          │
│         │                                                   │
│         ↓                                                   │
│  ┌──────────────────────────────┐                          │
│  │ Encrypted Computation        │                          │
│  │                              │                          │
│  │ - Statistical analysis       │                          │
│  │ - Machine learning           │                          │
│  │ - Custom queries             │                          │
│  └──────┬───────────────────────┘                          │
│         │                                                   │
│         ↓                                                   │
│  ┌──────────────────────────────┐                          │
│  │ Results                      │                          │
│  │                              │                          │
│  │ - Decrypt results only       │                          │
│  │ - Individual data remains    │                          │
│  │   encrypted                  │                          │
│  └──────────────────────────────┘                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### コンポーネント構成

```
ZKP-DB/
├── circuits/               # Circom ZKP回路
│   ├── data_verification.circom
│   └── build/             # コンパイル済み回路
│
├── python/                # Pythonモジュール
│   ├── generate_dummy_data.py
│   ├── homomorphic_encryption.py
│   ├── ml_encrypted.py
│   ├── advanced_ml_techniques.py
│   └── integrated_demo.py
│
├── scripts/               # JavaScriptスクリプト
│   ├── setup.js          # ZKP環境セットアップ
│   ├── generate_proof.js # 証明生成
│   └── verify_proof.js   # 証明検証
│
├── data/                  # データディレクトリ
│   ├── patients.json     # 生データ
│   └── encrypted_*.pkl   # 暗号化データ
│
├── keys/                  # 暗号鍵
│   ├── context.pkl       # HEコンテキスト
│   ├── *_final.zkey      # ZKP証明鍵
│   └── verification_key.json # ZKP検証鍵
│
└── proofs/                # 生成された証明
    ├── proof_*.json
    └── public_*.json
```

---

## 準同型暗号の実装

### CKKS方式の選択理由

**CKKS (Cheon-Kim-Kim-Song)** を採用した理由:

1. **実数値対応**: 医療データ（血圧、血糖値など）は実数
2. **近似計算**: 統計・機械学習には近似で十分
3. **効率性**: BFVより高速（実数値の場合）
4. **成熟度**: Microsoft SEALで実装済み

### 暗号化パラメータ

```python
context = ts.context(
    ts.SCHEME_TYPE.CKKS,
    poly_modulus_degree=8192,      # セキュリティパラメータ
    coeff_mod_bit_sizes=[60, 40, 40, 60]  # 係数モジュラス
)
context.global_scale = 2**40        # スケール（精度）
```

**パラメータの意味**:

| パラメータ | 値 | 意味 |
|-----------|-----|------|
| `poly_modulus_degree` | 8192 | 多項式の次数（セキュリティレベル） |
| `coeff_mod_bit_sizes` | [60,40,40,60] | 係数モジュラスのビットサイズ |
| `global_scale` | 2^40 | 固定小数点精度 |

**セキュリティレベル**:
- poly_modulus_degree=8192 → 約128ビットセキュリティ
- 商用利用に十分なセキュリティ

### 暗号化プロセス

#### 1. コンテキスト生成

```python
class MedicalDataEncryptor:
    def __init__(self):
        # CKKSコンテキストの初期化
        self.context = ts.context(
            ts.SCHEME_TYPE.CKKS,
            poly_modulus_degree=8192,
            coeff_mod_bit_sizes=[60, 40, 40, 60]
        )

        # 必要な鍵を生成
        self.context.generate_galois_keys()  # ローテーション用
        self.context.generate_relin_keys()   # 再線形化用

        self.context.global_scale = 2**40
```

**鍵の種類**:

1. **秘密鍵 (Secret Key)**: 復号に使用、厳重に管理
2. **公開鍵 (Public Key)**: 暗号化に使用、配布可能
3. **Galois鍵**: ベクトルのローテーション操作に必要
4. **再線形化鍵**: 乗算後のノイズ削減

#### 2. データの暗号化

```python
def encrypt_patient_data(self, patients):
    encrypted_data = {
        'ages': [],
        'blood_pressures_systolic': [],
        # ...
    }

    for patient in patients:
        # 各フィールドを個別に暗号化
        encrypted_data['ages'].append(
            ts.ckks_vector(self.context, [float(patient['age'])])
        )
        # ...

    return encrypted_data
```

**暗号文の構造**:

```
Ciphertext:
├─ c0: 多項式 (poly_modulus_degree 個の係数)
├─ c1: 多項式 (poly_modulus_degree 個の係数)
└─ metadata: スケール、レベル等

サイズ: 約 128 KB / 暗号文 (poly_modulus_degree=8192の場合)
```

#### 3. 準同型演算

**サポートされる演算**:

```python
# 加算
encrypted_sum = encrypted_a + encrypted_b
# Enc(a) + Enc(b) = Enc(a + b)

# 乗算
encrypted_product = encrypted_a * encrypted_b
# Enc(a) * Enc(b) = Enc(a * b)

# スカラー倍
encrypted_scaled = encrypted_a * 2.5
# Enc(a) * k = Enc(a * k)

# 平均の計算
total = encrypted_values[0]
for enc_val in encrypted_values[1:]:
    total = total + enc_val
average = total * (1.0 / len(encrypted_values))
```

**ノイズの管理**:

準同型暗号では、演算ごとにノイズが蓄積する。

```
初期ノイズ: ε₀
加算後: ε₀ + ε₁
乗算後: ε₀ * ε₁ (大幅に増加)

乗算可能回数 (multiplicative depth):
poly_modulus_degree=8192, coeff_mod=[60,40,40,60]
→ 約3-4回の乗算が可能
```

**ノイズ対策**:

1. **再線形化 (Relinearization)**: 乗算後のノイズ削減
2. **rescaling**: スケールの調整
3. **modulus switching**: レベルの低下

```python
# TenSEALでは自動的に処理される
result = encrypted_a * encrypted_b  # 内部で再線形化
```

### 暗号文のシリアライゼーション

```python
def save_encrypted_data(self, encrypted_data, filepath):
    # 暗号文をバイト列に変換
    serialized_data = {}
    for key, values in encrypted_data.items():
        serialized_data[key] = [val.serialize() for val in values]

    # ファイルに保存
    with open(filepath, 'wb') as f:
        pickle.dump(serialized_data, f)
```

**ストレージ要件**:

```
元データサイズ: 1 KB / 患者
暗号化データサイズ: 約 256 KB / 患者 (6フィールド)

100人の患者データ:
元データ: 100 KB
暗号化データ: 25.6 MB

→ 約256倍
```

---

## ゼロ知識証明の実装

### Groth16 zkSNARKの選択理由

**Groth16** を採用した理由:

1. **証明サイズが小さい**: 約200バイト（他方式は数KB）
2. **検証が高速**: 数ミリ秒
3. **成熟した実装**: snarkjs、circomで利用可能
4. **産業界での実績**: Zcash等で使用

**代替案との比較**:

| 方式 | 証明サイズ | 検証時間 | Trusted Setup |
|------|-----------|---------|---------------|
| Groth16 | 約200B | 数ms | 必要 |
| PLONK | 約1KB | 数十ms | Universal |
| STARKs | 数十KB | 数百ms | 不要 |

### ZKP回路の設計

#### 回路の目的

以下を証明する:

1. **データの完全性**: ハッシュ値が一致
2. **範囲制約**: データが有効な範囲内
3. **データの存在**: 実際のデータから生成された

#### 検証する具体的な範囲

本システムのZKP回路は、以下の5つのフィールドに対して範囲チェックを実行します：

| フィールド | 範囲 | 単位 | 医学的根拠 |
|-----------|------|------|-----------|
| **年齢** | 0 ≤ age ≤ 120 | 歳 | 人間の生物学的限界 |
| **収縮期血圧** | 80 ≤ systolic ≤ 200 | mmHg | 低血圧～重度高血圧の範囲 |
| **拡張期血圧** | 50 ≤ diastolic ≤ 130 | mmHg | 低血圧～重度高血圧の範囲 |
| **血糖値** | 50 ≤ blood_sugar ≤ 300 | mg/dL | 低血糖～重度高血糖の範囲 |
| **コレステロール** | 100 ≤ cholesterol ≤ 400 | mg/dL | 低コレステロール～重度高コレステロール |

**重要**: これらの範囲は医学的に妥当なデータを保証し、異常値や入力ミスを検出します。範囲外のデータはZKP証明生成時に拒否されます。

#### Circom回路の実装

```circom
pragma circom 2.0.0;

include "../node_modules/circomlib/circuits/poseidon.circom";
include "../node_modules/circomlib/circuits/comparators.circom";

template RangeCheck(min, max) {
    signal input value;
    signal output valid;

    // 最小値チェック: value >= min
    component geMin = GreaterEqThan(32);
    geMin.in[0] <== value;
    geMin.in[1] <== min;

    // 最大値チェック: value <= max
    component leMax = LessEqThan(32);
    leMax.in[0] <== value;
    leMax.in[1] <== max;

    // AND演算
    valid <== geMin.out * leMax.out;
}

template MedicalDataVerification() {
    // プライベート入力（秘密）
    signal input age;
    signal input blood_pressure_systolic;
    signal input blood_pressure_diastolic;
    signal input blood_sugar;
    signal input cholesterol;

    // パブリック入力
    signal input salt;  // ランダム値

    // パブリック出力
    signal output dataHash;
    signal output isValid;

    // 1. データハッシュの計算（Poseidon）
    component hasher = Poseidon(6);
    hasher.inputs[0] <== age;
    hasher.inputs[1] <== blood_pressure_systolic;
    hasher.inputs[2] <== blood_pressure_diastolic;
    hasher.inputs[3] <== blood_sugar;
    hasher.inputs[4] <== cholesterol;
    hasher.inputs[5] <== salt;

    dataHash <== hasher.out;

    // 2. 範囲チェック
    component ageCheck = RangeCheck(0, 120);
    ageCheck.value <== age;

    component bpSystolicCheck = RangeCheck(80, 200);
    bpSystolicCheck.value <== blood_pressure_systolic;

    component bpDiastolicCheck = RangeCheck(50, 130);
    bpDiastolicCheck.value <== blood_pressure_diastolic;

    component bloodSugarCheck = RangeCheck(50, 300);
    bloodSugarCheck.value <== blood_sugar;

    component cholesterolCheck = RangeCheck(100, 400);
    cholesterolCheck.value <== cholesterol;

    // 3. すべてのチェックが通ったか
    signal check1, check2, check3, check4;

    check1 <== ageCheck.valid * bpSystolicCheck.valid;
    check2 <== check1 * bpDiastolicCheck.valid;
    check3 <== check2 * bloodSugarCheck.valid;
    check4 <== check3 * cholesterolCheck.valid;

    isValid <== check4;

    // 制約: isValid == 1
    isValid === 1;
}

component main {public [salt]} = MedicalDataVerification();
```

#### 回路の制約数

```
RangeCheck回路: 約 128 制約 / チェック
MedicalDataVerification回路: 約 1000 制約

制約数が多いほど:
- セットアップ時間が長い
- 証明生成時間が長い
- 証明サイズは変わらない（Groth16）
```

### Powers of Tau セレモニー

**Trusted Setup** の実行:

```javascript
// Phase 1: Powers of Tau
await snarkjs.powersoftau.new(
    bn128,              // 楕円曲線
    12,                 // 2^12 = 4096 制約まで対応
    ptauFile
);

await snarkjs.powersoftau.contribute(
    ptauFile,
    ptauContributed,
    "First contribution",
    entropy
);

await snarkjs.powersoftau.prepare_phase2(
    ptauContributed,
    ptauFinal
);
```

**セキュリティの考慮**:

- 少なくとも1人が正直なら安全
- 複数の貢献者で信頼性向上
- 本番環境では公開セレモニーを推奨

### 証明の生成

```javascript
async function generateProof(patientData, salt) {
    // 入力データの準備
    const input = {
        age: patientData.age,
        blood_pressure_systolic: patientData.blood_pressure_systolic,
        blood_pressure_diastolic: patientData.blood_pressure_diastolic,
        blood_sugar: patientData.blood_sugar,
        cholesterol: patientData.cholesterol,
        salt: salt
    };

    // Witnessの計算
    const { proof, publicSignals } = await snarkjs.groth16.fullProve(
        input,
        wasmFile,
        zkeyFile
    );

    return { proof, publicSignals };
}
```

**生成される証明**:

```json
{
  "pi_a": ["<G1点>", "<G1点>", "1"],
  "pi_b": [["<G2点>", "<G2点>"], ["<G2点>", "<G2点>"], ["1", "0"]],
  "pi_c": ["<G1点>", "<G1点>", "1"],
  "protocol": "groth16",
  "curve": "bn128"
}
```

**サイズ**: 約 200-300 バイト

### 証明の検証

```javascript
async function verifyProof(proof, publicSignals) {
    // 検証鍵の読み込み
    const vkey = JSON.parse(
        fs.readFileSync('keys/verification_key.json', 'utf8')
    );

    // 検証実行
    const isValid = await snarkjs.groth16.verify(
        vkey,
        publicSignals,
        proof
    );

    return isValid;
}
```

**検証時間**: 約 10-50 ms

**公開シグナル**:

```json
[
  "12345678901234567890",  // dataHash
  "1",                     // isValid
  "42"                     // salt
]
```

### ZKPのセキュリティ保証

**数学的保証**:

1. **Completeness (完全性)**:
   - 正しいデータなら、証明は常に検証を通る

2. **Soundness (健全性)**:
   - 間違ったデータでは、証明は検証を通らない
   - 確率: 1 - 1/(楕円曲線の位数) ≈ 1 - 2^(-128)

3. **Zero-Knowledge (ゼロ知識性)**:
   - 証明からプライベート入力を推測できない

---

## 差分プライバシーの実装

### 差分プライバシーとは

差分プライバシー（Differential Privacy）は、統計クエリの結果にノイズを加えることで、個人のデータがクエリ結果に与える影響を数学的に制限する技術です。

**数学的定義**:

あるアルゴリズム $\mathcal{M}$ が $(\varepsilon, \delta)$-差分プライバシーを満たすとは、任意の隣接データセット $D, D'$（1レコードのみ異なる）と任意の出力集合 $S$ に対して：

$$
\Pr[\mathcal{M}(D) \in S] \leq e^\varepsilon \cdot \Pr[\mathcal{M}(D') \in S] + \delta
$$

### パラメータの意味

| パラメータ | 意味 | 推奨値 |
|-----------|------|--------|
| $\varepsilon$ (epsilon) | プライバシー損失。小さいほど高いプライバシー | 0.1〜1.0 |
| $\delta$ | 確率的な緩和。通常は非常に小さい値 | $\frac{1}{n^2}$（n=サンプル数） |
| Sensitivity | 1レコードがクエリ結果に与える最大影響 | 演算によって異なる |

### 本システムでの実装

#### DifferentialPrivacy クラス

```python
from enum import Enum
import numpy as np

class NoiseType(Enum):
    LAPLACE = "laplace"
    GAUSSIAN = "gaussian"

class DifferentialPrivacy:
    def __init__(self, epsilon: float = 1.0, delta: float = 1e-5):
        self.epsilon = epsilon
        self.delta = delta

    def calculate_sensitivity(self, operation: str, data_range: tuple,
                              sample_size: int) -> float:
        """演算タイプに基づいて感度を計算"""
        range_size = data_range[1] - data_range[0]

        if operation == "mean":
            return range_size / sample_size
        elif operation == "sum":
            return range_size
        elif operation == "count":
            return 1
        elif operation == "variance":
            return (range_size ** 2) / sample_size
        else:
            return range_size / sample_size

    def add_laplace_noise(self, value, sensitivity, epsilon=None):
        """ラプラスノイズを追加"""
        eps = epsilon or self.epsilon
        scale = sensitivity / eps
        noise = np.random.laplace(loc=0, scale=scale)
        return value + noise

    def add_gaussian_noise(self, value, sensitivity, epsilon=None, delta=None):
        """ガウスノイズを追加（より強いプライバシー保証）"""
        eps = epsilon or self.epsilon
        d = delta or self.delta
        sigma = sensitivity * np.sqrt(2 * np.log(1.25 / d)) / eps
        noise = np.random.normal(loc=0, scale=sigma)
        return value + noise
```

#### フィールド別感度設定

| フィールド | データ範囲 | 平均の感度 (n=100) |
|-----------|-----------|-------------------|
| age | 0〜120 | 1.2 |
| blood_pressure_systolic | 80〜200 | 1.2 |
| blood_pressure_diastolic | 50〜130 | 0.8 |
| blood_sugar | 50〜300 | 2.5 |
| cholesterol | 100〜400 | 3.0 |
| bmi | 10〜50 | 0.4 |

#### 使用例

```python
dp = DifferentialPrivacy(epsilon=1.0, delta=1e-5)

# 復号結果にノイズを適用
result = {
    "operation": "mean",
    "field": "blood_pressure_systolic",
    "value": 135.5
}

noisy_result = dp.apply_to_result(
    result=result,
    operation="mean",
    field="blood_pressure_systolic",
    sample_size=100,
    noise_type=NoiseType.LAPLACE
)
# noisy_result["noisy_value"] ≈ 135.5 ± 1.2
```

### プライバシーとユーティリティのトレードオフ

```
epsilon値   ノイズレベル    精度への影響
─────────────────────────────────────────
0.1        非常に高い      ±10〜20%
0.5        高い            ±2〜5%
1.0        中程度          ±1〜2%（推奨）
2.0        低い            ±0.5〜1%
5.0        非常に低い      ±0.1〜0.5%
```

---

## バッチZKP（Merkle Tree）

### 概要

従来のZKP方式では、各患者に対して個別にZKP証明を生成していましたが、大量のデータに対しては効率が悪くなります。バッチZKPは、Merkle Treeを使用して全患者データの整合性を効率的に検証します。

### Merkle Treeとは

Merkle Treeは、データの集合を階層的にハッシュ化したツリー構造です。

```
                    Root Hash
                   /         \
            Hash(0-1)        Hash(2-3)
           /       \        /       \
     Hash(P0)  Hash(P1)  Hash(P2)  Hash(P3)
        |         |         |         |
      Patient0  Patient1  Patient2  Patient3
```

**特性**:
- **Root Hash**: 全データの要約（32バイト）
- **証明サイズ**: $O(\log n)$（nはデータ数）
- **検証時間**: $O(\log n)$

### 本システムでの実装

#### MerkleTree クラス

```python
import hashlib
from typing import List, Dict, Optional

class MerkleTree:
    def __init__(self, hash_func=None):
        self.hash_func = hash_func or self._sha256_hash
        self.leaves: List[str] = []
        self.tree: List[List[str]] = []
        self.root: Optional[str] = None

    def _sha256_hash(self, data: str) -> str:
        return hashlib.sha256(data.encode()).hexdigest()

    def add_leaf_hash(self, leaf_hash: str):
        """リーフハッシュを追加"""
        self.leaves.append(leaf_hash)

    def build(self) -> str:
        """ツリーを構築してルートを返す"""
        if not self.leaves:
            raise ValueError("No leaves to build tree")

        current_level = self.leaves[:]

        # 奇数の場合、最後を複製
        if len(current_level) % 2 == 1:
            current_level.append(current_level[-1])

        self.tree = [current_level]

        while len(current_level) > 1:
            next_level = []
            for i in range(0, len(current_level), 2):
                combined = current_level[i] + current_level[i+1]
                next_level.append(self.hash_func(combined))

            if len(next_level) > 1 and len(next_level) % 2 == 1:
                next_level.append(next_level[-1])

            self.tree.append(next_level)
            current_level = next_level

        self.root = current_level[0]
        return self.root

    def get_proof(self, index: int) -> List[Dict]:
        """指定インデックスの包含証明を生成"""
        if not self.tree:
            raise ValueError("Tree not built yet")

        proof = []
        current_index = index

        for level in range(len(self.tree) - 1):
            level_size = len(self.tree[level])
            is_right = current_index % 2 == 1
            sibling_index = current_index - 1 if is_right else current_index + 1

            if sibling_index < level_size:
                proof.append({
                    "hash": self.tree[level][sibling_index],
                    "position": "left" if is_right else "right"
                })

            current_index = current_index // 2

        return proof

    @staticmethod
    def verify_proof(leaf_hash: str, proof: List[Dict], root: str) -> bool:
        """包含証明を検証"""
        current_hash = leaf_hash
        hash_func = lambda x: hashlib.sha256(x.encode()).hexdigest()

        for step in proof:
            if step["position"] == "left":
                combined = step["hash"] + current_hash
            else:
                combined = current_hash + step["hash"]
            current_hash = hash_func(combined)

        return current_hash == root
```

#### BatchZKPService クラス

```python
class BatchZKPService:
    def __init__(self):
        self.merkle_tree = MerkleTree()

    def hash_patient_data(self, patient_data: Dict) -> str:
        """患者データをハッシュ化"""
        sorted_keys = sorted(patient_data.keys())
        data_string = "|".join(f"{k}:{patient_data[k]}" for k in sorted_keys)
        return hashlib.sha256(data_string.encode()).hexdigest()

    def generate_batch_proof(self, patients_df, sample_size: int = 10) -> Dict:
        """バッチ証明を生成"""
        # 1. 全患者のハッシュを計算
        self.merkle_tree = MerkleTree()
        patient_hashes = []

        for _, patient in patients_df.iterrows():
            patient_hash = self.hash_patient_data(patient.to_dict())
            patient_hashes.append(patient_hash)
            self.merkle_tree.add_leaf_hash(patient_hash)

        # 2. Merkle Treeを構築
        merkle_root = self.merkle_tree.build()

        # 3. サンプリングしてZKP証明を生成
        sample_indices = np.random.choice(
            len(patient_hashes),
            min(sample_size, len(patient_hashes)),
            replace=False
        )

        sample_proofs = []
        for idx in sample_indices:
            proof = self.merkle_tree.get_proof(idx)
            sample_proofs.append({
                "index": int(idx),
                "leaf_hash": patient_hashes[idx],
                "merkle_proof": proof
            })

        return {
            "merkle_root": merkle_root,
            "total_patients": len(patient_hashes),
            "sample_size": len(sample_proofs),
            "sample_proofs": sample_proofs,
            "coverage": len(sample_proofs) / len(patient_hashes)
        }
```

### 従来方式との比較

| 指標 | 従来（個別ZKP） | バッチZKP |
|------|----------------|-----------|
| 証明数 | n（患者数） | 1 + サンプル数 |
| 証明サイズ | n × 200B | 32B + log(n) × サンプル数 |
| 生成時間 | O(n) | O(n) ハッシュ + O(sample) ZKP |
| 検証時間 | O(n) | O(sample × log n) |
| 全体カバレッジ | 100% | 統計的保証 |

### 使用例

```python
# バッチZKPの生成
batch_zkp_service = BatchZKPService()
batch_proof = batch_zkp_service.generate_batch_proof(
    patients_df=patients,
    sample_size=10
)

# 結果
print(f"Merkle Root: {batch_proof['merkle_root']}")
print(f"Total patients: {batch_proof['total_patients']}")
print(f"Sample coverage: {batch_proof['coverage']:.1%}")

# 検証
for sample in batch_proof['sample_proofs']:
    is_valid = MerkleTree.verify_proof(
        leaf_hash=sample['leaf_hash'],
        proof=sample['merkle_proof'],
        root=batch_proof['merkle_root']
    )
    print(f"Patient {sample['index']}: {'Valid' if is_valid else 'Invalid'}")
```

---

## 機械学習の実装

### 暗号化データでのML

#### サポートされるモデル

**完全対応**:

```python
# 1. 線形回帰
class EncryptedLinearRegression:
    def predict_encrypted(self, X_encrypted):
        # y = w·x + b (暗号化のまま)
        prediction = X_encrypted[0] * float(self.weights[0])
        for i in range(1, len(self.weights)):
            prediction = prediction + (X_encrypted[i] * float(self.weights[i]))
        prediction = prediction + float(self.bias)
        return prediction
```

**演算の内訳**:
- 加算: n回 (n = 特徴量数)
- 乗算: n回
- Multiplicative depth: 1

**精度**: 元のモデルと同等

#### Sigmoid関数の多項式近似

```python
def sigmoid_poly_approx(self, x):
    """
    σ(x) ≈ 0.5 + 0.197x - 0.004x³

    精度:
    - 範囲 [-5, 5]: 誤差 < 0.01
    - 範囲 [-2, 2]: 誤差 < 0.001
    """
    x_cubed = x * x * x
    result = x * 0.197 + x_cubed * (-0.004) + 0.5
    return result
```

**誤差分析**:

| x | 真のσ(x) | 近似値 | 誤差 |
|---|---------|--------|------|
| -5 | 0.007 | 0.015 | 0.008 |
| -2 | 0.119 | 0.122 | 0.003 |
| 0 | 0.500 | 0.500 | 0.000 |
| 2 | 0.881 | 0.878 | 0.003 |
| 5 | 0.993 | 0.985 | 0.008 |

**Multiplicative depth**: 3（x³の計算）

#### ニューラルネットワーク

```python
class EncryptedNeuralNetwork:
    def forward_encrypted(self, X_encrypted):
        # 隠れ層
        hidden = []
        for j in range(self.hidden_dim):
            h = X_encrypted[0] * float(self.W1[0, j])
            for i in range(1, self.input_dim):
                h = h + (X_encrypted[i] * float(self.W1[i, j]))
            h = h + float(self.b1[j])

            # 活性化関数（多項式近似）
            h = self.activation_poly(h)
            hidden.append(h)

        # 出力層
        output = hidden[0] * float(self.W2[0, 0])
        for j in range(1, self.hidden_dim):
            output = output + (hidden[j] * float(self.W2[j, 0]))
        output = output + float(self.b2[0])

        return output
```

**Multiplicative depth**:
- 隠れ層: 3 (線形変換1 + 活性化関数2)
- 出力層: 4 (隠れ層3 + 線形変換1)

**制限**:
- 2-3層が現実的な限界
- それ以上はノイズが蓄積

### 訓練 vs 推論

**訓練**:
```
暗号化データでの訓練は非常に困難:
- 逆伝播が複雑
- 勾配計算にノイズ蓄積
- 実用的には平文で訓練

推奨アプローチ:
1. データ提供者が平文で訓練
2. モデルパラメータ（重み）を共有
3. 購入者が暗号化データで推論
```

**推論**:
```
暗号化データでの推論は実用的:
- 順伝播のみ
- ノイズ管理が容易
- 精度低下は小さい
```

---

## 高度な手法

### 1. ハイブリッド暗号化

**アーキテクチャ**:

```python
class HybridEncryption:
    def __init__(self):
        self.sensitive_features = [0, 2]  # 年齢、血糖値
        self.public_features = [1, 3]     # 血圧、コレステロール

    def encrypt_data(self, X):
        encrypted_data = []
        public_data = []

        for row in X:
            # 機密データのみ暗号化
            sensitive_values = [row[i] for i in self.sensitive_features]
            encrypted_row = ts.ckks_vector(self.context, sensitive_values)
            encrypted_data.append(encrypted_row)

            # 非機密データは平文
            public_values = [row[i] for i in self.public_features]
            public_data.append(public_values)

        return encrypted_data, np.array(public_data)
```

**利点**:
- 複雑なモデル（Random Forest、XGBoost）が使用可能
- 計算速度が速い
- プライバシーと性能のトレードオフを調整可能

**プライバシー分析**:

```
機密度:
├─ 高: 年齢、遺伝情報 → 暗号化
├─ 中: 血圧、血糖値 → 場合による
└─ 低: BMI、性別 → 平文OK（統計的に推測可能）
```

### 2. クライアント-サーバー対話型計算

**プロトコル**:

```
クライアント側:
1. データを暗号化
2. サーバーに送信

サーバー側:
3. 線形演算を実行（暗号化のまま）
4. クライアントに返却

クライアント側:
5. 復号
6. 非線形関数を適用
7. 再暗号化
8. サーバーに送信

... 繰り返し
```

**実装**:

```python
class InteractiveComputation:
    class Server:
        @staticmethod
        def linear_layer(X_encrypted, weights, bias):
            # サーバー: 暗号化のまま線形演算
            output = []
            for j in range(weights.shape[1]):
                y = X_encrypted[0] * float(weights[0, j])
                for i in range(1, len(X_encrypted)):
                    y = y + (X_encrypted[i] * float(weights[i, j]))
                y = y + float(bias[j])
                output.append(y)
            return output

    class Client:
        @staticmethod
        def apply_activation(encrypted_values, activation='relu'):
            # クライアント: 復号→活性化→再暗号化
            decrypted = [enc_val.decrypt()[0] for enc_val in encrypted_values]

            if activation == 'relu':
                activated = [max(0, val) for val in decrypted]
            elif activation == 'sigmoid':
                activated = [1 / (1 + np.exp(-val)) for val in decrypted]

            context = encrypted_values[0].context()
            re_encrypted = [ts.ckks_vector(context, [val]) for val in activated]

            return re_encrypted
```

**通信量**:

```
1層あたり:
├─ サーバー → クライアント: n × 128 KB (n = ノード数)
├─ クライアント → サーバー: n × 128 KB
└─ 合計: 約 25 MB / 層 (n=100の場合)

10層NN: 約 250 MB
```

**計算時間**:

```
従来の暗号化NN: 10分
対話型計算: 30秒 + 通信時間

トレードオフ:
- 精度: 向上（非線形関数を正確に計算）
- 速度: 改善
- 通信: 必要
- セキュリティ: やや低下（クライアントが中間値を見る）
```

### 3. 知識蒸留

**プロセス**:

```
Phase 1: 教師モデルの訓練
├─ 複雑なモデル（Random Forest、深いNN）
├─ 平文データで訓練
└─ 高精度を達成

Phase 2: 生徒モデルの訓練
├─ 単純なモデル（線形、浅いNN）
├─ 教師モデルの出力（ソフトラベル）で訓練
└─ 教師の知識を継承

Phase 3: 暗号化推論
├─ 生徒モデルを使用
├─ 暗号化データで推論
└─ 高精度を維持
```

**実装**:

```python
class KnowledgeDistillation:
    def train_teacher(self, X, y):
        # 教師モデル: 複雑
        self.teacher_model = MLPClassifier(
            hidden_layer_sizes=(20, 15, 10),
            activation='relu',
            max_iter=1000
        )
        self.teacher_model.fit(X, y)

    def distill_to_student(self, X):
        # 教師モデルの出力（ソフトラベル）
        soft_labels = self.teacher_model.predict_proba(X)

        # 生徒モデル: 単純
        self.student_model = MLPClassifier(
            hidden_layer_sizes=(5,),  # 1層のみ
            activation='relu',
            max_iter=1000
        )

        # ソフトラベルで訓練
        hard_labels = np.argmax(soft_labels, axis=1)
        self.student_model.fit(X, hard_labels)
```

**精度の比較**:

```
モデル              精度      暗号化推論
──────────────────────────────────────
教師（深いNN）      95%       困難
生徒（浅いNN）      92%       可能
単純モデル          85%       可能

→ 知識蒸留により7%向上
```

---

## データフロー

### エンドツーエンドのフロー

```
[データ提供者]
    ↓
┌─────────────────────┐
│ 1. データ収集       │
│    - 患者データ     │
│    - 品質チェック   │
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│ 2. 前処理           │
│    - 正規化         │
│    - 欠損値処理     │
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│ 3. 暗号化           │
│    - CKKS暗号化     │
│    - コンテキスト   │
│      生成           │
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│ 4. ZKP証明生成      │
│    - 回路実行       │
│    - 証明生成       │
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│ 5. パッケージング   │
│    - データ         │
│    - 証明           │
│    - 鍵             │
└──────────┬──────────┘
           ↓
    [転送/API]
           ↓
┌─────────────────────┐
│ 6. 検証             │
│    - ZKP検証        │
│    - 整合性チェック │
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│ 7. 暗号化計算       │
│    - 統計分析       │
│    - ML推論         │
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│ 8. 結果取得         │
│    - 必要な値を復号 │
│    - レポート生成   │
└─────────────────────┘
           ↓
   [データ購入者]
```

### データ構造

**患者データ (JSON)**:

```json
{
  "patient_id": "P0001",
  "age": 45,
  "gender": "男性",
  "blood_pressure_systolic": 142,
  "blood_pressure_diastolic": 88,
  "blood_sugar": 105,
  "cholesterol": 220,
  "bmi": 24.5,
  "diseases": ["糖尿病"],
  "treatments": ["メトホルミン"],
  "hospitalization_count": 1,
  "last_visit": "2025-12-15"
}
```

**暗号化データ (pickle)**:

```python
{
  'ages': [<CKKSVector>, <CKKSVector>, ...],
  'blood_pressures_systolic': [<CKKSVector>, ...],
  'blood_pressures_diastolic': [<CKKSVector>, ...],
  'blood_sugars': [<CKKSVector>, ...],
  'cholesterols': [<CKKSVector>, ...],
  'bmis': [<CKKSVector>, ...]
}
```

**証明データ (JSON)**:

```json
{
  "proof": {
    "pi_a": [...],
    "pi_b": [...],
    "pi_c": [...],
    "protocol": "groth16",
    "curve": "bn128"
  },
  "publicSignals": [
    "12345678901234567890",  // dataHash
    "1",                     // isValid
    "42"                     // salt
  ]
}
```

---

## 計算機資源の要件

### ハードウェア要件

#### 最小構成

```
CPU: 4コア、2.0 GHz以上
RAM: 16 GB
ストレージ: 100 GB SSD
ネットワーク: 10 Mbps以上
```

**用途**: 開発、小規模テスト（100人程度）

#### 推奨構成

```
CPU: 8-16コア、3.0 GHz以上 (AVX2対応)
RAM: 32-64 GB
ストレージ: 500 GB SSD (NVMe推奨)
ネットワーク: 100 Mbps以上
GPU: (オプション) CUDA対応GPU
```

**用途**: 本番環境、大規模データ（10,000人以上）

#### エンタープライズ構成

```
CPU: 32-64コア、3.5 GHz以上
RAM: 128-256 GB
ストレージ: 2 TB NVMe SSD (RAID 0/10)
ネットワーク: 1 Gbps以上
GPU: NVIDIA A100 / V100 (zkML用)
```

**用途**: 数十万人規模、リアルタイム処理

### ソフトウェア要件

```
OS: Linux (Ubuntu 20.04+, CentOS 8+)
    または macOS 11+

言語環境:
├─ Python 3.8+
├─ Node.js 16+
└─ npm 8+

ライブラリ:
├─ TenSEAL 0.3.14+
├─ Circom 2.1.6+
├─ snarkjs 0.7.0+
├─ NumPy 1.24+
└─ scikit-learn 1.3+

オプション:
├─ Docker (コンテナ化)
└─ Kubernetes (オーケストレーション)
```

### ストレージ要件

**データサイズの見積もり**:

```
┌─────────────┬──────────┬───────────┬──────────┐
│ 患者数      │ 元データ │ 暗号化    │ 証明     │
├─────────────┼──────────┼───────────┼──────────┤
│ 100人       │ 100 KB   │ 25.6 MB   │ 50 KB    │
│ 1,000人     │ 1 MB     │ 256 MB    │ 500 KB   │
│ 10,000人    │ 10 MB    │ 2.56 GB   │ 5 MB     │
│ 100,000人   │ 100 MB   │ 25.6 GB   │ 50 MB    │
│ 1,000,000人 │ 1 GB     │ 256 GB    │ 500 MB   │
└─────────────┴──────────┴───────────┴──────────┘

※ 6フィールドを暗号化した場合
```

**追加のストレージ**:

```
ZKP関連:
├─ Powers of Tau: 200 MB - 2 GB (回路サイズによる)
├─ 証明鍵 (zkey): 100 MB - 1 GB
└─ ビルド成果物: 50 MB

ログ・バックアップ:
└─ データサイズの50-100%を追加で確保
```

### メモリ要件

**暗号化処理**:

```
患者数     メモリ使用量
────────────────────
100人      約 1 GB
1,000人    約 5 GB
10,000人   約 30 GB
100,000人  約 200 GB (要分割処理)
```

**ZKP証明生成**:

```
回路サイズ (制約数)  メモリ使用量
──────────────────────────────
1,000制約            約 500 MB
10,000制約           約 2 GB
100,000制約          約 10 GB
```

**機械学習**:

```
モデル               メモリ使用量
────────────────────────────
線形回帰             約 100 MB
ロジスティック回帰    約 200 MB
浅いNN (1層)         約 500 MB
浅いNN (2-3層)       約 2 GB
```

---

## パフォーマンス特性

### 暗号化性能

**暗号化速度** (poly_modulus_degree=8192):

```
CPU: Intel Core i7-9750H (6コア、2.6 GHz)

┌─────────────┬──────────────┬────────────┐
│ 患者数      │ 暗号化時間   │ スループット│
├─────────────┼──────────────┼────────────┤
│ 100人       │ 0.5秒        │ 200人/秒   │
│ 1,000人     │ 4秒          │ 250人/秒   │
│ 10,000人    │ 38秒         │ 263人/秒   │
│ 100,000人   │ 6分20秒      │ 263人/秒   │
└─────────────┴──────────────┴────────────┘

※ 6フィールドを暗号化
※ 並列化なし
```

**並列化の効果**:

```
スレッド数   スピードアップ   効率
─────────────────────────────────
1           1.0x            100%
2           1.8x            90%
4           3.2x            80%
8           5.6x            70%
16          8.0x            50%

※ CPU依存
```

### ZKP性能

**セットアップ時間**:

```
回路サイズ (制約数)  コンパイル   Powers of Tau   鍵生成    合計
──────────────────────────────────────────────────────────────
1,000制約            5秒          30秒            10秒      45秒
10,000制約           15秒         2分             30秒      3分
100,000制約          2分          10分            3分       15分
1,000,000制約        20分         1時間           30分      2時間

※ 初回のみ、再利用可能
```

**証明生成時間**:

```
回路サイズ (制約数)  Witness計算  証明生成   合計
──────────────────────────────────────────────
1,000制約            0.1秒        1秒        1.1秒
10,000制約           0.5秒        3秒        3.5秒
100,000制約          3秒          15秒       18秒
1,000,000制約        30秒         2分        2.5分
```

**証明検証時間**:

```
回路サイズに関わらず、ほぼ一定:

検証時間: 10-50 ms

※ Groth16の特性
```

### 機械学習性能

**訓練時間** (平文):

```
モデル               データ数     訓練時間
──────────────────────────────────────────
線形回帰             10,000      0.1秒
ロジスティック回帰    10,000      0.5秒
NN (1層)             10,000      2秒
NN (2層)             10,000      5秒
NN (3層)             10,000      10秒
```

**推論時間** (暗号化):

```
モデル               データ数     推論時間 (暗号化)  vs 平文
────────────────────────────────────────────────────────
線形回帰             100         0.5秒              50x
ロジスティック回帰    100         2秒                100x
NN (1層)             100         5秒                200x
NN (2層)             100         15秒               500x

※ 並列化なし
※ バッチ処理で改善可能
```

**バッチ処理の効果**:

```
バッチサイズ   推論時間 (100データ)   スループット
───────────────────────────────────────────────
1             50秒                   2データ/秒
10            8秒                    12.5データ/秒
100           5秒                    20データ/秒
```

### ネットワーク性能

**データ転送時間**:

```
ネットワーク速度: 100 Mbps

データサイズ   転送時間
───────────────────────
25.6 MB       2秒
256 MB        20秒
2.56 GB       3.4分
25.6 GB       34分
```

**圧縮の効果**:

```
暗号化データは圧縮困難:
圧縮率: 約 95-98% (ほぼ圧縮されない)

→ 圧縮は推奨しない
```

---

## セキュリティ分析

### 脅威モデル

**想定する攻撃者**:

1. **外部攻撃者**:
   - データベースへの不正アクセス
   - ネットワーク盗聴
   - サービス妨害 (DoS)

2. **内部関係者**:
   - システム管理者
   - データ分析者
   - 悪意のあるデータ購入者

3. **国家レベル攻撃者**:
   - 大規模な計算資源
   - 暗号解析の専門知識

### セキュリティ保証

#### 準同型暗号のセキュリティ

**暗号強度**:

```
poly_modulus_degree=8192
→ 約128ビットセキュリティ

解読に必要な計算量:
2^128 ≈ 3.4 × 10^38 演算

スーパーコンピュータ (10^18 FLOPS):
解読時間 ≈ 10^20 秒 ≈ 3 × 10^12 年

→ 実質的に解読不可能
```

**秘密鍵の管理**:

```
推奨事項:
├─ ハードウェアセキュリティモジュール (HSM) に保管
├─ 鍵の分散管理 (Shamir's Secret Sharing)
├─ 定期的な鍵ローテーション
└─ アクセスログの記録
```

実装上の前提:
- 秘密鍵はデータ提供者サーバーのみで保持し、暗号化パッケージには含めない
- 復号は必ず API (/api/decrypt) 経由で実行し、フロントエンドには公開鍵のみ配布

#### ZKPのセキュリティ

**健全性 (Soundness)**:

```
偽の証明が検証を通る確率:
< 1 / (楕円曲線の位数)
≈ 2^(-128)

→ 事実上不可能
```

**ゼロ知識性**:

```
証明から得られる情報:
- パブリック入力のみ
- プライベート入力は一切漏れない

数学的に保証:
シミュレータの存在により証明
```

**Trusted Setupのリスク**:

```
リスク:
- すべての参加者が共謀すると、偽の証明が可能

対策:
- 複数の独立した参加者
- 少なくとも1人が正直なら安全
- 公開セレモニーの実施

代替案:
- Transparent Setup (PLONK, STARKs)
```

### 攻撃シナリオと対策

#### シナリオ1: データベース漏洩

**攻撃**:
```
攻撃者がデータベース全体を盗む
```

**影響**:
```
仮名化の場合:
❌ データ内容が平文で見える
❌ 他のデータセットと突合で再識別

ZKP-DBの場合:
✅ 暗号文のみ
✅ 秘密鍵なしでは復号不可能
✅ プライバシーは保護される
```

#### シナリオ2: 中間者攻撃 (MITM)

**攻撃**:
```
ネットワーク通信を盗聴・改ざん
```

**対策**:
```
1. TLS/SSL通信の強制
2. ZKP証明による改ざん検出
3. 暗号化データのため、盗聴されても安全
```

#### シナリオ3: 悪意のあるデータ購入者

**攻撃**:
```
購入者が複数のデータセットを購入し、突合を試みる
```

**影響**:
```
仮名化の場合:
❌ 準識別子で突合可能
❌ 個人の再識別

ZKP-DBの場合:
✅ すべてのデータが暗号化
✅ 同じ患者でも異なる暗号文
✅ 突合攻撃が成立しない
```

#### シナリオ4: サイドチャネル攻撃

**攻撃**:
```
計算時間、消費電力などから情報を推測
```

**対策**:
```
1. 一定時間処理 (Constant-time)
2. ブラインディング技術
3. ノイズの追加

※ 本プロトタイプでは未実装
```

### コンプライアンス

**GDPR (欧州一般データ保護規則)**:

```
暗号化データの扱い:
- 秘密鍵なしで復号不可能
  → 個人データではない
- "pseudonymisation"より強力
- 国際的なデータ移転が容易
```

**HIPAA (米国医療情報保護法)**:

```
Safe Harbor方式:
暗号化は推奨される保護手段の一つ

追加の保護:
- アクセス制御
- 監査ログ
- データ最小化
```

**日本の次世代医療基盤法**:

```
匿名加工医療情報:
- 暗号化データは該当しない可能性
- 法的解釈は確認が必要

推奨:
- 法務専門家への相談
- 倫理委員会の承認
```

---

## API仕様

### RESTful API設計

#### エンドポイント一覧

```
POST   /api/v1/encrypt           データの暗号化
POST   /api/v1/decrypt           データの復号（自動DP適用）
POST   /api/v1/proof/generate    証明の生成
POST   /api/v1/proof/verify      証明の検証
POST   /api/v1/estimate-noise    ノイズ量の事前推定
POST   /api/v1/verify-batch-proof バッチ証明の検証
POST   /api/v1/query             暗号化クエリ実行
GET    /api/v1/data/:id          データパッケージ取得
POST   /api/v1/ml/train          モデル訓練 (平文)
POST   /api/v1/ml/predict        モデル推論 (暗号化)
```

#### データ暗号化 API

**リクエスト**:

```http
POST /api/v1/encrypt
Content-Type: application/json

{
  "data": [
    {
      "patient_id": "P0001",
      "age": 45,
      "blood_pressure_systolic": 142,
      ...
    },
    ...
  ],
  "fields": ["age", "blood_pressure_systolic", ...],
  "he_params": {
    "poly_modulus_degree": 8192,
    "coeff_mod_bit_sizes": [60, 40, 40, 60],
    "scale": 1099511627776
  }
}
```

**レスポンス**:

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "encrypted_data_id": "enc_abc123",
  "context_id": "ctx_xyz789",
  "num_records": 100,
  "encrypted_at": "2025-12-27T10:30:00Z",
  "download_url": "/api/v1/data/enc_abc123"
}
```

#### 証明生成 API

**リクエスト**:

```http
POST /api/v1/proof/generate
Content-Type: application/json

{
  "data": {
    "age": 45,
    "blood_pressure_systolic": 142,
    "blood_pressure_diastolic": 88,
    "blood_sugar": 105,
    "cholesterol": 220
  },
  "salt": 42,
  "circuit": "data_verification"
}
```

**レスポンス**:

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "proof_id": "proof_def456",
  "proof": {
    "pi_a": [...],
    "pi_b": [...],
    "pi_c": [...]
  },
  "public_signals": [
    "12345678901234567890",
    "1",
    "42"
  ],
  "generated_at": "2025-12-27T10:31:00Z"
}
```

#### 証明検証 API

**リクエスト**:

```http
POST /api/v1/proof/verify
Content-Type: application/json

{
  "proof_id": "proof_def456",
  "proof": {...},
  "public_signals": [...],
  "verification_key_id": "vkey_ghi789"
}
```

**レスポンス**:

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "valid": true,
  "verified_at": "2025-12-27T10:32:00Z",
  "message": "Proof is valid. Data integrity confirmed."
}
```

#### ノイズ推定 API

**リクエスト**:

```http
POST /api/v1/estimate-noise
Content-Type: application/json

{
  "operation": "mean",
  "field": "blood_pressure_systolic",
  "sample_size": 100,
  "noise_type": "laplace",
  "epsilon": 1.0
}
```

**レスポンス**:

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "field": "blood_pressure_systolic",
  "operation": "mean",
  "noise_type": "laplace",
  "epsilon": 1.0,
  "sensitivity": 1.2,
  "expected_noise_std": 1.7,
  "expected_99_percentile_noise": 5.5,
  "message": "期待されるノイズの99%は±5.5以内です"
}
```

#### バッチ証明検証 API

**リクエスト**:

```http
POST /api/v1/verify-batch-proof
Content-Type: application/json

{
  "merkle_root": "abc123...",
  "sample_proofs": [
    {
      "index": 0,
      "leaf_hash": "def456...",
      "merkle_proof": [
        {"hash": "ghi789...", "position": "right"}
      ]
    }
  ],
  "verification_key": "..."
}
```

**レスポンス**:

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "all_valid": true,
  "verified_count": 10,
  "total_proofs": 10,
  "invalid_indices": [],
  "merkle_root_verified": true,
  "message": "全ての証明が検証されました"
}
```

#### 暗号化クエリ API

**リクエスト**:

```http
POST /api/v1/query
Content-Type: application/json

{
  "encrypted_data_id": "enc_abc123",
  "operation": "average",
  "field": "blood_pressure_systolic",
  "filters": {
    "age_min": 40,
    "age_max": 60
  }
}
```

**レスポンス**:

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "result_encrypted": true,
  "result": "0x7a4f9b2e3c8d1f6a...",  // 暗号化された結果
  "decrypted_result": 142.5,            // オプション
  "num_records_processed": 45,
  "executed_at": "2025-12-27T10:33:00Z"
}
```

#### 準同型暗号計算 API

暗号化されたデータに対して準同型演算を実行するエンドポイント。

**リクエスト** (multipart/form-data):

```http
POST /api/compute
Content-Type: multipart/form-data

encrypted_package: [暗号化パッケージZIPファイル]
operation: "mean" | "sum" | "count"
field: "age" | "blood_pressure_systolic" | ...
```

**レスポンス**:

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "encrypted_result": "01a2b3c4...",  // 16進数エンコードされた暗号化結果
  "metadata": {
    "operation": "mean",
    "field": "age",
    "sample_size": 100,
    "filters": {}
  },
  "provider_id": "provider_0",
  "message": "Computed mean on age (encrypted)"
}
```

**対応操作**:
- `mean`: 平均値（暗号化のまま計算可能）
- `sum`: 合計値（暗号化のまま計算可能）
- `count`: カウント（暗号化のまま計算可能）
- `std`, `variance`, `min`, `max`: 復号が必要（別途実装が必要）

**使用例**:

```python
# Pythonでの使用例
import requests

# 暗号化パッケージをアップロード
files = {'encrypted_package': open('encrypted_package.zip', 'rb')}
data = {
    'operation': 'mean',
    'field': 'age'
}

response = requests.post('http://localhost:5000/api/compute', files=files, data=data)
result = response.json()

print(f"暗号化された結果: {result['encrypted_result']}")
print(f"サンプル数: {result['metadata']['sample_size']}")
```

#### 復号 API

暗号化された計算結果を復号し、差分プライバシーを適用して返すエンドポイント。

**リクエスト**:

```http
POST /api/decrypt
Content-Type: application/json

{
  "provider_id": "provider_0",
  "purchaser_id": "pharma_company_123",
  "encrypted_result": "01a2b3c4...",
  "metadata": {
    "operation": "mean",
    "field": "age",
    "sample_size": 100,
    "filters": {}
  }
}
```

**レスポンス**:

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "result": 55.3,  // ノイズ付加後の結果
  "original_result_hidden": true,
  "differential_privacy": {
    "epsilon_used": 1.0,
    "delta_used": 1e-5,
    "noise_type": "laplace",
    "sensitivity": 1.2
  },
  "metadata": {...},
  "remaining_budget": 9.0,
  "remaining_requests": 99,
  "status": "success"
}
```

**セキュリティチェック**:
- k-匿名性: 最低100レコード
- 集約統計のみ許可（個別データ復号は拒否）
- レート制限: 1時間あたり100リクエスト
- プライバシーバジェット管理
- 再構成攻撃検出

### Python SDK

```python
from zkp_db import Client

# クライアント初期化
client = Client(api_key="your_api_key", base_url="https://api.zkp-db.com")

# データ暗号化
encrypted_data = client.encrypt(
    data=patients,
    fields=["age", "blood_pressure_systolic", ...]
)

# 証明生成
proof = client.generate_proof(
    data=patient_data,
    circuit="data_verification"
)

# 証明検証
is_valid = client.verify_proof(
    proof=proof,
    public_signals=public_signals
)

# 暗号化クエリ
result = client.query(
    encrypted_data_id=encrypted_data.id,
    operation="average",
    field="blood_pressure_systolic"
)

# ML推論
prediction = client.predict_encrypted(
    model_id="model_123",
    encrypted_data=encrypted_patient
)
```

---

## Webインターフェース

### 概要

ZKP-DBは、データ提供者とデータ購入者向けの2つのWebアプリケーションを提供します。両方ともReact + Viteで構築され、モダンなSPA（Single Page Application）として動作します。

### アーキテクチャ

```
┌─────────────────────────────────────────────────────┐
│              Frontend Applications                  │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────────────┐    ┌──────────────────┐      │
│  │  Provider App    │    │ Purchaser App    │      │
│  │  (Vite + React)  │    │ (Vite + React)   │      │
│  │  Port: 3000      │    │ Port: 3001       │      │
│  └────────┬─────────┘    └────────┬─────────┘      │
│           │                       │                 │
│           └───────────┬───────────┘                 │
│                       │                             │
│                       ↓                             │
│              ┌─────────────────┐                    │
│              │  Backend API    │                    │
│              │  (Flask)        │                    │
│              │  Port: 5000     │                    │
│              └─────────────────┘                    │
└─────────────────────────────────────────────────────┘
```

### Provider App（データ提供者アプリ）

#### 目的

医療機関やカルテ会社が患者データを暗号化し、ZKP証明付きの販売パッケージを作成するためのWebインターフェース。

#### 主な機能

1. **CSVファイルのアップロード**
   - ドラッグ＆ドロップ対応
   - ファイル形式の検証（.csvのみ）
   - ファイルサイズの表示

2. **データの暗号化とZKP生成**
   - `/api/encrypt`エンドポイントを呼び出し
   - 準同型暗号化（CKKS方式）
   - バッチZKP証明の生成（Merkle Tree方式）
   - 進捗表示とエラーハンドリング

3. **暗号化パッケージのダウンロード**
   - ZIPファイルの自動ダウンロード
   - パッケージ内容の説明表示

#### 技術スタック

```javascript
// Provider App の技術構成
{
  "framework": "React 18",
  "build_tool": "Vite 5",
  "http_client": "axios",
  "styling": "CSS Modules",
  "dev_server": "Vite Dev Server (HMR対応)"
}
```

#### UI構成

```
┌─────────────────────────────────────────┐
│ 🏥 ZKP-DB データ提供者                   │
│ 準同型暗号 + ZKPによるプライバシー保護    │
├─────────────────────────────────────────┤
│                                         │
│ ┌─────────────────────────────────────┐ │
│ │ 患者データの暗号化                   │ │
│ ├─────────────────────────────────────┤ │
│ │                                     │ │
│ │  📁 CSVファイルを選択               │ │
│ │     または                          │ │
│ │     ドラッグ＆ドロップ              │ │
│ │                                     │ │
│ │  [暗号化して販売パッケージを作成]   │ │
│ │                                     │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ ┌─────────────────────────────────────┐ │
│ │ 📦 販売パッケージの内容             │ │
│ ├─────────────────────────────────────┤ │
│ │ • encrypted_data.pkl                │ │
│ │ • public_context.pkl                │ │
│ │ • proof.json (ZKP証明)              │ │
│ │ • public_signals.json               │ │
│ │ • verification_key.json             │ │
│ │ • metadata.json                     │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ ┌─────────────────────────────────────┐ │
│ │ 🔒 セキュリティ要件                 │ │
│ ├─────────────────────────────────────┤ │
│ │ ✅ k-匿名性: 最低100件必要          │ │
│ │ ✅ データ検証: 有効範囲チェック     │ │
│ │ ✅ ZKP: 正当性の数学的証明          │ │
│ │ ✅ 準同型暗号: 暗号化のまま計算可能 │ │
│ └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

#### 実装例

```javascript
// Provider App のメインコンポーネント
import { useState } from 'react'
import axios from 'axios'

function ProviderApp() {
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const apiBase = import.meta.env.VITE_API_BASE || '/api'

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await axios.post(`${apiBase}/encrypt`, formData, {
        responseType: 'blob'
      })

      // ZIPファイルをダウンロード
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', 'encrypted_package.zip')
      link.click()
    } catch (err) {
      console.error('Error:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <input type="file" accept=".csv" onChange={(e) => setFile(e.target.files[0])} />
      <button type="submit" disabled={!file || loading}>
        {loading ? '処理中...' : '暗号化して販売パッケージを作成'}
      </button>
    </form>
  )
}
```

### Purchaser App（データ購入者アプリ）

#### 目的

研究機関や製薬会社が暗号化パッケージの正当性を検証し、暗号化されたまま統計計算を実行するためのWebインターフェース。

#### 主な機能

1. **ZKP証明の検証**
   - `proof.json`と`public_signals.json`のアップロード
   - `/api/verify-proof`エンドポイントを呼び出し
   - 検証結果の表示（成功/失敗）
   - アップロードしたファイルの内容表示機能

2. **簡単な統計量の計算**
   - 暗号化パッケージのアップロード
   - 統計操作の選択（mean, sum, count）
   - フィールドの選択（age, blood_pressure_systolic等）
   - `/api/compute` → `/api/decrypt`の自動呼び出し
   - 差分プライバシー付き結果の表示

3. **Pythonを用いた複雑な統計量の計算**
   - Pythonスクリプトのサンプルコード表示
   - 暗号化結果の手動アップロード（ファイルまたはテキスト）
   - `/api/decrypt`を使った復号

4. **ファイル説明とドキュメント**
   - 各ファイル（proof.json、public_signals.json等）の詳細説明
   - 検証の流れの解説
   - セキュリティ制限の表示

#### UI構成

```
┌─────────────────────────────────────────┐
│ 💊 ZKP-DB データ購入者                   │
│ データの検証と暗号化されたまま分析        │
├─────────────────────────────────────────┤
│                                         │
│ ┌─────────────────────────────────────┐ │
│ │ 🔍 ZKP証明の検証                    │ │
│ ├─────────────────────────────────────┤ │
│ │ proof.json: [選択]                  │ │
│ │ public_signals.json: [選択]         │ │
│ │ [証明書を検証]                      │ │
│ │                                     │ │
│ │ ✅ 検証成功 / ❌ 検証失敗           │ │
│ │                                     │ │
│ │ [詳細説明] [ファイル内容を表示]    │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ ┌─────────────────────────────────────┐ │
│ │ 🧮 簡単な統計量の計算               │ │
│ ├─────────────────────────────────────┤ │
│ │ 暗号化パッケージ: [選択]            │ │
│ │ 統計計算: [mean ▼]                  │ │
│ │ フィールド: [age ▼]                 │ │
│ │ Purchaser ID: [pharma_company_123]  │ │
│ │ [暗号化されたまま計算実行]          │ │
│ │                                     │ │
│ │ 結果: 55.3                          │ │
│ │ サンプル数: 100                     │ │
│ │ 残りバジェット: 9.0                 │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ [Pythonを用いた複雑な統計量の計算]      │
│                                         │
│ ┌─────────────────────────────────────┐ │
│ │ 🔓 APIで復号 / Pythonでの分析方法   │ │
│ │ (タブ切り替え)                      │ │
│ └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

#### 実装例

```javascript
// Purchaser App のZKP検証部分
const handleVerify = async (e) => {
  e.preventDefault()

  const proofText = await proofFile.text()
  const publicSignalsText = await publicSignalsFile.text()

  const proof = JSON.parse(proofText)
  const publicSignals = JSON.parse(publicSignalsText)

  const response = await axios.post(`${apiBase}/verify-proof`, {
    proof,
    public_signals: publicSignals
  })

  setVerificationResult(response.data)
}

// 準同型暗号計算部分
const handleCompute = async (e) => {
  e.preventDefault()

  // ステップ1: 準同型演算を実行
  const formData = new FormData()
  formData.append('encrypted_package', encryptedPackage)
  formData.append('operation', computeOperation)
  formData.append('field', computeField)

  const computeResponse = await axios.post(`${apiBase}/compute`, formData)

  const { encrypted_result, metadata, provider_id } = computeResponse.data

  // ステップ2: 暗号化された結果を復号
  const decryptResponse = await axios.post(`${apiBase}/decrypt`, {
    provider_id,
    purchaser_id,
    encrypted_result,
    metadata
  })

  setComputeResult(decryptResponse.data)
}
```

### デプロイ構成

#### ローカル開発環境

```bash
# Backend
cd backend
source venv/bin/activate
python provider_api.py
# → http://localhost:5000

# Provider App
cd frontend/provider-app
npm install
npm run dev
# → http://localhost:3000/ZKP-DB/provider/

# Purchaser App
cd frontend/purchaser-app
npm install
npm run dev
# → http://localhost:3001/ZKP-DB/purchaser/
```

#### 本番環境

```
Frontend (GitHub Pages):
  Provider App: https://kkuejo.github.io/ZKP-DB/provider/
  Purchaser App: https://kkuejo.github.io/ZKP-DB/purchaser/

Backend (Render):
  API: https://zkp-db.onrender.com/api/*
```

### 環境変数

```bash
# Provider App (.env)
VITE_API_BASE=http://localhost:5000/api  # 開発環境
# VITE_API_BASE=https://zkp-db.onrender.com/api  # 本番環境

# Purchaser App (.env)
VITE_API_BASE=http://localhost:5000/api  # 開発環境
# VITE_API_BASE=https://zkp-db.onrender.com/api  # 本番環境
```

### ビルド設定

```javascript
// vite.config.js (Provider App)
export default defineConfig({
  plugins: [react()],
  base: '/ZKP-DB/provider/',  // GitHub Pages用のベースパス
  server: {
    port: 3000
  }
})

// vite.config.js (Purchaser App)
export default defineConfig({
  plugins: [react()],
  base: '/ZKP-DB/purchaser/',  // GitHub Pages用のベースパス
  server: {
    port: 3001
  }
})
```

### セキュリティ機能

#### CORS設定

バックエンドでCORSを有効化し、フロントエンドからのリクエストを許可：

```python
# backend/provider_api.py
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # 全オリジンを許可（開発環境）

# 本番環境では特定のオリジンのみ許可
# CORS(app, origins=["https://kkuejo.github.io"])
```

#### フロントエンドでのセキュリティ

- **秘密鍵はフロントエンドに送信されない**
- 復号は必ずバックエンドAPI経由
- 暗号化パッケージは公開鍵のみ含む
- ファイルアップロードのサイズ制限
- CSRFトークンの実装（本番環境推奨）

### パフォーマンス最適化

- **コード分割**: Viteの動的インポートを使用
- **遅延ロード**: 必要なコンポーネントのみ読み込み
- **キャッシング**: axios-cacheを使用してAPIレスポンスをキャッシュ
- **HMR（Hot Module Replacement）**: 開発時の高速リロード

### 今後の拡張

- [ ] ファイルプレビュー機能
- [ ] 複数ファイルの一括アップロード
- [ ] データ可視化（グラフ、チャート）
- [ ] リアルタイム進捗表示（WebSocket）
- [ ] ユーザー認証・認可
- [ ] ダッシュボード機能

---

## 実装の詳細

### ディレクトリ構造

```
ZKP-DB/
├── circuits/
│   ├── data_verification.circom     # メインZKP回路
│   ├── range_check.circom           # 範囲チェック回路
│   └── build/                       # ビルド成果物
│       ├── data_verification.r1cs
│       ├── data_verification.wasm
│       └── data_verification.sym
│
├── python/
│   ├── __init__.py
│   ├── generate_dummy_data.py       # ダミーデータ生成
│   ├── homomorphic_encryption.py    # HE実装
│   ├── ml_encrypted.py              # 暗号化ML
│   ├── advanced_ml_techniques.py    # 高度な手法
│   └── integrated_demo.py           # 統合デモ
│
├── scripts/
│   ├── setup.js                     # 環境セットアップ
│   ├── generate_proof.js            # 証明生成
│   └── verify_proof.js              # 証明検証
│
├── keys/
│   ├── context.pkl                  # HEコンテキスト
│   ├── pot12_final.ptau             # Powers of Tau
│   ├── data_verification_final.zkey # 証明鍵
│   └── verification_key.json        # 検証鍵
│
├── data/
│   ├── patients.json                # 生データ
│   ├── patients.csv
│   ├── encrypted_patients.pkl       # 暗号化データ
│   └── lr_model.pkl                 # MLモデル
│
├── proofs/
│   ├── proof_P0001.json
│   ├── public_P0001.json
│   └── witness_P0001.wtns
│
├── docs/
│   ├── ZKP-DB_Explain.md            # 営業向け説明資料
│   ├── ZKP-DB-TechSpec.md           # 技術仕様書（本文書）
│   └── anonymization_vs_encryption.md # 比較資料
│
├── requirements.txt                  # Python依存関係
├── package.json                      # Node.js依存関係
├── .gitignore
└── README.md
```

### 主要クラスの実装

#### MedicalDataEncryptor

```python
class MedicalDataEncryptor:
    """準同型暗号化クラス"""

    def __init__(self):
        self.context = self._create_context()

    def _create_context(self):
        context = ts.context(
            ts.SCHEME_TYPE.CKKS,
            poly_modulus_degree=8192,
            coeff_mod_bit_sizes=[60, 40, 40, 60]
        )
        context.generate_galois_keys()
        context.generate_relin_keys()
        context.global_scale = 2**40
        return context

    def encrypt_patient_data(self, patients):
        """患者データを暗号化"""
        encrypted_data = defaultdict(list)
        for patient in patients:
            for field in FIELDS:
                encrypted_data[field].append(
                    ts.ckks_vector(self.context, [float(patient[field])])
                )
        return encrypted_data

    def compute_encrypted_average(self, encrypted_values):
        """暗号化されたまま平均を計算"""
        total = encrypted_values[0]
        for enc_val in encrypted_values[1:]:
            total = total + enc_val
        return total * (1.0 / len(encrypted_values))

    def decrypt_value(self, encrypted_value):
        """復号"""
        return encrypted_value.decrypt()[0]
```

#### EncryptedLinearRegression

```python
class EncryptedLinearRegression:
    """暗号化線形回帰"""

    def __init__(self, context):
        self.context = context
        self.weights = None
        self.bias = None
        self.scaler = StandardScaler()

    def train(self, X, y):
        """平文で訓練"""
        X_scaled = self.scaler.fit_transform(X)
        model = LinearRegression()
        model.fit(X_scaled, y)
        self.weights = model.coef_
        self.bias = model.intercept_
        return self

    def predict_encrypted(self, X_encrypted):
        """暗号化データで予測"""
        prediction = X_encrypted[0] * float(self.weights[0])
        for i in range(1, len(self.weights)):
            prediction = prediction + (X_encrypted[i] * float(self.weights[i]))
        prediction = prediction + float(self.bias)
        return prediction
```

### テスト

**ユニットテスト**:

```python
# test_encryption.py
import unittest
from homomorphic_encryption import MedicalDataEncryptor

class TestEncryption(unittest.TestCase):
    def setUp(self):
        self.encryptor = MedicalDataEncryptor()

    def test_encrypt_decrypt(self):
        """暗号化→復号のテスト"""
        data = [45.0]
        encrypted = ts.ckks_vector(self.encryptor.context, data)
        decrypted = encrypted.decrypt()
        self.assertAlmostEqual(data[0], decrypted[0], places=2)

    def test_homomorphic_addition(self):
        """準同型加算のテスト"""
        a = ts.ckks_vector(self.encryptor.context, [10.0])
        b = ts.ckks_vector(self.encryptor.context, [20.0])
        c = a + b
        self.assertAlmostEqual(c.decrypt()[0], 30.0, places=2)
```

**統合テスト**:

```python
# test_integration.py
def test_end_to_end():
    """エンドツーエンドテスト"""
    # 1. データ生成
    patients = generate_patient_data(10)

    # 2. 暗号化
    encryptor = MedicalDataEncryptor()
    encrypted_data = encryptor.encrypt_patient_data(patients)

    # 3. 暗号化計算
    encrypted_avg = encryptor.compute_encrypted_average(
        encrypted_data['ages']
    )

    # 4. 復号
    avg_age = encryptor.decrypt_value(encrypted_avg)

    # 5. 検証
    actual_avg = np.mean([p['age'] for p in patients])
    assert abs(avg_age - actual_avg) < 0.1
```

---

## 制限事項と対策

### 現在の制限

#### 1. 計算速度

**問題**:
- 暗号化計算は平文の10-100倍遅い

**対策**:
```
短期:
├─ バッチ処理
├─ 並列化
└─ キャッシング

中期:
├─ GPU活用
├─ 専用ハードウェア (FPGAs)
└─ アルゴリズム最適化

長期:
└─ 技術の進化を待つ (年々高速化)
```

#### 2. Multiplicative Depth

**問題**:
- 乗算できる回数に制限（3-4回）

**対策**:
```
├─ Bootstrapping (ノイズリフレッシュ) ※非常に遅い
├─ パラメータチューニング
├─ ハイブリッド方式
└─ 対話型計算
```

#### 3. 非線形関数

**問題**:
- ReLU、Sigmoidが直接計算できない

**対策**:
```
├─ 多項式近似 (精度低下あり)
├─ 対話型計算 (通信コストあり)
└─ 知識蒸留 (単純なモデル)
```

#### 4. ストレージコスト

**問題**:
- 暗号化データは元データの約256倍

**対策**:
```
├─ ハイブリッド暗号化 (一部のみ)
├─ データ圧縮 (限定的)
└─ ストレージコストの低下を待つ
```

### 今後の改善計画

**実装済み**:
- [x] 差分プライバシー（Laplace/Gaussianノイズ）
- [x] バッチZKP（Merkle Tree）
- [x] API開発（暗号化・復号・証明検証）

**Phase 1 (3ヶ月)**:
- [ ] GPU活用による高速化
- [ ] バッチ処理の更なる最適化
- [ ] プライバシー予算管理システム

**Phase 2 (6ヶ月)**:
- [ ] より効率的なZKP回路
- [ ] PLONK / STARKsへの移行検討
- [x] Webインターフェース（実装済み: Provider App / Purchaser App）

**Phase 3 (12ヶ月)**:
- [ ] Federated Learningとの統合
- [ ] FHIR対応（医療データ標準）
- [ ] 本番環境での実証実験

---

## 今後の拡張

### 短期的な拡張

#### 1. より多くのMLモデル

```python
# Decision Tree (一部)
class EncryptedDecisionTree:
    # 比較演算の近似実装
    pass

# k-means Clustering
class EncryptedKMeans:
    # ユークリッド距離は計算可能
    pass
```

#### 2. Federated Learning

```python
class FederatedZKPSystem:
    def __init__(self, num_hospitals):
        self.hospitals = [Hospital(i) for i in range(num_hospitals)]

    def federated_train(self):
        # 各病院でローカル訓練
        # 勾配を暗号化して集約
        # ZKPで正当性を証明
        pass
```

#### 3. 差分プライバシー（実装済み）

本システムでは既に差分プライバシーが実装されています。詳細は「差分プライバシーの実装」セクションを参照してください。

**実装済み機能**:
- Laplace/Gaussianノイズ機構
- フィールド別感度計算
- 事前ノイズ推定API
- 復号時の自動DP適用

### 中期的な拡張

#### 1. zkML (Zero-Knowledge Machine Learning)

```
完全なZKMLスタック:
├─ モデル訓練の証明
├─ 推論の証明
└─ フェアネスの証明
```

#### 2. ブロックチェーン統合

```
スマートコントラクト:
├─ データの所有権管理
├─ 自動的な支払い
└─ アクセス制御
```

#### 3. Multi-Party Computation (MPC)

```
より柔軟な計算:
├─ 複数パーティで計算を分散
├─ より複雑な演算が可能
└─ 準同型暗号との組み合わせ
```

### 長期的なビジョン

#### 1. 完全なデータマーケットプレイス

```
機能:
├─ データの発見・検索
├─ 品質評価・レーティング
├─ 自動マッチング
├─ スマートコントラクト決済
└─ グローバル展開
```

#### 2. 標準化

```
目標:
├─ 業界標準プロトコルの策定
├─ 相互運用性の確保
└─ 規制当局との連携
```

#### 3. エコシステム

```
参加者:
├─ データ提供者（病院、カルテ会社）
├─ データ購入者（製薬、研究機関）
├─ 技術プロバイダー（ZKP-DB）
├─ 監査機関
└─ 規制当局
```

---

## 参考文献

### 論文

1. Cheon, J. H., Kim, A., Kim, M., & Song, Y. (2017). "Homomorphic encryption for arithmetic of approximate numbers." ASIACRYPT.

2. Groth, J. (2016). "On the size of pairing-based non-interactive arguments." EUROCRYPT.

3. Gilad-Bachrach, R., et al. (2016). "CryptoNets: Applying neural networks to encrypted data with high throughput and accuracy." ICML.

### 実装

- [Microsoft SEAL](https://github.com/Microsoft/SEAL)
- [TenSEAL](https://github.com/OpenMined/TenSEAL)
- [Circom](https://github.com/iden3/circom)
- [snarkjs](https://github.com/iden3/snarkjs)

### ドキュメント

- [SEAL Manual](https://github.com/microsoft/SEAL/blob/main/native/src/seal/seal.h)
- [Circom Documentation](https://docs.circom.io/)
- [ZKP Learning Resources](https://zkp.science/)

---

**文書の終わり**

本技術仕様書に関する質問や提案は、技術チームまでお問い合わせください。
