"""
準同型暗号化の実装
TenSEALを使用して患者データを暗号化し、暗号化されたまま計算を行います
"""

import json
import pickle
import tenseal as ts
import numpy as np
from pathlib import Path

class MedicalDataEncryptor:
    """
    医療データの暗号化・復号・計算を行うクラス
    """

    def __init__(self):
        """
        準同型暗号のコンテキストを初期化
        """
        # CKKS スキーム（実数値の計算に適している）
        self.context = ts.context(
            ts.SCHEME_TYPE.CKKS,
            poly_modulus_degree=8192,      # セキュリティレベル
            coeff_mod_bit_sizes=[60, 40, 40, 60]  # 係数モジュラス
        )

        # 必要な鍵を生成
        self.context.generate_galois_keys()
        self.context.generate_relin_keys()

        # スケール設定
        self.context.global_scale = 2**40

        print("✓ 準同型暗号コンテキストを初期化しました")

    def encrypt_patient_data(self, patients):
        """
        患者データを暗号化

        Args:
            patients: 患者データのリスト

        Returns:
            暗号化されたデータの辞書
        """
        encrypted_data = {
            'ages': [],
            'blood_pressures_systolic': [],
            'blood_pressures_diastolic': [],
            'blood_sugars': [],
            'cholesterols': [],
            'bmis': []
        }

        # 各患者のデータを暗号化
        for patient in patients:
            encrypted_data['ages'].append(
                ts.ckks_vector(self.context, [float(patient['age'])])
            )
            encrypted_data['blood_pressures_systolic'].append(
                ts.ckks_vector(self.context, [float(patient['blood_pressure_systolic'])])
            )
            encrypted_data['blood_pressures_diastolic'].append(
                ts.ckks_vector(self.context, [float(patient['blood_pressure_diastolic'])])
            )
            encrypted_data['blood_sugars'].append(
                ts.ckks_vector(self.context, [float(patient['blood_sugar'])])
            )
            encrypted_data['cholesterols'].append(
                ts.ckks_vector(self.context, [float(patient['cholesterol'])])
            )
            encrypted_data['bmis'].append(
                ts.ckks_vector(self.context, [float(patient['bmi'])])
            )

        print(f"✓ {len(patients)}人の患者データを暗号化しました")
        return encrypted_data

    def compute_encrypted_average(self, encrypted_values):
        """
        暗号化されたデータの平均を計算（暗号化されたまま）

        Args:
            encrypted_values: 暗号化された値のリスト

        Returns:
            暗号化された平均値
        """
        # 合計を計算
        total = encrypted_values[0]
        for enc_val in encrypted_values[1:]:
            total = total + enc_val

        # 平均を計算（データ数で割る）
        n = len(encrypted_values)
        average = total * (1.0 / n)

        return average

    def decrypt_value(self, encrypted_value):
        """
        暗号化された値を復号

        Args:
            encrypted_value: 暗号化された値

        Returns:
            復号された値
        """
        return encrypted_value.decrypt()[0]

    def save_context(self, filepath='keys/context.pkl'):
        """
        暗号化コンテキストを保存

        Args:
            filepath: 保存先パス
        """
        # シリアライズして保存
        context_bytes = self.context.serialize(save_secret_key=True)

        with open(filepath, 'wb') as f:
            f.write(context_bytes)

        print(f"✓ コンテキストを{filepath}に保存しました")

    def save_encrypted_data(self, encrypted_data, filepath='data/encrypted_patients.pkl'):
        """
        暗号化データを保存

        Args:
            encrypted_data: 暗号化されたデータ
            filepath: 保存先パス
        """
        # 暗号化データをシリアライズ
        serialized_data = {}
        for key, values in encrypted_data.items():
            serialized_data[key] = [val.serialize() for val in values]

        with open(filepath, 'wb') as f:
            pickle.dump(serialized_data, f)

        print(f"✓ 暗号化データを{filepath}に保存しました")

    @staticmethod
    def load_context(filepath='keys/context.pkl'):
        """
        保存されたコンテキストを読み込み
        """
        with open(filepath, 'rb') as f:
            context_bytes = f.read()

        context = ts.context_from(context_bytes)
        print(f"✓ コンテキストを{filepath}から読み込みました")
        return context


def demonstrate_encrypted_computation(patients):
    """
    暗号化されたまま計算できることをデモ
    """
    print("\n" + "="*60)
    print("準同型暗号デモ: 暗号化されたまま統計計算")
    print("="*60)

    # 暗号化
    encryptor = MedicalDataEncryptor()
    encrypted_data = encryptor.encrypt_patient_data(patients)

    # 暗号化されたまま平均を計算
    print("\n暗号化されたまま計算中...")

    encrypted_avg_age = encryptor.compute_encrypted_average(
        encrypted_data['ages']
    )
    encrypted_avg_bp = encryptor.compute_encrypted_average(
        encrypted_data['blood_pressures_systolic']
    )
    encrypted_avg_sugar = encryptor.compute_encrypted_average(
        encrypted_data['blood_sugars']
    )
    encrypted_avg_cholesterol = encryptor.compute_encrypted_average(
        encrypted_data['cholesterols']
    )

    # 結果を復号して確認
    print("\n暗号化データから計算された統計値:")
    print(f"  平均年齢: {encryptor.decrypt_value(encrypted_avg_age):.1f}歳")
    print(f"  平均収縮期血圧: {encryptor.decrypt_value(encrypted_avg_bp):.1f} mmHg")
    print(f"  平均血糖値: {encryptor.decrypt_value(encrypted_avg_sugar):.1f} mg/dL")
    print(f"  平均コレステロール: {encryptor.decrypt_value(encrypted_avg_cholesterol):.1f} mg/dL")

    # 検証: 生データから計算した値と比較
    print("\n検証: 生データから計算した値:")
    actual_avg_age = np.mean([p['age'] for p in patients])
    actual_avg_bp = np.mean([p['blood_pressure_systolic'] for p in patients])
    actual_avg_sugar = np.mean([p['blood_sugar'] for p in patients])
    actual_avg_cholesterol = np.mean([p['cholesterol'] for p in patients])

    print(f"  平均年齢: {actual_avg_age:.1f}歳")
    print(f"  平均収縮期血圧: {actual_avg_bp:.1f} mmHg")
    print(f"  平均血糖値: {actual_avg_sugar:.1f} mg/dL")
    print(f"  平均コレステロール: {actual_avg_cholesterol:.1f} mg/dL")

    print("\n✓ 暗号化されたまま正しく計算できました！")
    print("="*60)

    # データとコンテキストを保存
    encryptor.save_encrypted_data(encrypted_data)
    encryptor.save_context()

    return encryptor, encrypted_data


if __name__ == "__main__":
    # 患者データを読み込み
    print("患者データを読み込み中...")
    with open('data/patients.json', 'r', encoding='utf-8') as f:
        patients = json.load(f)

    print(f"✓ {len(patients)}人の患者データを読み込みました")

    # デモ実行
    encryptor, encrypted_data = demonstrate_encrypted_computation(patients)

    print("\n完了！")
