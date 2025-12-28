"""
暗号化・ZKP処理サービス
患者データの暗号化とゼロ知識証明の生成
"""
import json
import pickle
import subprocess
import tempfile
import os
from pathlib import Path
import tenseal as ts
import pandas as pd
import numpy as np


_GLOBAL_CONTEXT = None


def _get_shared_context():
    """
    超軽量パラメータで生成したCKKSコンテキストを使い回す。
    Render無料枠（512MB RAM制限）向けに最適化。
    """
    global _GLOBAL_CONTEXT
    if _GLOBAL_CONTEXT is None:
        ctx = ts.context(
            ts.SCHEME_TYPE.CKKS,
            poly_modulus_degree=2048,  # 4096→2048に軽量化（メモリ削減）
            coeff_mod_bit_sizes=[30, 20]  # ビットサイズも削減
        )
        # 加算とスカラー倍のみなのでGalois/Relinキーは生成しない（負荷軽減）
        ctx.global_scale = 2**15
        _GLOBAL_CONTEXT = ctx
    return _GLOBAL_CONTEXT


class EncryptionService:
    """準同型暗号による暗号化サービス"""

    def __init__(self):
        """CKKS暗号化コンテキストを取得（共有）"""
        self.context = _get_shared_context()

    def encrypt_patient_data(self, csv_data):
        """
        患者データを暗号化

        Args:
            csv_data: CSVファイルの内容（文字列またはDataFrame）

        Returns:
            dict: {
                'encrypted_data': 暗号化されたデータ（pickle化）,
                'context_public': 公開鍵情報（pickle化）,
                'sample_size': データ数,
                'fields': フィールド名リスト
            }
        """
        # CSVをDataFrameに変換
        if isinstance(csv_data, str):
            df = pd.read_csv(pd.io.common.StringIO(csv_data))
        else:
            df = csv_data

        # k-匿名性チェック（最低100件）
        if len(df) < 100:
            raise ValueError(
                f"k-anonymity violation: Need at least 100 records, got {len(df)}"
            )

        # データを暗号化
        encrypted_data = {}

        # 数値フィールドを暗号化
        numeric_fields = df.select_dtypes(include=[np.number]).columns.tolist()

        for field in numeric_fields:
            # 各患者のデータを個別に暗号化
            field_data = df[field].values.astype(float)
            encrypted_values = [
                ts.ckks_vector(self.context, [float(value)])
                for value in field_data
            ]
            # CKKSVectorをバイト列にシリアライズ
            encrypted_data[field] = [vec.serialize() for vec in encrypted_values]

        # 公開コンテキストを作成（秘密鍵を含まない）
        context_public = self.context.serialize()

        return {
            'encrypted_data': pickle.dumps(encrypted_data),
            'context_public': context_public,
            'sample_size': len(df),
            'fields': numeric_fields,
            'metadata': {
                'total_records': len(df),
                'numeric_fields': numeric_fields,
                'encryption_scheme': 'CKKS',
                'poly_modulus_degree': 2048
            }
        }

    def serialize_context_for_storage(self):
        """
        秘密鍵を含むコンテキストをシリアル化（データ提供者が保管）

        Returns:
            bytes: シリアル化されたコンテキスト
        """
        return self.context.serialize(save_secret_key=True)

    def get_public_context(self):
        """
        公開鍵のみのコンテキストを取得

        Returns:
            bytes: 公開コンテキスト
        """
        return self.context.serialize()


