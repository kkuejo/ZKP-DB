"""
準同型暗号を使った機械学習の実装

このモジュールでは、暗号化されたデータで以下のMLタスクを実行します：
1. 線形回帰
2. ロジスティック回帰（多項式近似）
3. 浅いニューラルネットワーク
"""

import json
import numpy as np
import tenseal as ts
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, accuracy_score, r2_score
import pickle


class EncryptedLinearRegression:
    """
    準同型暗号化された線形回帰

    暗号化されたデータで予測を実行できます
    """

    def __init__(self, context):
        """
        Args:
            context: TenSEALの暗号化コンテキスト
        """
        self.context = context
        self.weights = None
        self.bias = None
        self.scaler = StandardScaler()

    def train(self, X, y):
        """
        平文データで訓練（通常の機械学習）

        Args:
            X: 特徴量 (n_samples, n_features)
            y: ターゲット (n_samples,)
        """
        print("線形回帰モデルを訓練中...")

        # データを正規化
        X_scaled = self.scaler.fit_transform(X)

        # 線形回帰モデルを訓練
        model = LinearRegression()
        model.fit(X_scaled, y)

        self.weights = model.coef_
        self.bias = model.intercept_

        # 訓練データでの性能評価
        y_pred = model.predict(X_scaled)
        mse = mean_squared_error(y, y_pred)
        r2 = r2_score(y, y_pred)

        print(f"  訓練完了")
        print(f"  MSE: {mse:.2f}")
        print(f"  R²: {r2:.3f}")
        print(f"  重み: {self.weights}")
        print(f"  バイアス: {self.bias:.2f}")

        return self

    def predict_encrypted(self, X_encrypted):
        """
        暗号化されたデータで予測

        Args:
            X_encrypted: 暗号化された特徴量のリスト

        Returns:
            暗号化された予測値
        """
        if self.weights is None:
            raise ValueError("モデルが訓練されていません")

        # 暗号化されたまま線形演算: y = w1*x1 + w2*x2 + ... + b
        prediction = X_encrypted[0] * float(self.weights[0])

        for i in range(1, len(self.weights)):
            prediction = prediction + (X_encrypted[i] * float(self.weights[i]))

        # バイアス項を加算
        prediction = prediction + float(self.bias)

        return prediction

    def decrypt_prediction(self, encrypted_pred):
        """
        予測値を復号
        """
        return encrypted_pred.decrypt()[0]


class EncryptedLogisticRegression:
    """
    準同型暗号化されたロジスティック回帰

    Sigmoid関数を多項式で近似して実装
    """

    def __init__(self, context):
        self.context = context
        self.weights = None
        self.bias = None
        self.scaler = StandardScaler()

    def sigmoid_poly_approx(self, x):
        """
        Sigmoid関数の多項式近似

        σ(x) ≈ 0.5 + 0.197x - 0.004x³
        (範囲: -5 <= x <= 5 で精度が高い)

        Args:
            x: 暗号化された値

        Returns:
            暗号化されたSigmoid近似値
        """
        # 0.5 + 0.197x - 0.004x³
        x_cubed = x * x * x
        result = x * 0.197 + x_cubed * (-0.004) + 0.5
        return result

    def train(self, X, y):
        """
        ロジスティック回帰を訓練

        Args:
            X: 特徴量
            y: ターゲット（0 or 1）
        """
        print("ロジスティック回帰モデルを訓練中...")

        # データを正規化
        X_scaled = self.scaler.fit_transform(X)

        # ロジスティック回帰を訓練
        model = LogisticRegression(max_iter=1000)
        model.fit(X_scaled, y)

        self.weights = model.coef_[0]
        self.bias = model.intercept_[0]

        # 性能評価
        y_pred = model.predict(X_scaled)
        accuracy = accuracy_score(y, y_pred)

        print(f"  訓練完了")
        print(f"  精度: {accuracy:.3f}")
        print(f"  重み: {self.weights}")
        print(f"  バイアス: {self.bias:.2f}")

        return self

    def predict_encrypted(self, X_encrypted):
        """
        暗号化データで予測（確率）

        Args:
            X_encrypted: 暗号化された特徴量のリスト

        Returns:
            暗号化された予測確率
        """
        if self.weights is None:
            raise ValueError("モデルが訓練されていません")

        # 線形部分: z = w·x + b
        z = X_encrypted[0] * float(self.weights[0])
        for i in range(1, len(self.weights)):
            z = z + (X_encrypted[i] * float(self.weights[i]))
        z = z + float(self.bias)

        # Sigmoid近似
        prob = self.sigmoid_poly_approx(z)

        return prob


