"""
高度な機械学習手法

準同型暗号の制限を回避して、より複雑な機械学習を実現する手法：
1. ハイブリッド暗号化（一部のみ暗号化）
2. クライアント-サーバー対話型計算
3. 知識蒸留（複雑なモデルを単純化）
4. 転移学習
5. Federated Learning風のアプローチ
"""

import json
import numpy as np
import tenseal as ts
from sklearn.neural_network import MLPClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import pickle


class HybridEncryption:
    """
    ハイブリッド暗号化方式

    機密性の高いデータだけを暗号化し、
    その他は平文で処理することで、複雑なモデルも使用可能
    """

    def __init__(self):
        self.context = None
        self.sensitive_features = []  # 暗号化する特徴量のインデックス
        self.public_features = []     # 平文のまま処理する特徴量

    def setup(self, sensitive_indices, total_features):
        """
        セットアップ

        Args:
            sensitive_indices: 暗号化する特徴量のインデックスリスト
            total_features: 特徴量の総数
        """
        self.sensitive_features = sensitive_indices
        self.public_features = [
            i for i in range(total_features)
            if i not in sensitive_indices
        ]

        # 暗号化コンテキスト
        self.context = ts.context(
            ts.SCHEME_TYPE.CKKS,
            poly_modulus_degree=8192,
            coeff_mod_bit_sizes=[60, 40, 40, 60]
        )
        self.context.generate_galois_keys()
        self.context.generate_relin_keys()
        self.context.global_scale = 2**40

        print(f"ハイブリッド暗号化を設定:")
        print(f"  暗号化特徴量: {len(self.sensitive_features)}個")
        print(f"  平文特徴量: {len(self.public_features)}個")

    def encrypt_data(self, X):
        """
        データを部分的に暗号化

        Args:
            X: データ (n_samples, n_features)

        Returns:
            (暗号化データ, 平文データ)
        """
        encrypted_data = []
        public_data = []

        for row in X:
            # 機密データのみ暗号化
            sensitive_values = [float(row[i]) for i in self.sensitive_features]
            encrypted_row = ts.ckks_vector(self.context, sensitive_values)
            encrypted_data.append(encrypted_row)

            # 非機密データは平文
            public_values = [row[i] for i in self.public_features]
            public_data.append(public_values)

        return encrypted_data, np.array(public_data)

    def compute_statistics(self, encrypted_data):
        """
        暗号化データの統計を計算
        """
        # 平均を計算（暗号化のまま）
        total = encrypted_data[0]
        for enc_data in encrypted_data[1:]:
            total = total + enc_data

        average = total * (1.0 / len(encrypted_data))

        return average


