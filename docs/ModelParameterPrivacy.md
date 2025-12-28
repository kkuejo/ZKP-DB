# モデルパラメータの復号とプライバシーリスク

## 質問

**暗号化データを用いて、あるモデルのパラメータ推計をさせた場合、そのモデルパラメータの値を復号化できますか？**

## 技術的な回答

### ✅ YES、復号できます

準同型暗号で計算したモデルパラメータも暗号化されているため、秘密鍵で復号可能です。

```python
# 例: 線形回帰モデル

# 1. 暗号化データで学習
enc_X = [encrypt(patient['age']) for patient in patients]
enc_y = [encrypt(patient['blood_pressure']) for patient in patients]

# 2. 暗号化されたまま線形回帰
enc_beta0, enc_beta1 = encrypted_linear_regression(enc_X, enc_y)

# 3. パラメータを復号 ← 可能！
beta0 = enc_beta0.decrypt()[0]
beta1 = enc_beta1.decrypt()[0]

print(f"血圧 = {beta0:.2f} + {beta1:.2f} × 年齢")
# 出力例: "血圧 = 80.00 + 0.50 × 年齢"
```

---

## 🚨 重大な問題: モデルパラメータからのデータ漏洩

### 問題の所在

**モデルパラメータを復号すると、個別患者データが推測できてしまう可能性があります。**

これは先ほどの「個別データ復号攻撃」と同様、またはそれ以上に深刻な問題です。

---

### 攻撃例1: 少数データでのパラメータ推測

#### シナリオ

患者が**2人だけ**のデータでモデル学習した場合：

```python
# データ
患者1: 年齢=30歳, 血圧=110 mmHg
患者2: 年齢=60歳, 血圧=140 mmHg

# 線形回帰モデル: 血圧 = β0 + β1 × 年齢
```

#### 暗号化されたまま学習

```python
# 暗号化データで線形回帰
enc_ages = [encrypt([30]), encrypt([60])]
enc_bp = [encrypt([110]), encrypt([140])]

enc_beta0, enc_beta1 = encrypted_linear_regression(enc_ages, enc_bp)
```

#### 復号

```python
beta0 = enc_beta0.decrypt()[0]  # → 80.0
beta1 = enc_beta1.decrypt()[0]  # → 1.0

# モデル: 血圧 = 80.0 + 1.0 × 年齢
```

#### 攻撃: 元データの逆算

```python
# モデルパラメータから元データを逆算

# 線形回帰の公式:
# β1 = (y2 - y1) / (x2 - x1)
# β0 = y1 - β1 × x1

# 攻撃者が知っている情報:
# - β0 = 80.0
# - β1 = 1.0
# - データ数 = 2人
# - 年齢範囲は30-60歳（公開情報から推測）

# 逆算:
# もし x1=30 なら: y1 = β0 + β1×30 = 80 + 1.0×30 = 110
# もし x2=60 なら: y2 = β0 + β1×60 = 80 + 1.0×60 = 140

# 結果: 元の患者データを完全に復元！
```

**結論**: データ数が少ないと、モデルパラメータから個別データを逆算できてしまいます。

---

### 攻撃例2: 過学習モデルからのメンバーシップ推論

#### シナリオ

10人の患者データで複雑なモデル（例: ニューラルネットワーク）を学習した場合。

```python
# データ
患者1: 年齢=45, 血圧=130, 血糖=105, コレステロール=210
患者2: 年齢=52, 血圧=140, 血糖=120, コレステロール=230
...
患者10: 年齢=38, 血圧=115, 血糖=95, コレステロール=180

# ニューラルネットワーク: 糖尿病リスク予測
```

#### 過学習の問題

データ数（10）に対してパラメータ数が多すぎると、モデルが個別データを「記憶」してしまいます。

```python
# モデルパラメータ
layer1_weights = [
    [0.45, 0.23, -0.12, 0.89],  # 100個のパラメータ
    [0.67, -0.34, 0.56, -0.23],
    ...
]

# このパラメータから「患者1が訓練データに含まれていたか？」を推測可能
```

#### メンバーシップ推論攻撃

```python
def membership_inference_attack(model_params, candidate_data):
    """
    モデルパラメータから、特定の患者が訓練データに
    含まれていたかを推測する攻撃
    """
    # モデルの損失を計算
    loss = compute_loss(model_params, candidate_data)

    # 損失が異常に小さい → 訓練データに含まれていた可能性が高い
    if loss < threshold:
        return "訓練データに含まれていた"
    else:
        return "訓練データに含まれていない"

# 例
candidate = {'age': 45, 'bp': 130, 'bg': 105, 'chol': 210}
result = membership_inference_attack(model_params, candidate)
# → "訓練データに含まれていた"

# これにより、特定の患者が「糖尿病リスクのデータセット」に
# 含まれていたことが判明 → プライバシー侵害
```