class EncryptedNeuralNetwork:
    """
    暗号化された浅いニューラルネットワーク

    構造: 入力層 → 隠れ層(4ノード) → 出力層
    活性化関数: 多項式近似
    """

    def __init__(self, context, input_dim=4, hidden_dim=4):
        self.context = context
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim

        # 重み（訓練後に設定）
        self.W1 = None  # (input_dim, hidden_dim)
        self.b1 = None  # (hidden_dim,)
        self.W2 = None  # (hidden_dim, 1)
        self.b2 = None  # (1,)

        self.scaler = StandardScaler()

    def activation_poly(self, x):
        """
        ReLU風の多項式近似活性化関数

        f(x) ≈ x + 0.5x² - 0.05x³
        """
        x_squared = x * x
        x_cubed = x_squared * x
        result = x + x_squared * 0.5 + x_cubed * (-0.05)
        return result

    def train_simple(self, X, y):
        """
        簡単なニューラルネットワークを訓練

        実際には、事前に訓練された重みを使用します。
        完全な準同型暗号化での訓練は非常に複雑です。
        """
        print("ニューラルネットワークを訓練中...")

        X_scaled = self.scaler.fit_transform(X)

        # ランダムな重みで初期化（実際にはより良い訓練方法を使用）
        np.random.seed(42)
        self.W1 = np.random.randn(self.input_dim, self.hidden_dim) * 0.1
        self.b1 = np.zeros(self.hidden_dim)
        self.W2 = np.random.randn(self.hidden_dim, 1) * 0.1
        self.b2 = np.zeros(1)

        print(f"  ネットワーク構造: {self.input_dim} → {self.hidden_dim} → 1")
        print(f"  パラメータ数: {self.W1.size + self.b1.size + self.W2.size + self.b2.size}")

        return self

    def forward_encrypted(self, X_encrypted):
        """
        暗号化データで順伝播

        Args:
            X_encrypted: 暗号化された入力のリスト [enc(x1), enc(x2), ...]

        Returns:
            暗号化された出力
        """
        if self.W1 is None:
            raise ValueError("モデルが訓練されていません")

        # 隠れ層の計算
        hidden = []
        for j in range(self.hidden_dim):
            # h_j = activation(sum(W1[i,j] * x[i]) + b1[j])
            h = X_encrypted[0] * float(self.W1[0, j])
            for i in range(1, self.input_dim):
                h = h + (X_encrypted[i] * float(self.W1[i, j]))
            h = h + float(self.b1[j])

            # 活性化関数
            h = self.activation_poly(h)
            hidden.append(h)

        # 出力層の計算
        output = hidden[0] * float(self.W2[0, 0])
        for j in range(1, self.hidden_dim):
            output = output + (hidden[j] * float(self.W2[j, 0]))
        output = output + float(self.b2[0])

        return output