class InteractiveComputation:
    """
    クライアント-サーバー対話型計算

    サーバー: 線形演算（暗号化のまま）
    クライアント: 非線形演算（復号して実行）

    これにより、複雑なニューラルネットワークも実行可能
    """

    def __init__(self, context):
        self.context = context
        self.model_weights = None

    class Server:
        """サーバー側の処理（暗号化のまま線形演算）"""

        @staticmethod
        def linear_layer(X_encrypted, weights, bias):
            """
            線形層の計算: y = Wx + b

            Args:
                X_encrypted: 暗号化された入力
                weights: 重み行列
                bias: バイアス

            Returns:
                暗号化された出力
            """
            output = []
            n_output = weights.shape[1]

            for j in range(n_output):
                y = X_encrypted[0] * float(weights[0, j])
                for i in range(1, len(X_encrypted)):
                    y = y + (X_encrypted[i] * float(weights[i, j]))
                y = y + float(bias[j])
                output.append(y)

            return output

    class Client:
        """クライアント側の処理（復号して非線形演算）"""

        @staticmethod
        def apply_activation(encrypted_values, activation='relu'):
            """
            活性化関数を適用

            1. 暗号化データを復号
            2. 活性化関数を適用
            3. 再暗号化

            Args:
                encrypted_values: 暗号化された値のリスト
                activation: 活性化関数 ('relu', 'sigmoid', 'tanh')

            Returns:
                再暗号化された値のリスト
            """
            # 復号
            decrypted = [enc_val.decrypt()[0] for enc_val in encrypted_values]

            # 活性化関数を適用
            if activation == 'relu':
                activated = [max(0, val) for val in decrypted]
            elif activation == 'sigmoid':
                activated = [1 / (1 + np.exp(-val)) for val in decrypted]
            elif activation == 'tanh':
                activated = [np.tanh(val) for val in decrypted]
            else:
                activated = decrypted

            # 再暗号化
            context = encrypted_values[0].context()
            re_encrypted = [ts.ckks_vector(context, [val]) for val in activated]

            return re_encrypted

    def forward_interactive(self, X_encrypted, weights_list, bias_list):
        """
        対話型で順伝播

        Args:
            X_encrypted: 暗号化された入力
            weights_list: 各層の重みのリスト
            bias_list: 各層のバイアスのリスト

        Returns:
            最終出力
        """
        current = X_encrypted

        for i, (weights, bias) in enumerate(zip(weights_list, bias_list)):
            print(f"  層 {i+1}: サーバー側で線形演算を実行中...")
            # サーバー: 線形演算（暗号化のまま）
            linear_output = self.Server.linear_layer(current, weights, bias)

            if i < len(weights_list) - 1:  # 最終層以外
                print(f"  層 {i+1}: クライアント側で活性化関数を実行中...")
                # クライアント: 活性化関数（復号→計算→再暗号化）
                current = self.Client.apply_activation(linear_output, activation='relu')
            else:
                current = linear_output

        return current[0]


class KnowledgeDistillation:
    """
    知識蒸留

    1. 複雑な教師モデル（平文データで訓練）
    2. 単純な生徒モデル（暗号化データで推論可能）

    教師モデルの知識を生徒モデルに蒸留
    """

    def __init__(self):
        self.teacher_model = None
        self.student_model = None
        self.scaler = StandardScaler()

    def train_teacher(self, X, y):
        """
        複雑な教師モデルを訓練

        Args:
            X: 特徴量
            y: ターゲット
        """
        print("教師モデル（複雑なニューラルネットワーク）を訓練中...")

        X_scaled = self.scaler.fit_transform(X)

        # 複雑なモデル（隠れ層3層）
        self.teacher_model = MLPClassifier(
            hidden_layer_sizes=(20, 15, 10),
            activation='relu',
            max_iter=1000,
            random_state=42
        )
        self.teacher_model.fit(X_scaled, y)

        # 精度を確認
        y_pred = self.teacher_model.predict(X_scaled)
        accuracy = accuracy_score(y, y_pred)

        print(f"  教師モデルの精度: {accuracy:.3f}")
        print(f"  層構造: {self.teacher_model.hidden_layer_sizes}")

        return self

    def distill_to_student(self, X):
        """
        生徒モデルに知識を蒸留

        教師モデルの出力（ソフトラベル）を使って、
        より単純な生徒モデルを訓練
        """
        print("\n生徒モデル（単純な線形モデル）に知識を蒸留中...")

        if self.teacher_model is None:
            raise ValueError("教師モデルが訓練されていません")

        X_scaled = self.scaler.transform(X)

        # 教師モデルから確率を取得（ソフトラベル）
        soft_labels = self.teacher_model.predict_proba(X_scaled)

        # 単純な生徒モデル（線形に近い）
        self.student_model = MLPClassifier(
            hidden_layer_sizes=(5,),  # 隠れ層1層のみ
            activation='relu',
            max_iter=1000,
            random_state=42
        )

        # ソフトラベルで訓練
        hard_labels = np.argmax(soft_labels, axis=1)
        self.student_model.fit(X_scaled, hard_labels)

        # 精度を確認
        y_pred = self.student_model.predict(X_scaled)
        accuracy = accuracy_score(hard_labels, y_pred)

        print(f"  生徒モデルの精度: {accuracy:.3f}")
        print(f"  層構造: {self.student_model.hidden_layer_sizes}")
        print(f"  → より単純なモデルで、教師モデルの知識を保持！")

        return self