---

### 攻撃例3: モデル反転攻撃（Model Inversion Attack）

#### シナリオ

モデルパラメータと少数の補助情報から、訓練データの特徴を再構成する攻撃。

```python
# 攻撃者が知っている情報:
# - モデルパラメータ (復号済み)
# - 患者IDの一部（例: P0042）
# - 大まかな年齢層（例: 40代）

def model_inversion_attack(model_params, patient_id, age_range):
    """
    モデルパラメータから訓練データの特徴を再構成
    """
    # 勾配降下法で元データを推定
    reconstructed_data = {}

    # 初期値
    age = random.choice(age_range)  # 40-49
    bp = 120  # 初期推定値

    # モデルの勾配を使って元データを推定
    for iteration in range(1000):
        # モデルの予測
        prediction = model(age, bp, model_params)

        # 勾配を計算
        grad_age, grad_bp = compute_gradient(model_params, age, bp)

        # 元データに近づくように更新
        age -= learning_rate * grad_age
        bp -= learning_rate * grad_bp

    return {'age': age, 'bp': bp}

# 結果
reconstructed = model_inversion_attack(model_params, 'P0042', range(40, 50))
# → {'age': 45.3, 'bp': 132.7}
# 実際の患者P0042: age=45, bp=133 ← ほぼ一致！
```

---

## ✅ 防御メカニズム

### 1. **k-匿名性の強制** ★最重要★

モデル学習には最低k人（例: k=100人以上）のデータを使用することを強制。

```python
def train_model_with_k_anonymity(encrypted_data, min_k=100):
    """
    k-匿名性を満たすデータでのみモデル学習を許可
    """
    sample_size = len(encrypted_data)

    if sample_size < min_k:
        raise ValueError(
            f"k-anonymity violation: Need at least {min_k} samples, "
            f"got {sample_size}"
        )

    # モデル学習
    model_params = train_encrypted_model(encrypted_data)

    return model_params

# 使用例
try:
    model = train_model_with_k_anonymity(encrypted_data, min_k=100)
except ValueError as e:
    print(f"エラー: {e}")
    # → "k-anonymity violation: Need at least 100 samples, got 10"
```

**推奨値**:
- 線形回帰: k ≥ 100
- ロジスティック回帰: k ≥ 200
- ニューラルネットワーク: k ≥ 1000

---

### 2. **差分プライバシーによるパラメータノイズ追加**

モデルパラメータに差分プライバシーのノイズを追加します。

#### 差分プライバシー勾配降下法（DP-SGD）

```python
import numpy as np

def dp_sgd_train(encrypted_data, epsilon=1.0, delta=1e-5):
    """
    差分プライバシーを満たす勾配降下法でモデル学習

    Args:
        encrypted_data: 暗号化されたデータ
        epsilon: プライバシーバジェット（小さいほど高いプライバシー）
        delta: 失敗確率

    Returns:
        ノイズ付きモデルパラメータ（暗号化）
    """
    # 通常の勾配降下法でパラメータ推定
    enc_params = encrypted_gradient_descent(encrypted_data)

    # 復号
    params = enc_params.decrypt()

    # 差分プライバシーノイズを追加
    # Gaussian mechanism
    sensitivity = calculate_sensitivity(encrypted_data)
    noise_scale = sensitivity * np.sqrt(2 * np.log(1.25/delta)) / epsilon

    noisy_params = params + np.random.normal(0, noise_scale, size=params.shape)

    return noisy_params

# 使用例
epsilon = 1.0  # プライバシーバジェット
noisy_model = dp_sgd_train(encrypted_data, epsilon=epsilon)

print(f"元のパラメータ: {true_params}")
print(f"ノイズ付き: {noisy_model}")
# 出力例:
# 元のパラメータ: [80.00, 1.00]
# ノイズ付き: [80.23, 0.97]  ← わずかにずれている
```

#### プライバシーバジェット管理

