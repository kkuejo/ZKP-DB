# 差分プライバシーとは何をするのか？

## 短い回答

**差分プライバシーは、結果にノイズ（ランダムな誤差）を加えることで、「あなたがデータに含まれているかどうか」を第三者に推測されないようにする技術です。**

---

## 問題: なぜ差分プライバシーが必要なのか？

### シナリオ: 病院の患者データ

```
病院A: 糖尿病患者100人のデータを持っている
製薬会社B: このデータを使って統計分析をしたい
患者C（山田太郎さん）: 自分のデータが含まれることに同意
```

### 問題1: 統計結果から個人の参加がバレる

```python
# 製薬会社が2回統計を取得できたとする

# 1回目: 山田さんを含む100人のデータ
query1 = "糖尿病患者の平均年齢は？"
answer1 = 55.2歳

# 2回目: 山田さんを除く99人のデータ
query2 = "糖尿病患者の平均年齢は？"
answer2 = 55.0歳

# 攻撃: 差を計算
difference = answer1 - answer2 = 0.2歳

# 山田さんの年齢を逆算
yamada_age = 55.0 + 0.2 * 100 = 55.0 + 20 = 75歳

# 結論: 山田さん（75歳）がこのデータセットに含まれていたことが判明！
```

**問題**: 統計結果が少し違うだけで、個人の参加と属性がバレる。

---

### 問題2: モデルから個人の存在を推測できる

```python
# モデル学習
model1 = train_model(100人のデータ)  # 山田さんを含む
model2 = train_model(99人のデータ)   # 山田さんを除く

# 山田さんのデータでテスト
loss1 = model1.loss(yamada_data)  # 損失: 0.01（小さい）
loss2 = model2.loss(yamada_data)  # 損失: 0.15（大きい）

# 攻撃: model1は山田さんをよく予測できる
# → 山田さんはmodel1の訓練データに含まれていた！
```

**問題**: モデルの性能から、個人の参加がバレる（メンバーシップ推論攻撃）。

---

## 解決策: 差分プライバシー

### 基本アイデア

**「あなたがいてもいなくても、結果がほとんど変わらない」ようにする。**

### どうやって？

**結果にランダムなノイズを加える。**

---

## 具体例1: 平均年齢の計算

### 差分プライバシーなし（危険）

```python
# データ
患者1-100: 年齢の平均 = 55.2歳

# クエリ: 平均年齢は？
answer = 55.2歳  # ← 正確な値を返す

# 問題: 正確すぎると、個人の影響を検出できる
```

### 差分プライバシーあり（安全）

```python
# データ
患者1-100: 年齢の平均 = 55.2歳

# ステップ1: 正確な平均を計算
true_average = 55.2歳

# ステップ2: ランダムノイズを生成
noise = random_laplace(scale=1.0)  # 例: +0.7

# ステップ3: ノイズを加えて返す
answer = 55.2 + 0.7 = 55.9歳  # ← わずかにずれた値

# 効果: 真の値が55.2なのか55.9なのか分からない
#       → 個人の影響を検出できない
```

---

## なぜノイズで個人を保護できるのか？

### 差分プライバシーなしの場合

```python
# 山田さんを含む100人
average_with_yamada = 55.2歳

# 山田さんを除く99人
average_without_yamada = 55.0歳

# 差: 0.2歳
# → 山田さんの影響が明確に見える
# → 山田さんの年齢を逆算できる
```

### 差分プライバシーありの場合

```python
# 山田さんを含む100人
true_average1 = 55.2歳
noise1 = +0.7歳（ランダム）
answer1 = 55.2 + 0.7 = 55.9歳

# 山田さんを除く99人
true_average2 = 55.0歳
noise2 = -0.3歳（ランダム）
answer2 = 55.0 - 0.3 = 54.7歳

# 差: 55.9 - 54.7 = 1.2歳
# → でも、これは主にノイズの影響（0.7 - (-0.3) = 1.0）
# → 山田さんの実際の影響（0.2）が隠される
```

**効果**: ノイズがあるため、山田さんの影響を正確に測定できない。

---

## 数学的定義（簡略版）