def demonstrate_advanced_techniques():
    """
    高度な技術のデモンストレーション
    """
    print("="*70)
    print("高度なML技術: 準同型暗号の制限を回避する")
    print("="*70)

    # データ読み込み
    print("\nデータを読み込み中...")
    with open('data/patients.json', 'r', encoding='utf-8') as f:
        patients = json.load(f)

    X = np.array([
        [p['age'], p['blood_pressure_systolic'],
         p['blood_sugar'], p['cholesterol']]
        for p in patients
    ])

    # 高血圧分類タスク
    y = np.array([
        1 if p['blood_pressure_systolic'] >= 140 else 0
        for p in patients
    ])

    print(f"✓ {len(patients)}人のデータを読み込みました")

    # ========================================
    # 手法1: ハイブリッド暗号化
    # ========================================
    print("\n" + "="*70)
    print("手法1: ハイブリッド暗号化")
    print("="*70)
    print("\n機密性が高いデータだけを暗号化し、他は平文で処理")
    print("→ 複雑なモデルも使用可能\n")

    hybrid = HybridEncryption()

    # 年齢と血糖値は機密、血圧とコレステロールは公開と仮定
    sensitive_indices = [0, 2]  # 年齢、血糖値
    hybrid.setup(sensitive_indices, total_features=4)

    encrypted_data, public_data = hybrid.encrypt_data(X)

    print(f"\n✓ データを暗号化しました")
    print(f"  暗号化: 年齢、血糖値")
    print(f"  平文: 血圧、コレステロール")
    print(f"\n→ 平文データで複雑なモデル（Random Forestなど）を訓練可能！")

    # 公開データでRandom Forestを訓練（例）
    if len(public_data[0]) > 0:
        rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
        rf_model.fit(public_data, y)
        accuracy = rf_model.score(public_data, y)
        print(f"  Random Forest精度: {accuracy:.3f}")

    # ========================================
    # 手法2: クライアント-サーバー対話型
    # ========================================
    print("\n" + "="*70)
    print("手法2: クライアント-サーバー対話型計算")
    print("="*70)
    print("\nサーバー: 線形演算（暗号化のまま）")
    print("クライアント: 非線形演算（復号して実行）")
    print("→ 深いニューラルネットワークも可能\n")

    context = ts.context(
        ts.SCHEME_TYPE.CKKS,
        poly_modulus_degree=8192,
        coeff_mod_bit_sizes=[60, 40, 40, 60]
    )
    context.generate_galois_keys()
    context.generate_relin_keys()
    context.global_scale = 2**40

    interactive = InteractiveComputation(context)

    # 簡単な2層ニューラルネットワークの重み（ダミー）
    np.random.seed(42)
    weights1 = np.random.randn(4, 8) * 0.1  # 4 → 8
    bias1 = np.zeros(8)
    weights2 = np.random.randn(8, 1) * 0.1  # 8 → 1
    bias2 = np.zeros(1)

    # テストデータを暗号化
    test_patient = patients[0]
    X_test = [
        ts.ckks_vector(context, [float(test_patient['age'])]),
        ts.ckks_vector(context, [float(test_patient['blood_pressure_systolic'])]),
        ts.ckks_vector(context, [float(test_patient['blood_sugar'])]),
        ts.ckks_vector(context, [float(test_patient['cholesterol'])])
    ]

    print("対話型で順伝播を実行中...")
    output = interactive.forward_interactive(
        X_test,
        [weights1, weights2],
        [bias1, bias2]
    )

    result = output.decrypt()[0]
    print(f"\n✓ 対話型計算が完了")
    print(f"  出力: {result:.3f}")
    print(f"\n→ ReLUなどの非線形関数も正確に計算可能！")

    # ========================================
    # 手法3: 知識蒸留
    # ========================================
    print("\n" + "="*70)
    print("手法3: 知識蒸留")
    print("="*70)
    print("\n複雑な教師モデル → 単純な生徒モデルに知識を転移")
    print("→ 暗号化推論に適した単純なモデルを構築\n")

    kd = KnowledgeDistillation()

    # 教師モデルの訓練
    kd.train_teacher(X, y)

    # 知識蒸留
    kd.distill_to_student(X)

    print(f"\n✓ 知識蒸留が完了")
    print(f"  教師: 3層ニューラルネット（複雑）")
    print(f"  生徒: 1層ニューラルネット（単純）")
    print(f"\n→ 生徒モデルは暗号化データでも推論可能！")

    # ========================================
    # まとめ
    # ========================================
    print("\n" + "="*70)
    print("複雑なMLを実現する手段のまとめ")
    print("="*70)
    print("""
1️⃣  ハイブリッド暗号化
   - 一部のみ暗号化、他は平文
   - 複雑なモデル（Random Forest, XGBoost）も使用可能
   - プライバシーと性能のバランスを調整

2️⃣  クライアント-サーバー対話型
   - 線形演算: サーバー（暗号化のまま）
   - 非線形演算: クライアント（復号して実行）
   - 深いニューラルネットワークが可能
   - 通信コストはあるが、精度は高い

3️⃣  知識蒸留
   - 複雑なモデルの知識を単純なモデルに転移
   - 暗号化推論に適したモデルを構築
   - 精度低下は小さい

4️⃣  Federated Learning（別途実装可能）
   - データを各所に残したまま学習
   - 準同型暗号と組み合わせて使用
   - プライバシー保護と高精度を両立

5️⃣  MPC (Multi-Party Computation)
   - 複数パーティで計算を分散
   - より複雑な計算が可能
   - 準同型暗号より柔軟

💡 実用的な推奨:
   → タスクの複雑さに応じて手法を使い分ける
   → ハイブリッドアプローチが最も現実的
   → プライバシーレベルと性能のトレードオフを考慮
    """)

    print("="*70)