```python
class ModelPrivacyBudgetManager:
    """モデル学習のプライバシーバジェット管理"""

    def __init__(self, total_budget=10.0):
        self.total_budget = total_budget
        self.used_budget = 0.0
        self.trained_models = []

    def train_model(self, encrypted_data, epsilon, model_type='linear'):
        """
        差分プライバシーを満たすモデル学習

        Args:
            encrypted_data: 暗号化データ
            epsilon: このモデルに使用するプライバシーバジェット
            model_type: モデルタイプ

        Returns:
            ノイズ付きモデルパラメータ
        """
        # バジェットチェック
        remaining = self.total_budget - self.used_budget

        if epsilon > remaining:
            raise ValueError(
                f"Privacy budget exceeded. "
                f"Required: {epsilon}, Remaining: {remaining:.2f}"
            )

        # モデル学習（DP-SGD）
        noisy_params = dp_sgd_train(encrypted_data, epsilon=epsilon)

        # バジェット消費
        self.used_budget += epsilon

        # ログ記録
        self.trained_models.append({
            'model_type': model_type,
            'epsilon': epsilon,
            'params': noisy_params,
            'timestamp': datetime.now()
        })

        print(f"✓ モデル学習完了")
        print(f"  使用バジェット: {epsilon}")
        print(f"  残りバジェット: {self.total_budget - self.used_budget:.2f}")

        return noisy_params

    def get_remaining_budget(self):
        """残りプライバシーバジェットを取得"""
        return self.total_budget - self.used_budget

# 使用例
budget_manager = ModelPrivacyBudgetManager(total_budget=10.0)

# モデル1: 線形回帰（epsilon=2.0）
model1 = budget_manager.train_model(encrypted_data, epsilon=2.0, model_type='linear')
# → 残りバジェット: 8.0

# モデル2: ロジスティック回帰（epsilon=3.0）
model2 = budget_manager.train_model(encrypted_data, epsilon=3.0, model_type='logistic')
# → 残りバジェット: 5.0

# モデル3: ニューラルネットワーク（epsilon=6.0）
try:
    model3 = budget_manager.train_model(encrypted_data, epsilon=6.0, model_type='nn')
except ValueError as e:
    print(f"エラー: {e}")
    # → "Privacy budget exceeded. Required: 6.0, Remaining: 5.00"
```

---

### 3. **正則化による過学習防止**

L1/L2正則化を使用して、モデルが個別データを「記憶」することを防ぎます。

```python
def encrypted_ridge_regression(enc_X, enc_y, lambda_reg=1.0):
    """
    L2正則化付き線形回帰（Ridge回帰）

    Args:
        enc_X: 暗号化された説明変数
        enc_y: 暗号化された目的変数
        lambda_reg: 正則化パラメータ（大きいほど強い正則化）

    Returns:
        暗号化されたモデルパラメータ（正則化済み）
    """
    # 正規方程式: β = (X^T X + λI)^{-1} X^T y
    # 暗号化されたまま計算

    n_features = len(enc_X[0])

    # X^T X を計算（暗号化されたまま）
    enc_XtX = encrypted_matrix_multiply(enc_X.T, enc_X)

    # λI を追加（正則化項）
    enc_lambda_I = [
        [encrypt(lambda_reg if i == j else 0) for j in range(n_features)]
        for i in range(n_features)
    ]
    enc_XtX_reg = enc_XtX + enc_lambda_I

    # (X^T X + λI)^{-1} を計算
    enc_inv = encrypted_matrix_inverse(enc_XtX_reg)

    # X^T y を計算
    enc_Xty = encrypted_matrix_multiply(enc_X.T, enc_y)

    # β = (X^T X + λI)^{-1} X^T y
    enc_beta = encrypted_matrix_multiply(enc_inv, enc_Xty)

    return enc_beta

# 使用例
# 正則化なし（過学習リスク高）
enc_beta_no_reg = encrypted_linear_regression(enc_X, enc_y)
beta_no_reg = enc_beta_no_reg.decrypt()

# 正則化あり（過学習を防止）
enc_beta_reg = encrypted_ridge_regression(enc_X, enc_y, lambda_reg=10.0)
beta_reg = enc_beta_reg.decrypt()

print(f"正則化なし: {beta_no_reg}")  # [80.00, 1.00]
print(f"正則化あり: {beta_reg}")      # [79.50, 0.85] ← より汎化
```

---

### 4. **パラメータの選択的開示**

すべてのパラメータを開示するのではなく、必要な統計量のみを提供します。