### 差分プライバシーの保証

メカニズム $M$（統計分析の方法）が**ε-差分プライバシー**を満たす ⇔

```
「1人追加/削除しても、結果の分布がほぼ同じ」
```

**数式**:

$$
\Pr[M(D) = r] \leq e^\epsilon \cdot \Pr[M(D') = r]
$$

ここで：
- $D$ と $D'$ は1人だけ異なるデータセット
- $r$ は任意の結果
- $\epsilon$ (イプシロン) はプライバシーパラメータ

### イプシロン（ε）の意味

| ε値 | プライバシー | 意味 |
|-----|------------|------|
| ε = 0 | 完璧 | 結果が完全に同じ（無限ノイズ、使い物にならない） |
| ε = 0.1 | 非常に強い | 結果がほぼ同じ（個人の影響をほぼ検出不可） |
| ε = 1.0 | 強い | 結果は最大2.7倍違う（推奨値） |
| ε = 10.0 | 弱い | 結果は最大22,000倍違う（ほぼ保護なし） |

**推奨値**: ε = 0.1 ~ 1.0

---

## 具体例2: データベースクエリ

### シナリオ

```
病院のデータベース: 1000人の患者
クエリ: 「糖尿病患者は何人？」
```

### 差分プライバシーなし

```python
# 正確なカウント
count = 234人

# 問題: もし山田さんが加わると...
count_with_yamada = 235人

# 差: 1人
# → 山田さんが糖尿病患者だとバレる
```

### 差分プライバシーあり

```python
# 正確なカウント
true_count = 234人

# Laplace機構でノイズを追加
noise = random_laplace(scale=1/ε)  # ε=1.0なら scale=1
# 例: noise = +3

# ノイズ付きカウント
answer = 234 + 3 = 237人

# 山田さんが加わった場合
true_count2 = 235人
noise2 = -2  # 別のランダムノイズ
answer2 = 235 - 2 = 233人

# 結果: 237人 → 233人
# → 山田さんが加わったのに減った！
# → これはノイズのせい
# → 山田さんの影響を検出できない
```

---

## Laplace機構（最も基本的な差分プライバシー実装）

### 仕組み

```python
def laplace_mechanism(true_value, sensitivity, epsilon):
    """
    Laplace機構で差分プライバシーを実現

    Args:
        true_value: 真の値
        sensitivity: 感度（1人変わると最大いくつ変わるか）
        epsilon: プライバシーパラメータ

    Returns:
        ノイズ付きの値
    """
    # Laplaceノイズを生成
    scale = sensitivity / epsilon
    noise = np.random.laplace(0, scale)

    # ノイズを加える
    return true_value + noise
```

### 例: 平均年齢

```python
# 真の平均年齢
true_average = 55.2

# 感度を計算
# 1人の年齢が変わると、平均はどれくらい変わる？
# 年齢範囲: 0-120歳
# データ数: 100人
sensitivity = (120 - 0) / 100 = 1.2

# プライバシーパラメータ
epsilon = 1.0

# Laplace機構を適用
noisy_average = laplace_mechanism(55.2, sensitivity=1.2, epsilon=1.0)
# 例: 55.2 + 0.7 = 55.9

print(f"真の平均: {true_average}歳")
print(f"ノイズ付き: {noisy_average}歳")
# 出力:
# 真の平均: 55.2歳
# ノイズ付き: 55.9歳
```

---

## 具体例3: 機械学習モデル

### シナリオ

```
訓練データ: 1000人の患者
モデル: 糖尿病リスク予測（線形回帰）
```

### 差分プライバシーなし

```python
# モデル学習
model = train_model(1000人のデータ)
params = [β0=80.0, β1=1.0]

# 問題: 山田さんを含む/含まないでモデルを比較すると...
model_with = train_model(1000人)     # params = [80.0, 1.0]
model_without = train_model(999人)   # params = [79.95, 0.998]

# 差: わずかだが検出可能
# → メンバーシップ推論攻撃が成立
```

### 差分プライバシーあり（DP-SGD）

```python
# 差分プライバシー勾配降下法（DP-SGD）
model = train_dp_model(1000人のデータ, epsilon=1.0)

# ステップ1: 通常の学習
params = [β0=80.0, β1=1.0]

# ステップ2: 各パラメータにノイズを追加
noise = [random_laplace(0, 0.5), random_laplace(0, 0.01)]
# 例: noise = [+0.3, -0.02]

# ステップ3: ノイズ付きパラメータ
noisy_params = [80.0+0.3, 1.0-0.02] = [80.3, 0.98]

# 山田さんを含む/含まないでモデルを比較しても...
model_with = [80.3, 0.98]   # ノイズ: [+0.3, -0.02]
model_without = [79.7, 1.01] # ノイズ: [-0.25, +0.03]

# ノイズが大きいため、山田さんの影響を検出できない
```

---

## ノイズの大きさ: トレードオフ

### ノイズが小さい（εが大きい）

```python
epsilon = 10.0  # プライバシー保護が弱い
noise = random_laplace(0, scale=1.2/10.0) = random_laplace(0, 0.12)
# ノイズ: 例 +0.08

true_average = 55.2
noisy_average = 55.2 + 0.08 = 55.28

# メリット: 正確
# デメリット: プライバシー保護が弱い
```

### ノイズが大きい（εが小さい）

```python
epsilon = 0.1  # プライバシー保護が非常に強い
noise = random_laplace(0, scale=1.2/0.1) = random_laplace(0, 12.0)
# ノイズ: 例 +8.5

true_average = 55.2
noisy_average = 55.2 + 8.5 = 63.7

# メリット: プライバシー保護が非常に強い
# デメリット: 不正確（真の値55.2が63.7に！）
```

### バランス

| ε | ノイズ規模 | 精度 | プライバシー | 推奨用途 |
|---|---------|------|------------|---------|
| 0.1 | 非常に大きい | 低い | 非常に強い | 極秘データ |
| 1.0 | 中程度 | 中程度 | 強い | **推奨値** |
| 10.0 | 小さい | 高い | 弱い | プライバシー重要度低 |

---

## プライバシーバジェット: 累積的なプライバシー損失

### 問題: 複数回クエリするとプライバシーが失われる

```python
# 1回目のクエリ（ε=1.0）
query1 = "平均年齢は？"
answer1 = 55.9歳（ノイズ付き）

# 2回目のクエリ（ε=1.0）
query2 = "平均血圧は？"
answer2 = 127.3 mmHg（ノイズ付き）

# 3回目のクエリ（ε=1.0）
query3 = "平均血糖値は？"
answer3 = 103.7 mg/dL（ノイズ付き）

# 問題: 複数のクエリを組み合わせると、個人の情報が漏洩する可能性
# 累積プライバシー損失: ε_total = ε1 + ε2 + ε3 = 1.0 + 1.0 + 1.0 = 3.0
```

### 解決策: プライバシーバジェット管理

```python
class PrivacyBudgetManager:
    def __init__(self, total_budget=10.0):
        self.total_budget = 10.0  # 合計でε=10.0まで許可
        self.used_budget = 0.0

    def request_query(self, query, epsilon):
        # 残りバジェットをチェック
        remaining = self.total_budget - self.used_budget

        if epsilon > remaining:
            raise ValueError(f"予算不足: 残り{remaining}, 必要{epsilon}")

        # クエリを実行
        result = execute_query_with_dp(query, epsilon)

        # バジェットを消費
        self.used_budget += epsilon

        return result

# 使用例
budget = PrivacyBudgetManager(total_budget=10.0)

# クエリ1（ε=1.0）
answer1 = budget.request_query("平均年齢", epsilon=1.0)
# 残りバジェット: 9.0

# クエリ2-10（各ε=1.0）
...

# クエリ11（ε=1.0）
try:
    answer11 = budget.request_query("平均コレステロール", epsilon=1.0)
except ValueError:
    print("プライバシーバジェットを使い果たしました")
```

---

## まとめ: 差分プライバシーは何をするのか？

### 簡単に言うと

**結果にランダムなノイズを加えることで、「あなたがデータに含まれているかどうか」を第三者に推測されないようにする。**

### 3つの重要ポイント

#### 1. **ノイズを加える**

```
真の値: 55.2歳
ノイズ: +0.7歳
結果: 55.9歳
```

#### 2. **個人の影響を隠す**

```
山田さんがいる: 55.9歳（ノイズ含む）
山田さんがいない: 54.7歳（ノイズ含む）
→ 差は主にノイズのせい
→ 山田さんの実際の影響（0.2歳）が隠される
```

#### 3. **数学的保証**

```
ε-差分プライバシー:
「1人追加/削除しても、結果の分布は最大e^ε倍しか変わらない」

ε=1.0なら: e^1 ≈ 2.7倍
→ 十分小さい
```

---

## 差分プライバシーの利点

### 1. **数学的に証明可能**

他のプライバシー保護技術（k匿名性など）と違い、数学的に厳密な保証がある。

### 2. **あらゆる攻撃に対して頑健**

- メンバーシップ推論攻撃: ✅ 防げる
- モデル反転攻撃: ✅ 防げる
- バックグラウンド知識攻撃: ✅ 防げる
- 将来の未知の攻撃: ✅ 防げる

### 3. **複数クエリの累積的影響を管理できる**

プライバシーバジェットで、累積的なプライバシー損失を制御。

---

## 差分プライバシーの欠点

### 1. **精度の低下**

ノイズを加えるため、結果が不正確になる。

```
真の平均: 55.2歳
ノイズ付き: 55.9歳
誤差: 0.7歳
```

### 2. **トレードオフ**

プライバシー ⇔ 精度

- 強いプライバシー（ε小）: 大きなノイズ → 不正確
- 弱いプライバシー（ε大）: 小さなノイズ → 正確

### 3. **複雑な実装**

正しく実装するのが難しい（感度計算、ノイズ生成、バジェット管理など）。

---

## 実装例: 完全なコード

```python
import numpy as np

class DifferentialPrivacy:
    """差分プライバシーの実装"""

    def __init__(self, epsilon=1.0, delta=1e-5):
        """
        Args:
            epsilon: プライバシーパラメータ（小さいほど強い保護）
            delta: 失敗確率（通常は非常に小さい値）
        """
        self.epsilon = epsilon
        self.delta = delta

    def laplace_mechanism(self, true_value, sensitivity):
        """
        Laplace機構で差分プライバシーを実現

        Args:
            true_value: 真の値（スカラーまたは配列）
            sensitivity: 感度（1人変わると最大いくつ変わるか）

        Returns:
            ノイズ付きの値
        """
        scale = sensitivity / self.epsilon

        if isinstance(true_value, np.ndarray):
            noise = np.random.laplace(0, scale, size=true_value.shape)
        else:
            noise = np.random.laplace(0, scale)

        return true_value + noise

    def gaussian_mechanism(self, true_value, sensitivity):
        """
        Gaussian機構で差分プライバシーを実現（(ε,δ)-DP）

        Args:
            true_value: 真の値
            sensitivity: 感度

        Returns:
            ノイズ付きの値
        """
        # Gaussianノイズのスケール
        scale = sensitivity * np.sqrt(2 * np.log(1.25 / self.delta)) / self.epsilon

        if isinstance(true_value, np.ndarray):
            noise = np.random.normal(0, scale, size=true_value.shape)
        else:
            noise = np.random.normal(0, scale)

        return true_value + noise

# 使用例1: 平均年齢の計算
ages = [45, 50, 55, 60, 65, 70, 48, 52, 58, 62]  # 10人の年齢

# 真の平均
true_average = np.mean(ages)
print(f"真の平均年齢: {true_average:.1f}歳")

# 差分プライバシーを適用
dp = DifferentialPrivacy(epsilon=1.0)
sensitivity = (120 - 0) / len(ages)  # (最大 - 最小) / データ数
noisy_average = dp.laplace_mechanism(true_average, sensitivity)
print(f"ノイズ付き平均年齢: {noisy_average:.1f}歳")
print(f"誤差: {abs(noisy_average - true_average):.1f}歳")

# 出力例:
# 真の平均年齢: 56.5歳
# ノイズ付き平均年齢: 57.2歳
# 誤差: 0.7歳

# 使用例2: カウントクエリ
count = 234  # 糖尿病患者数

# 真のカウント
print(f"真のカウント: {count}人")

# 差分プライバシーを適用
dp = DifferentialPrivacy(epsilon=1.0)
sensitivity = 1  # カウントの感度は常に1
noisy_count = dp.laplace_mechanism(count, sensitivity)
print(f"ノイズ付きカウント: {int(round(noisy_count))}人")

# 出力例:
# 真のカウント: 234人
# ノイズ付きカウント: 237人

# 使用例3: モデルパラメータ
model_params = np.array([80.0, 1.0, 0.5])  # β0, β1, β2

# 真のパラメータ
print(f"真のパラメータ: {model_params}")

# 差分プライバシーを適用
dp = DifferentialPrivacy(epsilon=1.0)
sensitivity = 0.01  # モデルパラメータの感度（データセット依存）
noisy_params = dp.laplace_mechanism(model_params, sensitivity)
print(f"ノイズ付きパラメータ: {noisy_params}")

# 出力例:
# 真のパラメータ: [80.   1.   0.5 ]
# ノイズ付きパラメータ: [80.012  0.998  0.503]
```

---

## 視覚的な説明

### ノイズなし vs ノイズあり

```
【ノイズなし】
クエリ1（山田さん含む）: 55.2歳
クエリ2（山田さん除く）: 55.0歳
差: 0.2歳 → 山田さんの年齢を逆算可能


【ノイズあり（ε=1.0）】
クエリ1（山田さん含む）: 55.2 + 0.7 = 55.9歳
クエリ2（山田さん除く）: 55.0 - 0.3 = 54.7歳
差: 1.2歳 → でもこれは主にノイズ（1.0）のせい
            真の差（0.2）が隠される
```

### Laplaceノイズの分布

```
       |
       |
   0.5 |    *
       |   * *
   0.4 |  *   *
       | *     *
   0.3 |*       *
       |         *
   0.2 |          *
       |           *
   0.1 |            *
       |_____________*___________
      -4  -2   0   2   4   6

中心（0）で最も確率が高く、離れるほど低い
ほとんどのノイズは -2 ~ +2 の範囲
```

---

## 最終まとめ

### 差分プライバシーとは？

**統計結果にランダムノイズを加えることで、個人の参加を推測不可能にする技術。**

### 何を保護する？

**「あなたがデータに含まれているかどうか」**

### どうやって？

**Laplaceノイズ（またはGaussianノイズ）を加える**

### いつ使う？

- 統計クエリの結果を返すとき
- 機械学習モデルのパラメータを返すとき
- 個人の参加がバレると困るとき

### トレードオフ

**プライバシー ⇔ 精度**

- ε小さい（0.1）: 強いプライバシー、大きなノイズ、低い精度
- ε中程度（1.0）: バランス（推奨）
- ε大きい（10.0）: 弱いプライバシー、小さなノイズ、高い精度

### 推奨値

**ε = 1.0（1つのクエリ/モデルあたり）**
**総プライバシーバジェット = 10.0（データセットの生涯）**

---

## 本システムでの実装（ZKP-DB）

### 実装クラス

本システムでは `backend/security_checks.py` に差分プライバシーが実装されています。

```python
from security_checks import DifferentialPrivacy, NoiseType

# インスタンス作成（ε=1.0, δ=1e-5）
dp = DifferentialPrivacy(epsilon=1.0, delta=1e-5)
```

### 機能一覧

| 機能 | メソッド | 説明 |
|------|----------|------|
| Laplace機構 | `add_laplace_noise()` | (ε)-差分プライバシー |
| Gaussian機構 | `add_gaussian_noise()` | (ε, δ)-差分プライバシー |
| 感度計算 | `calculate_sensitivity()` | クエリの感度を自動計算 |
| 結果へのノイズ付加 | `apply_to_result()` | 統計結果にノイズを適用 |
| ノイズ推定 | `estimate_noise_magnitude()` | 事前にノイズ量を確認 |

### 使用例1: 平均年齢にノイズを付加

```python
from security_checks import DifferentialPrivacy, NoiseType

# 差分プライバシーインスタンス
dp = DifferentialPrivacy(epsilon=1.0, delta=1e-5)

# 元の統計結果
true_average = 55.2

# ノイズを付加
dp_result = dp.apply_to_result(
    result=true_average,
    operation='mean',      # 操作種類（mean, sum, count等）
    field='age',           # フィールド名
    sample_size=100,       # データ数
    noise_type=NoiseType.LAPLACE
)

print(f"元の値: {true_average}")
print(f"ノイズ付き: {dp_result['noisy_result']}")
print(f"使用したε: {dp_result['epsilon_used']}")
print(f"感度: {dp_result['sensitivity']}")

# 出力例:
# 元の値: 55.2
# ノイズ付き: 55.87
# 使用したε: 1.0
# 感度: 1.2
```

### 使用例2: ノイズ量の事前推定

クエリ実行前にノイズの大きさを確認できます：

```python
estimate = dp.estimate_noise_magnitude(
    operation='mean',
    field='blood_sugar',
    sample_size=100,
    noise_type=NoiseType.LAPLACE
)

print(f"感度: {estimate['sensitivity']}")
print(f"予想ノイズ量: {estimate['expected_noise_magnitude']}")
print(f"推奨: {estimate['recommendation']}")

# 出力例:
# 感度: 2.5
# 予想ノイズ量: 2.5
# 推奨: 良好: ノイズは許容範囲内で、実用的な統計が得られます
```

### 使用例3: Gaussian機構（より強い保証）

```python
noisy_result = dp.add_gaussian_noise(
    value=55.2,
    sensitivity=1.2,
    epsilon=1.0,
    delta=1e-5  # δパラメータ
)

# (ε, δ)-差分プライバシーを保証
# δ = 失敗確率（非常に小さい値）
```

### API経由での使用

本システムでは、復号API `/api/decrypt` で自動的に差分プライバシーが適用されます：

```bash
# 復号リクエスト
curl -X POST http://localhost:5000/api/decrypt \
  -H "Content-Type: application/json" \
  -d '{
    "provider_id": "provider_0",
    "purchaser_id": "pharma_company",
    "encrypted_result": "...",
    "metadata": {
      "operation": "mean",
      "field": "age",
      "sample_size": 100,
      "noise_type": "laplace"
    }
  }'
```

レスポンス例：
```json
{
  "result": 55.87,
  "original_result_hidden": true,
  "differential_privacy": {
    "epsilon_used": 1.0,
    "delta_used": null,
    "noise_type": "laplace",
    "sensitivity": 1.2
  },
  "remaining_budget": 9.0,
  "status": "success"
}
```

### ノイズ推定API

事前にノイズ量を確認するAPI：

```bash
curl -X POST http://localhost:5000/api/estimate-noise \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "mean",
    "field": "age",
    "sample_size": 100,
    "epsilon": 1.0,
    "noise_type": "laplace"
  }'
```

### フィールド別の感度設定

本システムでは、医療データのフィールドごとに範囲が設定されています：

| フィールド | 範囲 | mean感度 (n=100) |
|------------|------|------------------|
| age | 0-120 | 1.2 |
| blood_pressure_systolic | 80-200 | 1.2 |
| blood_pressure_diastolic | 50-130 | 0.8 |
| blood_sugar | 50-300 | 2.5 |
| cholesterol | 100-400 | 3.0 |
| bmi | 10-50 | 0.4 |

### プライバシーバジェット管理

累積的なプライバシー損失を管理：

```python
from security_checks import PrivacyBudgetManager

budget = PrivacyBudgetManager(total_budget=10.0)

# クエリ1
budget.consume_budget("pharma_co", epsilon=1.0)
print(budget.get_remaining_budget("pharma_co"))  # 9.0

# クエリ2-10...
# ...

# バジェット超過時はエラー
budget.check_budget("pharma_co", required_epsilon=1.0)
# → ValueError: Privacy budget exceeded
```