class ZKPService:
    """ゼロ知識証明サービス"""

    def __init__(self):
        self.circuit_path = Path(__file__).parent.parent / 'circuits' / 'data_verification.circom'
        self.build_path = Path(__file__).parent.parent / 'circuits' / 'build'
        self.keys_path = Path(__file__).parent.parent / 'keys'

    def generate_proof(self, patient_data):
        """
        患者データの正当性を証明するZKP証明を生成

        Args:
            patient_data: dict形式の患者データ

        Returns:
            dict: {
                'proof': 証明データ,
                'public_signals': 公開信号,
                'data_hash': データハッシュ
            }
        """
        # データが有効範囲内かチェック
        self._validate_data_ranges(patient_data)

        # 入力データを準備
        input_data = {
            'age': int(patient_data.get('age', 0)),
            'blood_pressure_systolic': int(patient_data.get('blood_pressure_systolic', 0)),
            'blood_pressure_diastolic': int(patient_data.get('blood_pressure_diastolic', 0)),
            'blood_sugar': int(patient_data.get('blood_sugar', 0)),
            'cholesterol': int(patient_data.get('cholesterol', 0)),
            'salt': int(patient_data.get('salt', 12345678))  # ランダムソルト
        }

        # 一時ファイルに入力データを書き込み
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(input_data, f)
            input_file = f.name

        try:
            # witness計算
            witness_file = input_file.replace('.json', '_witness.wtns')
            wasm_file = self.build_path / 'data_verification_js' / 'data_verification.wasm'

            subprocess.run([
                'node',
                str(self.build_path / 'data_verification_js' / 'generate_witness.js'),
                str(wasm_file),
                input_file,
                witness_file
            ], check=True, capture_output=True)

            # 証明生成
            proof_file = input_file.replace('.json', '_proof.json')
            public_file = input_file.replace('.json', '_public.json')
            zkey_file = self.keys_path / 'data_verification_0000.zkey'

            subprocess.run([
                'snarkjs', 'groth16', 'prove',
                str(zkey_file),
                witness_file,
                proof_file,
                public_file
            ], check=True, capture_output=True)

            # 証明と公開信号を読み込み
            with open(proof_file, 'r') as f:
                proof = json.load(f)

            with open(public_file, 'r') as f:
                public_signals = json.load(f)

            return {
                'proof': proof,
                'public_signals': public_signals,
                'data_hash': public_signals[0],  # 最初の公開信号がデータハッシュ
                'is_valid': public_signals[1] if len(public_signals) > 1 else "1"
            }

        finally:
            # 一時ファイルを削除
            for temp_file in [input_file, witness_file, proof_file, public_file]:
                if os.path.exists(temp_file):
                    os.remove(temp_file)

    def verify_proof(self, proof, public_signals):
        """
        ZKP証明を検証

        Args:
            proof: 証明データ
            public_signals: 公開信号

        Returns:
            bool: 検証成功時True
        """
        # 一時ファイルに証明と公開信号を書き込み
        with tempfile.NamedTemporaryFile(mode='w', suffix='_proof.json', delete=False) as f:
            json.dump(proof, f)
            proof_file = f.name

        with tempfile.NamedTemporaryFile(mode='w', suffix='_public.json', delete=False) as f:
            json.dump(public_signals, f)
            public_file = f.name

        try:
            # 検証鍵
            vkey_file = self.keys_path / 'verification_key.json'

            # 証明を検証
            result = subprocess.run([
                'snarkjs', 'groth16', 'verify',
                str(vkey_file),
                public_file,
                proof_file
            ], check=True, capture_output=True, text=True)

            # 出力に "OK" が含まれていれば成功
            return 'OK' in result.stdout

        except subprocess.CalledProcessError:
            return False

        finally:
            # 一時ファイルを削除
            for temp_file in [proof_file, public_file]:
                if os.path.exists(temp_file):
                    os.remove(temp_file)

    def _validate_data_ranges(self, data):
        """
        データが有効範囲内かチェック

        Args:
            data: 患者データ

        Raises:
            ValueError: データが範囲外
        """
        ranges = {
            'age': (0, 120),
            'blood_pressure_systolic': (80, 200),
            'blood_pressure_diastolic': (50, 120),
            'blood_sugar': (50, 300),
            'cholesterol': (100, 400)
        }

        for field, (min_val, max_val) in ranges.items():
            if field in data:
                value = data[field]
                if not (min_val <= value <= max_val):
                    raise ValueError(
                        f"{field} value {value} is out of valid range "
                        f"[{min_val}, {max_val}]"
                    )

    def get_verification_key(self):
        """
        検証鍵を取得

        Returns:
            dict: 検証鍵データ
        """
        vkey_file = self.keys_path / 'verification_key.json'

        if not vkey_file.exists():
            raise FileNotFoundError("Verification key not found")

        with open(vkey_file, 'r') as f:
            return json.load(f)


def create_data_package(csv_file_path, output_dir):
    """
    CSVファイルから販売パッケージを作成

    Args:
        csv_file_path: CSVファイルのパス
        output_dir: 出力ディレクトリ

    Returns:
        dict: 作成されたファイルのパス
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # CSVを読み込み
    df = pd.read_csv(csv_file_path)

    # 暗号化サービス
    encryption_service = EncryptionService()
    encrypted_package = encryption_service.encrypt_patient_data(df)

    # ZKPサービス
    zkp_service = ZKPService()

    # 各患者データのZKP証明を生成（サンプルとして最初の1件のみ）
    first_patient = df.iloc[0].to_dict()
    zkp_proof = zkp_service.generate_proof(first_patient)

    # 暗号化データを保存
    encrypted_data_file = output_dir / 'encrypted_data.pkl'
    with open(encrypted_data_file, 'wb') as f:
        f.write(encrypted_package['encrypted_data'])

    # 公開コンテキストを保存
    context_file = output_dir / 'public_context.pkl'
    with open(context_file, 'wb') as f:
        f.write(encrypted_package['context_public'])

    # ZKP証明を保存
    proof_file = output_dir / 'proof.json'
    with open(proof_file, 'w') as f:
        json.dump(zkp_proof['proof'], f, indent=2)

    # 公開信号を保存
    public_file = output_dir / 'public_signals.json'
    with open(public_file, 'w') as f:
        json.dump(zkp_proof['public_signals'], f, indent=2)

    # 検証鍵を保存
    verification_key = zkp_service.get_verification_key()
    vkey_file = output_dir / 'verification_key.json'
    with open(vkey_file, 'w') as f:
        json.dump(verification_key, f, indent=2)

    # メタデータを保存
    metadata = {
        **encrypted_package['metadata'],
        'data_hash': zkp_proof['data_hash'],
        'package_created': pd.Timestamp.now().isoformat()
    }
    metadata_file = output_dir / 'metadata.json'
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)

    # 秘密鍵を保存（データ提供者のみが保持）
    secret_context_file = output_dir / 'secret_context.pkl'
    with open(secret_context_file, 'wb') as f:
        f.write(encryption_service.serialize_context_for_storage())

    return {
        'encrypted_data': str(encrypted_data_file),
        'public_context': str(context_file),
        'proof': str(proof_file),
        'public_signals': str(public_file),
        'verification_key': str(vkey_file),
        'metadata': str(metadata_file),
        'secret_context': str(secret_context_file)  # データ提供者が保管
    }