```python
def selective_parameter_disclosure(encrypted_data, query_type):
    """
    パラメータの選択的開示

    Args:
        encrypted_data: 暗号化データ
        query_type: 'prediction' | 'feature_importance' | 'full_params'

    Returns:
        開示される情報
    """
    # モデル学習（暗号化されたまま）
    enc_model = train_encrypted_model(encrypted_data)

    if query_type == 'prediction':
        # 予測のみ提供（パラメータは非開示）
        return {
            'type': 'prediction_service',
            'endpoint': '/api/predict',
            'description': 'モデルパラメータは非開示。予測APIのみ提供'
        }

    elif query_type == 'feature_importance':
        # 特徴量の重要度のみ提供
        enc_params = enc_model.get_params()
        params = enc_params.decrypt()

        # 絶対値のランキングのみ（符号と大きさは非開示）
        importance_ranking = np.argsort(np.abs(params))[::-1]

        return {
            'type': 'feature_importance',
            'ranking': importance_ranking.tolist(),
            'description': '特徴量の重要度ランキング（パラメータ値は非開示）'
        }

    elif query_type == 'full_params':
        # 完全なパラメータ（要審査）
        # k-匿名性、差分プライバシーチェック後に提供
        if not check_privacy_requirements(encrypted_data):
            raise ValueError("Privacy requirements not met")

        enc_params = enc_model.get_params()
        params = enc_params.decrypt()

        # 差分プライバシーノイズ追加
        noisy_params = add_dp_noise(params, epsilon=1.0)

        return {
            'type': 'full_parameters',
            'params': noisy_params.tolist(),
            'privacy_guarantee': 'epsilon=1.0 differential privacy',
            'description': 'ノイズ付きパラメータ'
        }

    else:
        raise ValueError(f"Unknown query type: {query_type}")

# 使用例

# ケース1: 予測のみ
result1 = selective_parameter_disclosure(encrypted_data, 'prediction')
print(result1)
# → {'type': 'prediction_service', 'endpoint': '/api/predict', ...}

# ケース2: 特徴量重要度
result2 = selective_parameter_disclosure(encrypted_data, 'feature_importance')
print(result2)
# → {'type': 'feature_importance', 'ranking': [3, 1, 0, 2], ...}

# ケース3: 完全なパラメータ（ノイズ付き）
result3 = selective_parameter_disclosure(encrypted_data, 'full_params')
print(result3)
# → {'type': 'full_parameters', 'params': [80.23, 0.97], ...}
```

---

### 5. **復号サービスでのモデルパラメータ審査**

モデルパラメータの復号リクエストに対しても、統計値と同様の審査を実施します。

```python
@app.route('/decrypt_model', methods=['POST'])
def decrypt_model_parameters():
    """モデルパラメータの復号API（厳格な審査付き）"""

    # === 1. 認証 ===
    purchaser_id = request.headers.get('X-Purchaser-ID')
    api_key = request.headers.get('X-API-Key')

    if not verify_purchaser(purchaser_id, api_key):
        return jsonify({'error': 'Unauthorized'}), 401

    # === 2. リクエストデータ取得 ===
    request_data = request.get_json()
    encrypted_model = pickle.loads(bytes.fromhex(request_data['encrypted_model']))
    metadata = request_data['metadata']

    # === 3. k-匿名性チェック ===
    training_sample_size = metadata.get('training_sample_size', 0)
    MIN_K = 100  # モデル学習には最低100人必要

    if training_sample_size < MIN_K:
        return jsonify({
            'error': 'k-anonymity violation',
            'message': f'Model training requires at least {MIN_K} samples',
            'provided': training_sample_size
        }), 403

    # === 4. モデル複雑度チェック ===
    model_type = metadata.get('model_type')
    n_params = metadata.get('n_parameters')

    # パラメータ数 / データ数 の比率をチェック
    params_per_sample = n_params / training_sample_size

    if params_per_sample > 0.1:  # 10%以上は過学習リスク
        return jsonify({
            'error': 'Overfitting risk',
            'message': f'Too many parameters ({n_params}) for sample size ({training_sample_size})',
            'ratio': params_per_sample
        }), 403

    # === 5. プライバシーバジェットチェック ===
    epsilon = metadata.get('privacy_budget', 1.0)

    if epsilon < 0.1:  # epsilon が小さすぎるとノイズが大きすぎて無意味
        return jsonify({
            'error': 'Privacy budget too small',
            'message': 'epsilon must be at least 0.1'
        }), 400

    try:
        budget_manager.check_budget(purchaser_id, epsilon)
    except ValueError as e:
        return jsonify({
            'error': 'Privacy budget exceeded',
            'message': str(e)
        }), 403

    # === 6. モデルパラメータ復号 ===
    decrypted_params = encrypted_model.decrypt()

    # === 7. 差分プライバシーノイズ追加 ===
    sensitivity = calculate_model_sensitivity(metadata)
    noisy_params = add_laplace_noise(decrypted_params, sensitivity, epsilon)

    # === 8. バジェット消費 ===
    budget_manager.consume_budget(purchaser_id, epsilon)

    # === 9. ログ記録 ===
    log_model_decryption_request(
        purchaser_id=purchaser_id,
        model_type=model_type,
        training_sample_size=training_sample_size,
        n_parameters=n_params,
        epsilon=epsilon,
        timestamp=datetime.now()
    )

    # === 10. 結果返却 ===
    return jsonify({
        'model_type': model_type,
        'parameters': noisy_params.tolist(),
        'privacy_guarantee': f'epsilon={epsilon} differential privacy',
        'training_sample_size': training_sample_size,
        'n_parameters': n_params,
        'remaining_budget': budget_manager.get_remaining_budget(purchaser_id),
        'status': 'success'
    })
```

