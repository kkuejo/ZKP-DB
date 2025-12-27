# 準同型暗号（Homomorphic Encryption）の技術的背景

## 目次

1. [準同型暗号とは何か](#準同型暗号とは何か)
2. [歴史的背景](#歴史的背景)
3. [準同型暗号の種類](#準同型暗号の種類)
4. [CKKS方式の詳細](#ckks方式の詳細)
5. [数学的背景](#数学的背景)
6. [暗号化と演算の仕組み](#暗号化と演算の仕組み)
7. [本システムでの利用](#本システムでの利用)
8. [具体例と実践](#具体例と実践)

---

## 準同型暗号とは何か

### 簡単な比喩で理解する

準同型暗号を「魔法の箱」に例えてみましょう。

**普通の暗号化**:
```
[100] → 暗号化 → [●●●] → 計算できない → 復号 → [100]
```
- データを箱に入れる（暗号化）
- 箱の中身を見るには鍵で開ける必要がある（復号）
- 箱を開けないと計算できない

**準同型暗号**:
```
[100] → 暗号化 → [●●●] → 箱のまま計算 → [●●●] → 復号 → [結果]
```
- データを魔法の箱に入れる（暗号化）
- **箱を開けずに、外から計算ができる**
- 最後に結果だけを取り出す（復号）

### 技術的な定義

準同型暗号は、**暗号化されたデータに対して、復号せずに演算を行える暗号方式**です。

数学的には、以下の性質を持ちます：

暗号化関数を $E(\cdot)$、復号関数を $D(\cdot)$ とすると、

**加法準同型性**:
$$
E(m_1) + E(m_2) = E(m_1 + m_2)
$$

**乗法準同型性**:
$$
E(m_1) \times E(m_2) = E(m_1 \times m_2)
$$

つまり、暗号化されたデータ同士を演算すると、**平文を演算した結果を暗号化したものと同じになる**という性質です。

---

## 歴史的背景

### 準同型暗号の発展

#### 1978年: RSA暗号（部分準同型暗号）

最初の公開鍵暗号であるRSAは、**乗法準同型性**を持っていました。

$$
E(m_1) \times E(m_2) \equiv (m_1 \times m_2)^e \pmod{n} = E(m_1 \times m_2)
$$

しかし、加法準同型性は持っていませんでした。

#### 1999年: Paillier暗号（部分準同型暗号）

**加法準同型性**を持つ暗号方式が登場。

$$
E(m_1) \times E(m_2) = E(m_1 + m_2)
$$

電子投票などに応用されましたが、乗算はできませんでした。

#### 2009年: Gentry の完全準同型暗号（FHE）

Craig Gentry がスタンフォード大学で、**世界初の完全準同型暗号**を発表。

- 加算も乗算も**無制限**にできる
- しかし、計算コストが非常に高い（実用化は困難）

#### 2016年: CKKS方式の登場

Cheon-Kim-Kim-Song が、**近似計算に特化した実用的な準同型暗号**を発表。

- 浮動小数点数の暗号化
- 機械学習や統計処理に最適
- **本システムで採用している方式**

---

## 準同型暗号の種類

### 1. 部分準同型暗号（PHE: Partially Homomorphic Encryption）

加算**または**乗算のいずれか一方のみをサポート。

**例**:
- **Paillier暗号**: 加算のみ
- **RSA暗号**: 乗算のみ

**用途**:
- 電子投票（Paillier）
- プライバシー保護データマイニング

### 2. やや準同型暗号（SHE: Somewhat Homomorphic Encryption）

加算と乗算の両方をサポートするが、**回数に制限がある**。

**制限の理由**:
- 演算のたびに「ノイズ」が増加
- ノイズが一定値を超えると復号不可能

**例**:
- BGV方式
- BFV方式

### 3. 完全準同型暗号（FHE: Fully Homomorphic Encryption）

加算と乗算を**無制限**に実行できる。

**実現方法**:
- **ブートストラッピング**: ノイズをクリアにする技術
- 計算コストが非常に高い（数千〜数万倍遅い）

**例**:
- Gentry の格子ベース方式
- TFHE（高速FHE）

### 4. CKKS方式（本システムで採用）

**近似計算**に特化した準同型暗号。

**特徴**:
- 浮動小数点数を暗号化
- 加算・乗算・スカラー倍が可能
- 乗算の回数に制限あり（**乗算深度**）
- 機械学習や統計処理に最適

**比較表**:

| 方式 | 加算 | 乗算 | 精度 | 速度 | 用途 |
|------|------|------|------|------|------|
| Paillier | ✅ 無制限 | ❌ | 完全 | 遅い | 投票 |
| BGV/BFV | ✅ | ✅ 制限あり | 完全 | 中程度 | 汎用 |
| CKKS | ✅ | ✅ 制限あり | **近似** | **高速** | **ML/統計** |
| TFHE | ✅ | ✅ 無制限 | 完全 | 非常に遅い | 論理回路 |

---

## CKKS方式の詳細

### なぜCKKSが機械学習に適しているのか

機械学習では、完全な精度は不要なことが多い：

```
例: 血圧の平均値
真の値: 127.8364291...
必要な精度: 127.8 または 128

→ 小数点以下の細かい誤差は許容できる
```

**CKKSの利点**:
- 浮動小数点数をネイティブサポート
- 近似計算により高速化
- ベクトル演算（SIMD）で並列処理

### CKKSの基本構造

#### 1. 平文空間

CKKS では、複素数のベクトルを暗号化します。

$$
\mathbf{m} = (m_0, m_1, \ldots, m_{N/2-1}) \in \mathbb{C}^{N/2}
$$

ここで、$N$ はスロット数（多項式の次数）。

#### 2. 多項式環

暗号文は、多項式環上の要素として表現されます。

$$
R = \mathbb{Z}[X] / (X^N + 1)
$$

- $N$ は2のべき乗（例: 4096, 8192, 16384）
- $X^N + 1$ は円分多項式

#### 3. スケーリング因子

浮動小数点数を整数に変換するためのスケール。

$$
\Delta = 2^{\text{scale}}
$$

例: $\text{scale} = 40$ なら、$\Delta = 2^{40} \approx 1.1 \times 10^{12}$

---

## 数学的背景

### Ring Learning With Errors（RLWE）問題

CKKS の安全性は、**RLWE問題**の計算困難性に基づきます。

#### RLWE問題とは

多項式環 $R_q = \mathbb{Z}_q[X]/(X^N+1)$ において：

**秘密鍵** $s \in R_q$ が与えられたとき、以下の式で生成されるサンプル $(a, b)$ を多数観測しても、$s$ を推測することは困難：

$$
b = a \cdot s + e \pmod{q}
$$

ここで：
- $a$: ランダムな多項式
- $s$: 秘密鍵（小さい係数の多項式）
- $e$: 小さいエラー（ノイズ）
- $q$: 大きな素数（モジュラス）

**直感的な理解**:
- $(a, b)$ のペアを見ても、ノイズ $e$ があるため $s$ を正確に計算できない
- ノイズが「暗号の安全性」を保証
- しかし、演算するたびにノイズが増加（これが乗算回数の制限につながる）

### 多項式環上の演算

#### 加算

$$
(a_1, b_1) + (a_2, b_2) = (a_1 + a_2, b_1 + b_2)
$$

**ノイズの増加**: $e_1 + e_2$（線形的）

#### 乗算

$$
(a_1, b_1) \times (a_2, b_2) = (c_0, c_1, c_2)
$$

その後、**再線形化（Relinearization）**を行い、$(a, b)$ の形に戻します。

**ノイズの増加**: $e_1 \cdot e_2$（指数的）

→ これが乗算回数に制限がある理由

---

## 暗号化と演算の仕組み

### 1. 鍵生成（KeyGen）

**秘密鍵** $s \in R$ を生成:
$$
s \leftarrow \chi_{\text{key}}
$$
（$\chi_{\text{key}}$ は小さい係数を持つ分布）

**公開鍵** $(pk_0, pk_1)$ を生成:
$$
pk_0 = -a \cdot s + e \pmod{q}
$$
$$
pk_1 = a
$$

**評価鍵**（再線形化キー、回転キーなど）も生成。

### 2. 暗号化（Encrypt）

平文 $\mathbf{m} \in \mathbb{C}^{N/2}$ を暗号化:

**Step 1**: エンコード（複素ベクトル → 多項式）
$$
m(X) = \text{Encode}(\mathbf{m}, \Delta)
$$
スケーリング因子 $\Delta$ を掛けて整数化。

**Step 2**: 暗号化
$$
ct_0 = pk_0 \cdot u + e_0 + m(X) \pmod{q}
$$
$$
ct_1 = pk_1 \cdot u + e_1 \pmod{q}
$$

ここで：
- $u$: ランダム多項式
- $e_0, e_1$: 小さいノイズ

**暗号文**: $ct = (ct_0, ct_1)$

### 3. 復号（Decrypt）

暗号文 $ct = (ct_0, ct_1)$ を復号:

$$
m(X) = ct_0 + ct_1 \cdot s \pmod{q}
$$

**Step 1**: ノイズを含む多項式を取得
$$
m(X) + e_{\text{total}}
$$

**Step 2**: スケーリング因子で割る
$$
\mathbf{m} \approx \frac{m(X)}{\Delta}
$$

**Step 3**: デコード（多項式 → 複素ベクトル）
$$
\mathbf{m} = \text{Decode}(m(X) / \Delta)
$$

### 4. 準同型加算（Add）

$$
ct_{\text{add}} = ct_1 + ct_2
$$
$$
= (ct_{1,0} + ct_{2,0}, ct_{1,1} + ct_{2,1})
$$

**復号すると**:
$$
(ct_{1,0} + ct_{2,0}) + (ct_{1,1} + ct_{2,1}) \cdot s = m_1 + m_2 + (e_1 + e_2)
$$

→ 平文 $m_1 + m_2$ が得られる（ノイズは加算される）

### 5. 準同型乗算（Multiply）

**Step 1**: テンソル積
$$
ct_{\text{mult}} = ct_1 \otimes ct_2
$$
$$
= (ct_{1,0} \cdot ct_{2,0}, \ ct_{1,0} \cdot ct_{2,1} + ct_{1,1} \cdot ct_{2,0}, \ ct_{1,1} \cdot ct_{2,1})
$$

この時点で暗号文は3つの要素を持つ。

**Step 2**: 再線形化（Relinearization）

評価鍵 $evk$ を使って、3要素を2要素に戻す:
$$
ct_{\text{relin}} = (c_0, c_1)
$$

**Step 3**: リスケーリング（Rescaling）

スケーリング因子が $\Delta^2$ になっているので、$\Delta$ に戻す:
$$
ct_{\text{rescale}} = \left\lfloor \frac{ct_{\text{relin}}}{p} \right\rceil
$$
（$p$ は特殊な素数）

**復号すると**:
$$
m_1 \times m_2 + e_{\text{mult}}
$$

→ 平文 $m_1 \times m_2$ が得られる（ノイズは乗算される）

### 6. スカラー倍（Scalar Multiplication）

定数 $c$ を掛ける:
$$
ct_{\text{scalar}} = c \cdot ct
$$

これは暗号化されていない定数なので、**ノイズが増えない**。

---

## 本システムでの利用

### TenSEAL ライブラリ

本システムでは、Microsoft SEAL をベースにした **TenSEAL** を使用しています。

```python
import tenseal as ts

# コンテキスト作成
context = ts.context(
    ts.SCHEME_TYPE.CKKS,
    poly_modulus_degree=8192,   # N = 8192（セキュリティパラメータ）
    coeff_mod_bit_sizes=[60, 40, 40, 60]  # モジュラスチェーン
)
context.generate_galois_keys()      # 回転キー
context.generate_relin_keys()       # 再線形化キー
context.global_scale = 2**40        # スケール Δ = 2^40
```

### パラメータの意味

#### poly_modulus_degree = 8192

- 多項式の次数 $N = 8192$
- **セキュリティレベル**: 128ビット（現代の標準）
- スロット数: $N/2 = 4096$（4096個の数値を並列処理）

**セキュリティとの関係**:
$$
\log_2(q) \lesssim N / (\text{安全係数})
$$

$N = 8192$ なら、$\log_2(q) \lesssim 218$ ビット程度まで安全。

#### coeff_mod_bit_sizes = [60, 40, 40, 60]

モジュラスチェーン（RNS表現）:
$$
q = q_0 \times q_1 \times q_2 \times q_3
$$

各 $q_i$ のビット数: 60, 40, 40, 60

**合計**: $60 + 40 + 40 + 60 = 200$ ビット

**意味**:
- 最初の $q_0$ (60ビット): フレッシュな暗号文用
- 中間の $q_1, q_2$ (40ビット): 乗算ごとにリスケール
- 最後の $q_3$ (60ビット): 最終結果用

**乗算深度**:
- リスケールできる回数 = モジュラス数 - 1 = **3回**
- つまり、**3〜4回の乗算**が可能

#### global_scale = 2^40

スケーリング因子:
$$
\Delta = 2^{40} \approx 1.1 \times 10^{12}
$$

**精度との関係**:
$$
\text{精度} \approx \frac{q}{\Delta} \approx 2^{200-40} = 2^{160}
$$

→ 十分な精度（約48桁の10進数）

### 実際の暗号化と計算

```python
# 平文データ
data1 = [100.5, 120.3, 95.7]
data2 = [80.2, 90.1, 110.5]

# 暗号化
enc_data1 = ts.ckks_vector(context, data1)
enc_data2 = ts.ckks_vector(context, data2)

# 準同型加算
enc_sum = enc_data1 + enc_data2
print(enc_sum.decrypt())  # [180.7, 210.4, 206.2]

# 準同型乗算
enc_product = enc_data1 * enc_data2
print(enc_product.decrypt())  # [8060.1, 10842.03, 10574.85]

# スカラー倍
enc_scaled = enc_data1 * 2.0
print(enc_scaled.decrypt())  # [201.0, 240.6, 191.4]
```

### 医療データでの具体例

```python
# 100人の患者の血圧データ（暗号化）
blood_pressures_encrypted = [
    ts.ckks_vector(context, [patient.bp]) for patient in patients
]

# 暗号化されたまま平均を計算
total = blood_pressures_encrypted[0]
for enc_bp in blood_pressures_encrypted[1:]:
    total = total + enc_bp  # 準同型加算

average = total * (1.0 / 100)  # スカラー倍

# 復号して結果を取得
avg_bp = average.decrypt()[0]
print(f"平均血圧: {avg_bp:.1f} mmHg")
```

**重要なポイント**:
- データは暗号化されたまま
- 秘密鍵を持つのはデータ提供者のみ
- データ購入者は暗号化されたデータで計算
- 結果のみを復号して取得

---

## 具体例と実践

### 例1: 暗号化された統計処理

**シナリオ**: 病院が患者の血糖値データを暗号化して、製薬会社に提供。製薬会社は平均値と標準偏差を計算。

**データ**:
$$
\mathbf{x} = (110, 95, 130, 105, 115, 100, 125, 90, 135, 120)
$$

**暗号化**:
$$
E(\mathbf{x}) = \text{Encrypt}(\mathbf{x})
$$

**平均の計算**:
$$
\bar{x} = \frac{1}{n} \sum_{i=1}^{n} x_i
$$

暗号化されたまま:
$$
E(\bar{x}) = E\left(\frac{1}{n}\right) \cdot \sum_{i=1}^{n} E(x_i)
$$
$$
= \frac{1}{n} \cdot \left( E(x_1) + E(x_2) + \cdots + E(x_{10}) \right)
$$

**分散の計算**:
$$
\sigma^2 = \frac{1}{n} \sum_{i=1}^{n} (x_i - \bar{x})^2
$$

暗号化されたまま:
$$
E(\sigma^2) = \frac{1}{n} \cdot \sum_{i=1}^{n} \left(E(x_i) - E(\bar{x})\right)^2
$$

ここで、減算と乗算を準同型演算で実行。

**復号**:
$$
\bar{x} = D(E(\bar{x})) \approx 112.5
$$
$$
\sigma = \sqrt{D(E(\sigma^2))} \approx 14.7
$$

### 例2: 暗号化された線形回帰

**シナリオ**: 年齢 $x$ から血圧 $y$ を予測するモデル $y = wx + b$ を訓練。

**データ**:
- 年齢: $\mathbf{x} = (30, 40, 50, 60, 70)$
- 血圧: $\mathbf{y} = (110, 120, 130, 140, 150)$

**モデル**: 最小二乗法で $w, b$ を求める。

$$
w = \frac{n \sum xy - \sum x \sum y}{n \sum x^2 - (\sum x)^2}
$$

**暗号化されたデータで計算**:

1. $\sum E(x) \cdot E(y)$ （準同型乗算）
2. $\sum E(x)$ （準同型加算）
3. $\sum E(y)$ （準同型加算）
4. $\sum E(x)^2$ （準同型乗算）

すべて暗号化されたまま計算可能！

**結果**:
$$
w \approx 1.0, \quad b \approx 80
$$

予測モデル: $y = 1.0x + 80$

### 例3: ノイズの増加と乗算深度

**実験**: 1.0 を暗号化して、繰り返し2倍にする。

```python
x = ts.ckks_vector(context, [1.0])

# 1回目: 1.0 * 2 = 2.0
x = x * 2.0
print(x.decrypt())  # [2.0]  誤差: ±0.001

# 2回目: 2.0 * 2 = 4.0
x = x * 2.0
print(x.decrypt())  # [4.0]  誤差: ±0.01

# 3回目: 4.0 * 2 = 8.0
x = x * 2.0
print(x.decrypt())  # [8.0]  誤差: ±0.1

# 4回目: 8.0 * 2 = 16.0（限界）
x = x * 2.0
print(x.decrypt())  # [16.0]  誤差: ±1.0

# 5回目: エラー（乗算深度超過）
x = x * 2.0  # RuntimeError: scale out of bounds
```

**観察**:
- 乗算のたびにノイズが増加
- 4回目で誤差が大きくなる
- 5回目で復号不可能

**対策**:
- 計算グラフを最適化
- 不要な乗算を削減
- より大きな $N$ を使用（例: 16384）

---

## まとめ

### 準同型暗号の本質

1. **暗号化されたまま計算**: データを秘密にしたまま処理可能
2. **RLWE問題**: 格子暗号理論に基づく高い安全性
3. **ノイズ管理**: 演算のたびにノイズが増加 → 乗算回数に制限

### CKKS方式の特徴

- **浮動小数点数**: 実数・複素数を直接扱える
- **近似計算**: 機械学習や統計処理に最適
- **SIMD**: ベクトル演算で高速化
- **乗算深度**: 3〜4回の制限（パラメータ調整で増減可能）

### 本システムでの役割

- **医療データの秘匿**: 患者情報を暗号化
- **プライバシー保護分析**: 暗号化されたまま統計・ML
- **データ提供者の安心**: 秘密鍵を手放さない
- **データ購入者の利便性**: 暗号化データで研究可能

### 今後の展望

- **より深い乗算**: アルゴリズム最適化、大きいパラメータ
- **ブートストラッピング**: 無制限の計算（まだ遅い）
- **ハードウェア高速化**: GPU/FPGA対応
- **標準化**: CKKS の国際標準化（進行中）

---

## 参考文献

1. Cheon, J. H., Kim, A., Kim, M., & Song, Y. (2017). "Homomorphic encryption for arithmetic of approximate numbers." *ASIACRYPT 2017*.

2. Halevi, S., & Shoup, V. (2014). "Algorithms in HElib." *CRYPTO 2014*.

3. Microsoft Research. "Microsoft SEAL: Fast and Easy Homomorphic Encryption Library." https://github.com/microsoft/SEAL

4. OpenMined. "TenSEAL: A library for doing homomorphic encryption operations on tensors." https://github.com/OpenMined/TenSEAL

5. Gentry, C. (2009). "A fully homomorphic encryption scheme." *PhD thesis, Stanford University*.

6. Smart, N. P., & Vercauteren, F. (2014). "Fully homomorphic SIMD operations." *Designs, Codes and Cryptography, 71*(1), 57-81.
