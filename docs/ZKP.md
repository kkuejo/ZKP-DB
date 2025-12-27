# ゼロ知識証明（Zero-Knowledge Proof）の技術的背景

## 目次

1. [ゼロ知識証明とは何か](#ゼロ知識証明とは何か)
2. [歴史的背景](#歴史的背景)
3. [ゼロ知識証明の種類](#ゼロ知識証明の種類)
4. [zkSNARKとGroth16方式](#zksnarkとgroth16方式)
5. [数学的背景](#数学的背景)
6. [証明生成と検証の仕組み](#証明生成と検証の仕組み)
7. [本システムでの利用](#本システムでの利用)
8. [具体例と実践](#具体例と実践)

---

## ゼロ知識証明とは何か

### 簡単な比喩で理解する

ゼロ知識証明を「色盲の友人にボールの色を証明する」例で理解しましょう。

**シナリオ**:
- あなたは赤と緑のボールを持っています
- 友人は色盲で、2つのボールが同じに見える
- あなたは「2つのボールは違う色だ」と証明したい
- しかし、**どちらが赤でどちらが緑かは教えたくない**

**証明方法**:
1. 友人に2つのボールを見せる
2. 友人が背後でボールを入れ替える（または入れ替えない）
3. あなたは入れ替わったかどうかを当てる
4. これを100回繰り返す

**結果**:
- あなたが毎回正解 → 2つのボールは確実に違う色
- 友人は色の違いを知らないまま（ゼロ知識）
- でも違う色であることは確信できる

### 技術的な定義

ゼロ知識証明は、**ある命題が真であることを証明しながら、その証明に必要な情報以外は一切明かさない暗号技術**です。

**3つの性質**:

1. **完全性（Completeness）**:
   - 命題が真なら、正直な証明者は検証者を納得させられる
   $$
   \text{真の命題} \Rightarrow P(\text{検証成功}) = 1
   $$

2. **健全性（Soundness）**:
   - 命題が偽なら、不正な証明者でも検証者を騙せない
   $$
   \text{偽の命題} \Rightarrow P(\text{検証成功}) \approx 0
   $$

3. **ゼロ知識性（Zero-Knowledge）**:
   - 証明から、命題が真であること以外の情報は一切得られない
   $$
   I(\text{証明}; \text{秘密情報}) = 0
   $$

### 実用例

**パスワード認証（従来）**:
```
ユーザー: 「私のパスワードは "P@ssw0rd" です」
サーバー: 「確かに正しい」
→ パスワードが漏れる！
```

**ゼロ知識証明**:
```
ユーザー: 「私はパスワードを知っている」（証明を送信）
サーバー: 「証明が正しい → あなたはパスワードを知っている」
→ パスワードは一切送信されない！
```

---

## 歴史的背景

### ゼロ知識証明の発展

#### 1985年: ゼロ知識証明の誕生

Goldwasser, Micali, Rackoff が論文で初めて定義。

**歴史的な例**: グラフ同型問題（Graph Isomorphism）

2つのグラフ $G_1$ と $G_2$ が同型であることを、**同型写像を明かさずに**証明。

#### 1986年: GMR署名

ゼロ知識証明を使ったデジタル署名方式。

#### 1988年: フィアット・シャミア変換

**対話型**証明を**非対話型**に変換する技術。

対話型:
```
証明者 ←→ 検証者（何度もやり取り）
```

非対話型:
```
証明者 → 証明 → 検証者（1回で完結）
```

#### 2010年代: zkSNARKの登場

**zkSNARK** (Zero-Knowledge Succinct Non-Interactive Argument of Knowledge)
- **簡潔（Succinct）**: 証明サイズが非常に小さい（数百バイト）
- **非対話型（Non-Interactive）**: 1回のメッセージで完結
- **高速検証**: 数ミリ秒で検証可能

**応用**:
- **Zcash** (2016): プライバシー保護暗号通貨
- **zkSync** (2020): Ethereum Layer 2
- **Filecoin** (2020): 分散ストレージ

#### 2016年: Groth16

Jens Groth が、**最も効率的な zkSNARK** を発表。

- 証明サイズ: たった **128バイト**（3つの楕円曲線点）
- 検証時間: **数ミリ秒**
- **本システムで採用している方式**

#### 2019年以降: 次世代ZKP

- **PLONK** (2019): セットアップが簡単
- **STARKs** (2018): 量子耐性、透明性
- **Bulletproofs** (2018): セットアップ不要

---

## ゼロ知識証明の種類

### 1. 対話型 vs 非対話型

#### 対話型（Interactive）

証明者と検証者が複数回やり取り。

**例**: Schnorr プロトコル
```
ラウンド1: 証明者 → コミットメント → 検証者
ラウンド2: 証明者 ← チャレンジ ← 検証者
ラウンド3: 証明者 → レスポンス → 検証者
```

**欠点**: リアルタイムの通信が必要

#### 非対話型（Non-Interactive）

証明者が1回のメッセージで証明を完結。

**例**: zkSNARK（Groth16）
```
証明者 → 証明（128バイト）→ 検証者
```

**利点**: 証明を保存・転送可能

### 2. 簡潔性による分類

#### 簡潔なZKP（zkSNARK）

- 証明サイズ: $O(1)$（定数サイズ）
- 検証時間: $O(1)$

**例**: Groth16, PLONK

#### 簡潔でないZKP

- 証明サイズ: $O(\sqrt{n})$ または $O(\log n)$

**例**: Bulletproofs, STARKs

### 3. セットアップによる分類

#### Trusted Setup が必要

事前に「信頼されたセットアップ儀式」が必要。

**例**: Groth16
- **CRS** (Common Reference String) を生成
- セットアップの「有毒廃棄物」（toxic waste）を破棄する必要

**リスク**: セットアップが不正なら偽の証明が作れる

#### Transparent（セットアップ不要）

公開パラメータのみで動作。

**例**: STARKs, Bulletproofs

### 比較表

| 方式 | 証明サイズ | 検証時間 | セットアップ | 量子耐性 |
|------|-----------|----------|--------------|----------|
| **Groth16** | **128B** | **10ms** | Trusted | ❌ |
| PLONK | 400B | 20ms | Universal | ❌ |
| Bulletproofs | 1.3KB | 100ms | なし | ❌ |
| STARKs | 50KB | 20ms | なし | ✅ |

**本システムの選択**: Groth16
- 理由: 最小の証明サイズ、最速の検証、成熟した実装

---

## zkSNARKとGroth16方式

### zkSNARKとは

**zkSNARK** = **Z**ero-**K**nowledge **S**uccinct **N**on-Interactive **AR**gument of **K**nowledge

**各用語の意味**:
- **Zero-Knowledge**: 秘密情報を明かさない
- **Succinct**: 証明が簡潔（小さい）
- **Non-Interactive**: 1回の通信で完結
- **Argument**: 計算量的に安全（無限の計算力があれば破れる）
- **of Knowledge**: 証明者が実際に秘密を知っている

### Groth16 の特徴

Groth16 は、**現時点で最も効率的な zkSNARK** です。

#### 証明サイズ

たった **3つの楕円曲線点** = **128バイト**（BN254曲線の場合）

$$
\pi = (A, B, C) \in \mathbb{G}_1 \times \mathbb{G}_2 \times \mathbb{G}_1
$$

- $A, C \in \mathbb{G}_1$: 各32バイト
- $B \in \mathbb{G}_2$: 64バイト

合計: $32 + 64 + 32 = 128$ バイト

#### 検証時間

**たった1つのペアリング方程式**を検証:

$$
e(A, B) = e(\alpha, \beta) \cdot e(C, \delta) \cdot e(\text{public}, \gamma)
$$

検証時間: **10〜50ミリ秒**

#### セットアップ

**2段階のセットアップ**:

1. **Powers of Tau**: 汎用的なセットアップ（1回だけ）
   - 楕円曲線のべき乗を生成: $[1]G, [\tau]G, [\tau^2]G, \ldots, [\tau^{2^n}]G$
   - $\tau$ は秘密（セットアップ後に破棄）

2. **Circuit-specific Setup**: 回路ごとのセットアップ
   - 検証鍵（Verification Key）
   - 証明鍵（Proving Key）

---

## 数学的背景

### 楕円曲線暗号

#### 楕円曲線の定義

楕円曲線 $E$ は、以下の方程式を満たす点の集合:

$$
y^2 = x^3 + ax + b
$$

**例**: BN254曲線（Groth16で使用）
$$
y^2 = x^3 + 3
$$

#### 群演算

楕円曲線上の点の**加算**が定義されます:

$$
P + Q = R
$$

**性質**:
- 交換法則: $P + Q = Q + P$
- 結合法則: $(P + Q) + R = P + (Q + R)$
- 単位元: $\mathcal{O}$（無限遠点）

**スカラー倍**:
$$
nP = \underbrace{P + P + \cdots + P}_{n \text{回}}
$$

#### 離散対数問題（DLP）

$P, Q$ が与えられたとき、$Q = nP$ となる $n$ を求めることは困難。

$$
Q = nP \quad \text{が与えられても} \quad n = ?
$$

これが楕円曲線暗号の安全性の基礎。

### ペアリング（Bilinear Map）

#### 定義

ペアリングは、2つの楕円曲線群 $\mathbb{G}_1, \mathbb{G}_2$ からターゲット群 $\mathbb{G}_T$ への写像:

$$
e: \mathbb{G}_1 \times \mathbb{G}_2 \to \mathbb{G}_T
$$

#### 双線形性（Bilinearity）

$$
e(aP, bQ) = e(P, Q)^{ab}
$$

**重要な性質**:
$$
e(P_1 + P_2, Q) = e(P_1, Q) \cdot e(P_2, Q)
$$
$$
e(P, Q_1 + Q_2) = e(P, Q_1) \cdot e(P, Q_2)
$$

#### 非退化性（Non-degeneracy）

$$
\exists P, Q: e(P, Q) \neq 1
$$

#### ペアリングの計算例

BN254曲線の場合:

$$
e: \mathbb{G}_1 \times \mathbb{G}_2 \to \mathbb{F}_{p^{12}}
$$

- $\mathbb{G}_1$: $E(\mathbb{F}_p)$ の部分群
- $\mathbb{G}_2$: $E'(\mathbb{F}_{p^2})$ の部分群
- $\mathbb{G}_T$: $\mathbb{F}_{p^{12}}$ の乗法群

### QAP（Quadratic Arithmetic Program）

#### R1CS（Rank-1 Constraint System）

計算を**制約式**で表現。

各制約は以下の形:
$$
(a_1 w_1 + a_2 w_2 + \cdots)(b_1 w_1 + b_2 w_2 + \cdots) = c_1 w_1 + c_2 w_2 + \cdots
$$

**例**: $x \times y = z$ を検証

変数: $w = (1, x, y, z)$（$w_0 = 1$ は定数）

制約:
$$
(w_1) \times (w_2) = w_3
$$

つまり:
$$
(0 \cdot w_0 + 1 \cdot w_1 + 0 \cdot w_2 + 0 \cdot w_3) \times (0 \cdot w_0 + 0 \cdot w_1 + 1 \cdot w_2 + 0 \cdot w_3) = 0 \cdot w_0 + 0 \cdot w_1 + 0 \cdot w_2 + 1 \cdot w_3
$$

#### QAPへの変換

R1CS を**多項式**で表現。

$m$ 個の制約、$n$ 個の変数の場合:

**多項式**: $A_i(x), B_i(x), C_i(x)$ for $i = 0, 1, \ldots, n$

**QAP の条件**:

$$
\left( \sum_{i=0}^{n} w_i A_i(x) \right) \times \left( \sum_{i=0}^{n} w_i B_i(x) \right) - \left( \sum_{i=0}^{n} w_i C_i(x) \right) = H(x) \cdot Z(x)
$$

ここで:
- $Z(x) = (x - r_1)(x - r_2) \cdots (x - r_m)$: ターゲット多項式
- $H(x)$: 商多項式

**重要**: この等式が成り立つ ⇔ すべての制約が満たされる

---

## 証明生成と検証の仕組み

### セットアップ（Setup）

#### 1. Powers of Tau（信頼されたセットアップ）

秘密の値 $\tau$ を使って、楕円曲線点を生成:

$$
[\tau^0]G, [\tau^1]G, [\tau^2]G, \ldots, [\tau^d]G
$$

同様に、$\alpha, \beta, \gamma, \delta$ に対しても生成。

**重要**: $\tau, \alpha, \beta, \gamma, \delta$ は**破棄**される（有毒廃棄物）

#### 2. Circuit-specific Setup

回路 $C$ に対して、証明鍵と検証鍵を生成。

**証明鍵（Proving Key）**:
$$
pk = \left( [\tau^i]G_1, [\alpha \tau^i]G_1, [\beta \tau^i]G_1, \ldots \right)
$$

**検証鍵（Verification Key）**:
$$
vk = \left( [\alpha]G_1, [\beta]G_2, [\gamma]G_2, [\delta]G_2, \text{IC}_0, \text{IC}_1, \ldots \right)
$$

### 証明生成（Prove）

#### 入力

- **公開入力** $x$: 検証者が知っている値
- **秘密入力** $w$: 証明者だけが知っている値
- **証明鍵** $pk$

#### 手順

1. **Witness 計算**: 回路を実行して、すべての中間変数を計算
   $$
   (w_0, w_1, \ldots, w_n) = \text{Compute}(x, w)
   $$

2. **多項式評価**: $A(x), B(x), C(x), H(x)$ を計算
   $$
   A(\tau) = \sum_{i=0}^{n} w_i A_i(\tau)
   $$
   $$
   B(\tau) = \sum_{i=0}^{n} w_i B_i(\tau)
   $$
   $$
   C(\tau) = \sum_{i=0}^{n} w_i C_i(\tau)
   $$

3. **証明の構築**: ランダム値 $r, s$ を選び、以下を計算
   $$
   A = \alpha + A(\tau) + r \delta
   $$
   $$
   B = \beta + B(\tau) + s \delta
   $$
   $$
   C = \frac{1}{\delta} \left( \sum_{i=l+1}^{n} w_i (\beta A_i(\tau) + \alpha B_i(\tau) + C_i(\tau)) + H(\tau) Z(\tau) \right) + A \cdot s + B \cdot r - rs\delta
   $$

   楕円曲線上で:
   $$
   [A]G_1, [B]G_2, [C]G_1
   $$

#### 出力

証明:
$$
\pi = ([A]G_1, [B]G_2, [C]G_1)
$$

サイズ: **128バイト**

### 検証（Verify）

#### 入力

- **証明** $\pi = (A, B, C)$
- **公開入力** $x$
- **検証鍵** $vk$

#### 手順

1. **公開入力の線形結合**:
   $$
   [\text{public}]G_1 = \sum_{i=0}^{l} x_i \cdot \text{IC}_i
   $$
   （$\text{IC}_i$ は検証鍵に含まれる）

2. **ペアリング検証**: 以下の等式を確認
   $$
   e(A, B) = e([\alpha]G_1, [\beta]G_2) \cdot e([\text{public}]G_1, [\gamma]G_2) \cdot e(C, [\delta]G_2)
   $$

#### 出力

- 等式が成立 → **Accept**（証明は正しい）
- 等式が不成立 → **Reject**（証明は偽）

### なぜこれがゼロ知識なのか

**証明 $\pi = (A, B, C)$ からは、秘密入力 $w$ の情報が漏れない**

理由:
- $A, B, C$ はランダム値 $r, s$ でマスクされている
- 楕円曲線の離散対数問題により、$A, B, C$ から元の値を復元できない
- ペアリング方程式は成立するが、具体的な $w$ は分からない

---

## 本システムでの利用

### Circom と snarkjs

本システムでは、**Circom** で回路を記述し、**snarkjs** で証明生成・検証を行います。

#### Circom: 回路記述言語

**例**: 年齢が20歳以上120歳以下であることを証明

```circom
template RangeCheck(min, max) {
    signal input value;
    signal output valid;

    // value >= min
    signal diff_min;
    diff_min <== value - min;
    component check_min = LessEqThan(8);  // 8ビット比較
    check_min.in[0] <== 0;
    check_min.in[1] <== diff_min;

    // value <= max
    signal diff_max;
    diff_max <== max - value;
    component check_max = LessEqThan(8);
    check_max.in[0] <== 0;
    check_max.in[1] <== diff_max;

    // Both conditions must be true
    valid <== check_min.out * check_max.out;
}

template MedicalDataVerification() {
    signal input age;
    signal input blood_pressure_systolic;
    signal input blood_pressure_diastolic;
    signal input blood_sugar;
    signal input cholesterol;
    signal input salt;  // ランダムソルト

    signal output dataHash;
    signal output isValid;

    // 範囲チェック
    component ageCheck = RangeCheck(0, 120);
    ageCheck.value <== age;

    component bpCheck = RangeCheck(80, 200);
    bpCheck.value <== blood_pressure_systolic;

    component bgCheck = RangeCheck(50, 300);
    bgCheck.value <== blood_sugar;

    // すべてのチェックが成功
    isValid <== ageCheck.valid * bpCheck.valid * bgCheck.valid;

    // データのハッシュを計算（改ざん検出）
    component hasher = Poseidon(6);
    hasher.inputs[0] <== age;
    hasher.inputs[1] <== blood_pressure_systolic;
    hasher.inputs[2] <== blood_pressure_diastolic;
    hasher.inputs[3] <== blood_sugar;
    hasher.inputs[4] <== cholesterol;
    hasher.inputs[5] <== salt;

    dataHash <== hasher.out;
}
```

#### Circom から R1CS への変換

Circom コンパイラが自動的に R1CS に変換。

```bash
circom data_verification.circom --r1cs --wasm --sym
```

**出力**:
- `data_verification.r1cs`: 制約システム
- `data_verification.wasm`: Witness 計算用
- `data_verification.sym`: シンボル情報

#### セットアップ

```bash
# Powers of Tau（汎用）
snarkjs powersoftau new bn128 14 pot14_0000.ptau
snarkjs powersoftau contribute pot14_0000.ptau pot14_0001.ptau

# Circuit-specific setup
snarkjs groth16 setup data_verification.r1cs pot14_0001.ptau circuit_0000.zkey
snarkjs zkey contribute circuit_0000.zkey circuit_final.zkey

# 検証鍵をエクスポート
snarkjs zkey export verificationkey circuit_final.zkey verification_key.json
```

#### 証明生成

```javascript
const snarkjs = require('snarkjs');
const fs = require('fs');

// 入力データ
const input = {
    age: 45,
    blood_pressure_systolic: 130,
    blood_pressure_diastolic: 85,
    blood_sugar: 110,
    cholesterol: 220,
    salt: 123456789  // ランダムソルト
};

// Witness 計算
const { proof, publicSignals } = await snarkjs.groth16.fullProve(
    input,
    "data_verification.wasm",
    "circuit_final.zkey"
);

// 証明を保存
fs.writeFileSync("proof.json", JSON.stringify(proof, null, 2));
fs.writeFileSync("public.json", JSON.stringify(publicSignals, null, 2));

console.log("Proof generated!");
console.log("Public signals:", publicSignals);
// publicSignals[0]: dataHash
// publicSignals[1]: isValid (1 = valid, 0 = invalid)
```

#### 検証

```javascript
const vKey = JSON.parse(fs.readFileSync("verification_key.json"));

const verified = await snarkjs.groth16.verify(
    vKey,
    publicSignals,
    proof
);

if (verified) {
    console.log("Verification OK");
    if (publicSignals[1] === "1") {
        console.log("Data is valid (within ranges)");
    }
} else {
    console.log("Invalid proof");
}
```

### 証明の内容

**証明**（128バイト）:
```json
{
  "pi_a": ["0x1a2b3c...", "0x4d5e6f...", "1"],
  "pi_b": [
    ["0x7g8h9i...", "0xjklmno..."],
    ["0xpqrstu...", "0xvwxyz0..."],
    ["1", "0"]
  ],
  "pi_c": ["0x123456...", "0x789abc...", "1"],
  "protocol": "groth16",
  "curve": "bn128"
}
```

**公開信号**:
```json
[
  "14532087652934876529348765",  // dataHash（Poseidon ハッシュ）
  "1"                             // isValid（1 = 有効）
]
```

**重要**:
- 証明からは `age`, `blood_pressure` などの値は**一切分からない**
- `dataHash` は暗号学的ハッシュなので、逆算不可能
- `isValid = 1` なら、データが正当な範囲内であることだけが分かる

---

## 具体例と実践

### 例1: 年齢確認（20歳以上を証明）

**シナリオ**: お酒を買いたいが、年齢を明かしたくない。

**回路**:
```circom
template AgeVerification() {
    signal input age;
    signal input salt;
    signal output ageHash;
    signal output isAdult;

    // age >= 20
    component check = GreaterEqThan(8);
    check.in[0] <== age;
    check.in[1] <== 20;
    isAdult <== check.out;

    // Hash for commitment
    component hasher = Poseidon(2);
    hasher.inputs[0] <== age;
    hasher.inputs[1] <== salt;
    ageHash <== hasher.out;
}
```

**証明生成**:
```javascript
const input = {
    age: 25,        // 秘密
    salt: 99999     // ランダム値
};

const { proof, publicSignals } = await snarkjs.groth16.fullProve(
    input,
    "age_verification.wasm",
    "age_verification.zkey"
);

// publicSignals[0]: ageHash
// publicSignals[1]: 1（20歳以上）
```

**検証**:
```javascript
const verified = await snarkjs.groth16.verify(vKey, publicSignals, proof);

if (verified && publicSignals[1] === "1") {
    console.log("この人は20歳以上です（年齢は不明）");
}
```

### 例2: 医療データの正当性証明

**シナリオ**: 病院が患者データを製薬会社に提供。データが改ざんされていないことを証明したいが、内容は秘密にしたい。

**回路**:
```circom
template MedicalDataIntegrity() {
    signal input patient_id;
    signal input diagnosis_code;
    signal input treatment_code;
    signal input hospital_signature;  // 病院の秘密署名

    signal output commitment;
    signal output isAuthentic;

    // 病院の署名検証（簡略化）
    component sigCheck = SignatureVerify();
    sigCheck.message <== diagnosis_code + treatment_code;
    sigCheck.signature <== hospital_signature;
    isAuthentic <== sigCheck.valid;

    // データのコミットメント
    component hasher = Poseidon(4);
    hasher.inputs[0] <== patient_id;
    hasher.inputs[1] <== diagnosis_code;
    hasher.inputs[2] <== treatment_code;
    hasher.inputs[3] <== hospital_signature;
    commitment <== hasher.out;
}
```

**利点**:
- 製薬会社は `commitment` を受け取る
- `isAuthentic = 1` なら、病院が正当に署名したデータと分かる
- しかし、`patient_id`, `diagnosis_code` などは一切分からない

### 例3: 統計的クエリ（範囲内の患者数）

**シナリオ**: 「血圧が130以上の患者は何人いるか？」を証明したい。

**回路**:
```circom
template CountInRange(N) {  // N人の患者
    signal input blood_pressures[N];
    signal input threshold;
    signal output count;

    signal partial_counts[N];
    partial_counts[0] <== 0;

    for (var i = 0; i < N; i++) {
        component check = GreaterEqThan(8);
        check.in[0] <== blood_pressures[i];
        check.in[1] <== threshold;

        if (i > 0) {
            partial_counts[i] <== partial_counts[i-1] + check.out;
        } else {
            partial_counts[i] <== check.out;
        }
    }

    count <== partial_counts[N-1];
}
```

**証明**:
```javascript
const input = {
    blood_pressures: [120, 135, 140, 125, 150, 110, 145],  // 秘密
    threshold: 130
};

const { proof, publicSignals } = await snarkjs.groth16.fullProve(
    input,
    "count_in_range.wasm",
    "count_in_range.zkey"
);

// publicSignals[0]: 4（130以上の患者数）
```

**結果**:
- 検証者は「4人の患者が血圧130以上」と分かる
- しかし、**どの患者が該当するか**、**具体的な血圧値**は分からない

---

## まとめ

### ゼロ知識証明の本質

1. **証明と秘密の分離**: 命題の真偽を証明しながら、証明に使った情報は隠す
2. **暗号学的保証**: 偽の証明は作れない（計算量的安全性）
3. **効率性**: 証明サイズは小さく、検証は高速

### Groth16 の特徴

- **最小の証明サイズ**: 128バイト（3つの楕円曲線点）
- **最速の検証**: 1つのペアリング方程式
- **成熟した実装**: Zcash、Filecoin、zkSync で実績
- **トレードオフ**: Trusted Setup が必要

### 本システムでの役割

- **データの正当性**: 医療データが規定の範囲内であることを証明
- **改ざん検出**: データのハッシュ（commitment）で整合性を保証
- **プライバシー保護**: 具体的な値は一切明かさない
- **信頼の構築**: 暗号化データが「本物」であることを保証

### zkSNARK の応用分野

1. **プライバシー保護暗号通貨**: Zcash, Tornado Cash
2. **スケーリング（Layer 2）**: zkSync, StarkNet, Polygon zkEVM
3. **認証・アイデンティティ**: 年齢確認、資格証明
4. **コンプライアンス**: 規制遵守の証明
5. **プライバシー保護機械学習**: 本システム

### 今後の展望

- **PLONK, Halo2**: より柔軟なセットアップ
- **Recursive SNARKs**: 証明の証明（無限の合成）
- **zkVM**: 汎用プログラムのゼロ知識実行
- **量子耐性**: STARKs などポスト量子暗号への移行
- **ハードウェア高速化**: ASIC、FPGA による高速化

---

## 参考文献

1. Goldwasser, S., Micali, S., & Rackoff, C. (1985). "The knowledge complexity of interactive proof-systems." *STOC 1985*.

2. Groth, J. (2016). "On the size of pairing-based non-interactive arguments." *EUROCRYPT 2016*.

3. Ben-Sasson, E., Chiesa, A., Tromer, E., & Virza, M. (2014). "Succinct non-interactive zero knowledge for a von Neumann architecture." *USENIX Security 2014*.

4. Zcash Protocol Specification. https://zips.z.cash/protocol/protocol.pdf

5. Circom Documentation. https://docs.circom.io/

6. snarkjs Documentation. https://github.com/iden3/snarkjs

7. Buterin, V. (2016-2017). "zk-SNARKs: Under the Hood." Blog series. https://medium.com/@VitalikButerin

8. Gabizon, A. (2017). "Explaining SNARKs." Blog series. https://electriccoin.co/blog/snark-explain/