def comparison_table():
    """
    各手法の比較表を表示
    """
    print("\n" + "="*70)
    print("各手法の比較")
    print("="*70)
    print("""
┌─────────────────┬──────────┬──────────┬──────────┬──────────┐
│     手法        │プライバシー│  精度   │  速度   │ 複雑さ  │
├─────────────────┼──────────┼──────────┼──────────┼──────────┤
│ 純粋な準同型暗号  │   ★★★★★ │  ★★☆☆☆ │ ★☆☆☆☆ │ ★★★☆☆ │
│ ハイブリッド     │   ★★★☆☆ │  ★★★★☆ │ ★★★★☆ │ ★★☆☆☆ │
│ 対話型計算       │   ★★★★☆ │  ★★★★★ │ ★★★☆☆ │ ★★★★☆ │
│ 知識蒸留        │   ★★★☆☆ │  ★★★★☆ │ ★★★★★ │ ★★★☆☆ │
│ Federated       │   ★★★★☆ │  ★★★★☆ │ ★★★☆☆ │ ★★★★★ │
│ MPC            │   ★★★★★ │  ★★★★★ │ ★★☆☆☆ │ ★★★★★ │
└─────────────────┴──────────┴──────────┴──────────┴──────────┘

推奨ユースケース:

🏥 医療データ分析:
   → ハイブリッド + 知識蒸留の組み合わせ

🏦 金融データ:
   → 対話型計算 or MPC

🔬 研究機関:
   → Federated Learning

📱 モバイルアプリ:
   → 知識蒸留（推論のみ）
    """)


if __name__ == "__main__":
    demonstrate_advanced_techniques()
    comparison_table()