def demonstrate_ml_tasks():
    """
    様々な機械学習タスクのデモ
    """
    print("="*70)
    print("準同型暗号を使った機械学習デモ")
    print("="*70)

    # データの読み込み
    print("\n患者データを読み込み中...")
    with open('data/patients.json', 'r', encoding='utf-8') as f:
        patients = json.load(f)

    # 特徴量とターゲットの準備
    X = np.array([
        [p['age'], p['blood_pressure_systolic'],
         p['blood_sugar'], p['cholesterol']]
        for p in patients
    ])

    # ターゲット1: BMI（回帰タスク）
    y_regression = np.array([p['bmi'] for p in patients])

    # ターゲット2: 高血圧の有無（分類タスク）
    y_classification = np.array([
        1 if p['blood_pressure_systolic'] >= 140 else 0
        for p in patients
    ])

    print(f"✓ {len(patients)}人のデータを読み込みました")
    print(f"  特徴量: 年齢、収縮期血圧、血糖値、コレステロール")

    # 暗号化コンテキストの作成
    context = ts.context(
        ts.SCHEME_TYPE.CKKS,
        poly_modulus_degree=8192,
        coeff_mod_bit_sizes=[60, 40, 40, 60]
    )
    context.generate_galois_keys()
    context.generate_relin_keys()
    context.global_scale = 2**40

    # ========================================
    # タスク1: 線形回帰
    # ========================================
    print("\n" + "="*70)
    print("タスク1: 線形回帰でBMIを予測")
    print("="*70)

    lr_model = EncryptedLinearRegression(context)
    lr_model.train(X, y_regression)

    # テストデータで予測（暗号化）
    print("\n暗号化データでの予測を実行中...")
    test_idx = 0
    test_patient = patients[test_idx]

    # テストデータを暗号化
    X_test_encrypted = [
        ts.ckks_vector(context, [float(test_patient['age'])]),
        ts.ckks_vector(context, [float(test_patient['blood_pressure_systolic'])]),
        ts.ckks_vector(context, [float(test_patient['blood_sugar'])]),
        ts.ckks_vector(context, [float(test_patient['cholesterol'])])
    ]

    # 暗号化されたまま予測
    encrypted_pred = lr_model.predict_encrypted(X_test_encrypted)
    predicted_bmi = lr_model.decrypt_prediction(encrypted_pred)
    actual_bmi = test_patient['bmi']

    print(f"\n患者 {test_patient['patient_id']} の予測結果:")
    print(f"  実際のBMI: {actual_bmi:.1f}")
    print(f"  予測BMI: {predicted_bmi:.1f}")
    print(f"  誤差: {abs(predicted_bmi - actual_bmi):.2f}")
    print("\n✅ データは暗号化されたまま予測が実行されました！")

    # ========================================
    # タスク2: ロジスティック回帰
    # ========================================
    print("\n" + "="*70)
    print("タスク2: ロジスティック回帰で高血圧を予測")
    print("="*70)

    logistic_model = EncryptedLogisticRegression(context)
    logistic_model.train(X, y_classification)

    print("\n暗号化データでの予測を実行中...")

    # 暗号化されたまま予測（確率）
    encrypted_prob = logistic_model.predict_encrypted(X_test_encrypted)
    predicted_prob = encrypted_prob.decrypt()[0]
    actual_label = y_classification[test_idx]

    print(f"\n患者 {test_patient['patient_id']} の予測結果:")
    print(f"  実際の血圧: {test_patient['blood_pressure_systolic']} mmHg")
    print(f"  高血圧ラベル: {'高血圧' if actual_label == 1 else '正常'}")
    print(f"  予測確率: {predicted_prob:.3f}")
    print(f"  予測ラベル: {'高血圧' if predicted_prob > 0.5 else '正常'}")
    print("\n✅ Sigmoid関数を多項式近似して暗号化のまま計算しました！")

    # ========================================
    # タスク3: ニューラルネットワーク
    # ========================================
    print("\n" + "="*70)
    print("タスク3: 浅いニューラルネットワーク")
    print("="*70)

    nn_model = EncryptedNeuralNetwork(context, input_dim=4, hidden_dim=4)
    nn_model.train_simple(X, y_regression)

    print("\n暗号化データでの予測を実行中...")

    # 暗号化されたまま順伝播
    encrypted_output = nn_model.forward_encrypted(X_test_encrypted)
    nn_prediction = encrypted_output.decrypt()[0]

    print(f"\n患者 {test_patient['patient_id']} の予測結果:")
    print(f"  ニューラルネットワークの出力: {nn_prediction:.2f}")
    print("\n✅ 多層ニューラルネットワークを暗号化のまま実行しました！")

    # ========================================
    # まとめ
    # ========================================
    print("\n" + "="*70)
    print("準同型暗号でのML: 何ができるか")
    print("="*70)
    print("""
✅ 実装可能なモデル:
  1. 線形回帰 - 完全に可能
  2. ロジスティック回帰 - 多項式近似で可能
  3. 浅いニューラルネットワーク - 2-3層なら可能
  4. 決定木 - 一部の操作は可能
  5. k-means - ユークリッド距離計算が可能

⚠️  制限事項:
  1. 深いニューラルネットワーク - 乗算の深さ制限
  2. ReLU, Sigmoid - 多項式近似が必要（精度低下）
  3. 比較演算 - if文、max/minが困難
  4. 大規模モデル - 計算時間が長い

💡 実用的な解決策:
  1. ハイブリッド方式: 一部を暗号化、一部を平文
  2. 転移学習: 暗号化データでファインチューニング
  3. 知識蒸留: 大きなモデルから小さなモデルへ
  4. Federated Learning: データは各所に残したまま学習
    """)

    print("="*70)


def save_models():
    """
    訓練済みモデルを保存
    """
    print("\n訓練済みモデルを保存中...")

    # データ読み込み
    with open('data/patients.json', 'r', encoding='utf-8') as f:
        patients = json.load(f)

    X = np.array([
        [p['age'], p['blood_pressure_systolic'],
         p['blood_sugar'], p['cholesterol']]
        for p in patients
    ])
    y_regression = np.array([p['bmi'] for p in patients])

    # コンテキスト作成
    context = ts.context(
        ts.SCHEME_TYPE.CKKS,
        poly_modulus_degree=8192,
        coeff_mod_bit_sizes=[60, 40, 40, 60]
    )
    context.generate_galois_keys()
    context.generate_relin_keys()
    context.global_scale = 2**40

    # モデル訓練
    lr_model = EncryptedLinearRegression(context)
    lr_model.train(X, y_regression)

    # 保存
    with open('data/lr_model.pkl', 'wb') as f:
        pickle.dump({
            'weights': lr_model.weights,
            'bias': lr_model.bias,
            'scaler': lr_model.scaler
        }, f)

    print("✓ モデルを data/lr_model.pkl に保存しました")


if __name__ == "__main__":
    demonstrate_ml_tasks()
    save_models()