---

## 📋 セキュリティチェックリスト（モデルパラメータ用）

モデルパラメータの復号には、以下のすべてのチェックが必要です：

- [ ] **認証・認可**: API keyの検証
- [ ] **k-匿名性チェック**: 訓練データは最低k人（推奨: k≥100）
- [ ] **モデル複雑度チェック**: パラメータ数/データ数 ≤ 0.1
- [ ] **正則化の確認**: L1/L2正則化が適用されているか
- [ ] **差分プライバシー**: パラメータにノイズ追加
- [ ] **プライバシーバジェット管理**: 累積プライバシー損失を追跡
- [ ] **過学習チェック**: 検証データでの性能確認
- [ ] **レート制限**: 短時間の大量モデル学習を防止
- [ ] **ログ記録**: すべてのモデル学習・復号リクエストを記録
- [ ] **アラート**: 異常なパターンをセキュリティチームに通知

---

## 推奨パラメータ

### データサイズとモデル複雑度

| モデルタイプ | 最小データ数（k） | 最大パラメータ数 | 推奨epsilon |
|------------|-----------------|----------------|------------|
| 線形回帰 | 100 | 10 | 1.0 |
| Ridge回帰 | 100 | 20 | 1.0 |
| ロジスティック回帰 | 200 | 10 | 0.5 |
| ニューラルネットワーク（小） | 1,000 | 100 | 0.5 |
| ニューラルネットワーク（中） | 10,000 | 1,000 | 0.1 |
| ニューラルネットワーク（大） | 100,000 | 10,000 | 0.1 |

### 差分プライバシーパラメータ

- **epsilon（ε）**: プライバシーバジェット
  - ε = 0.1: 非常に強いプライバシー（ノイズ大）
  - ε = 1.0: 強いプライバシー（推奨）
  - ε = 10.0: 弱いプライバシー（ノイズ小）

- **delta（δ）**: 失敗確率
  - 推奨値: δ = 1/n^2（nはデータ数）
  - 例: n=1000なら δ = 10^-6

---

## まとめ

### 質問への回答

**Q: 暗号化データを用いて、あるモデルのパラメータ推計をさせた場合、そのモデルパラメータの値を復号化できますか？**

**A: YES、技術的には復号可能です。しかし、重大なプライバシーリスクがあります。**

### プライバシーリスク

1. **少数データからの逆算**: データが少ないと、パラメータから元データを復元可能
2. **メンバーシップ推論**: 特定の患者が訓練データに含まれていたかを推測可能
3. **モデル反転攻撃**: パラメータから訓練データの特徴を再構成可能

### 必須の防御メカニズム

1. ✅ **k-匿名性の強制**: 最低k人（推奨: k≥100）のデータで学習
2. ✅ **差分プライバシー**: パラメータにノイズ追加（DP-SGD）
3. ✅ **正則化**: L1/L2正則化で過学習を防止
4. ✅ **選択的開示**: 必要な統計量のみ提供
5. ✅ **厳格な審査**: 復号サービスで多層チェック

### 最終推奨

**モデルパラメータの完全開示は避け、以下のいずれかを採用:**

1. **予測サービスのみ提供**: パラメータは非開示、予測APIのみ
2. **特徴量重要度のみ提供**: パラメータ値ではなくランキング
3. **ノイズ付きパラメータ提供**: 差分プライバシー（ε≤1.0）を満たす

これにより、**プライバシー保護と機械学習モデルの実用性を両立**できます。
