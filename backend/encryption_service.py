"""
暗号化・ZKP処理サービス
患者データの暗号化とゼロ知識証明の生成
"""
import json
import pickle
import subprocess
import tempfile
import os
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import tenseal as ts
import pandas as pd
import numpy as np


class MerkleTree:
    """
    Merkle Tree実装
    全患者データのハッシュを効率的に集約・検証
    """

    def __init__(self, hash_func=None):
        """
        Args:
            hash_func: ハッシュ関数（デフォルト: SHA256）
        """
        self.hash_func = hash_func or self._sha256_hash
        self.leaves: List[str] = []
        self.tree: List[List[str]] = []
        self.root: Optional[str] = None

    def _sha256_hash(self, data: str) -> str:
        """SHA256ハッシュを計算"""
        return hashlib.sha256(data.encode()).hexdigest()

    def _combine_hash(self, left: str, right: str) -> str:
        """2つのハッシュを結合してハッシュ化"""
        return self.hash_func(left + right)

    def add_leaf(self, data: str) -> str:
        """
        葉ノードを追加

        Args:
            data: ハッシュ化するデータ

        Returns:
            str: 葉ノードのハッシュ
        """
        leaf_hash = self.hash_func(data)
        self.leaves.append(leaf_hash)
        return leaf_hash

    def add_leaf_hash(self, leaf_hash: str):
        """既にハッシュ化されたデータを追加"""
        self.leaves.append(leaf_hash)

    def build(self) -> str:
        """
        Merkle Treeを構築

        Returns:
            str: Merkle Root
        """
        if not self.leaves:
            raise ValueError("No leaves to build tree")

        # 葉が奇数の場合、最後の葉を複製
        leaves = self.leaves.copy()
        if len(leaves) % 2 == 1:
            leaves.append(leaves[-1])

        self.tree = [leaves]

        # ボトムアップで木を構築
        current_level = leaves
        while len(current_level) > 1:
            next_level = []
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                right = current_level[i + 1] if i + 1 < len(current_level) else left
                parent = self._combine_hash(left, right)
                next_level.append(parent)

            self.tree.append(next_level)
            current_level = next_level

        self.root = current_level[0]
        return self.root

    def get_proof(self, index: int) -> List[Dict]:
        """
        特定の葉ノードのMerkle Proofを取得

        Args:
            index: 葉ノードのインデックス

        Returns:
            List[Dict]: 証明パス（各ステップで兄弟ノードと位置を含む）
        """
        if not self.tree:
            raise ValueError("Tree not built yet")

        if index < 0 or index >= len(self.leaves):
            raise ValueError(f"Invalid index: {index}")

        proof = []
        current_index = index

        for level in self.tree[:-1]:  # ルートを除く各レベル
            # 兄弟ノードを取得
            if current_index % 2 == 0:
                sibling_index = current_index + 1
                position = 'right'
            else:
                sibling_index = current_index - 1
                position = 'left'

            if sibling_index < len(level):
                proof.append({
                    'hash': level[sibling_index],
                    'position': position
                })

            current_index = current_index // 2

        return proof

    def verify_proof(self, leaf_hash: str, proof: List[Dict], root: str) -> bool:
        """
        Merkle Proofを検証

        Args:
            leaf_hash: 検証する葉ノードのハッシュ
            proof: 証明パス
            root: 期待されるMerkle Root

        Returns:
            bool: 検証成功時True
        """
        current_hash = leaf_hash

        for step in proof:
            sibling_hash = step['hash']
            position = step['position']

            if position == 'left':
                current_hash = self._combine_hash(sibling_hash, current_hash)
            else:
                current_hash = self._combine_hash(current_hash, sibling_hash)

        return current_hash == root

    def to_dict(self) -> Dict:
        """木の情報を辞書形式で出力"""
        return {
            'root': self.root,
            'leaf_count': len(self.leaves),
            'tree_height': len(self.tree),
            'leaves': self.leaves
        }


class BatchZKPService:
    """
    バッチZKP証明サービス
    全患者データの正当性を効率的に証明
    """

    def __init__(self):
        self.zkp_service = ZKPService()
        self.merkle_tree = MerkleTree()

    def hash_patient_data(self, patient_data: Dict) -> str:
        """
        患者データをハッシュ化

        Args:
            patient_data: 患者データ辞書

        Returns:
            str: ハッシュ値
        """
        # 数値フィールドのみを使用
        numeric_fields = ['age', 'blood_pressure_systolic', 'blood_pressure_diastolic',
                         'blood_sugar', 'cholesterol', 'bmi', 'hospitalization_count']

        # 一貫性のためにフィールドをソートして結合
        data_str = '|'.join(
            f"{field}:{patient_data.get(field, 0)}"
            for field in sorted(numeric_fields)
            if field in patient_data
        )

        return hashlib.sha256(data_str.encode()).hexdigest()

    def generate_batch_proof(
        self,
        patients_df: pd.DataFrame,
        sample_size: int = 10
    ) -> Dict:
        """
        全患者データのバッチZKP証明を生成

        方式:
        1. 全患者データのハッシュをMerkle Treeに追加
        2. サンプル患者（等間隔で選択）のZKP証明を生成
        3. Merkle RootとサンプルZKP証明を返却

        Args:
            patients_df: 患者データのDataFrame
            sample_size: ZKP証明を生成するサンプル数

        Returns:
            Dict: {
                'merkle_root': Merkle Root,
                'merkle_tree_info': 木の情報,
                'sample_proofs': サンプルZKP証明,
                'coverage': カバレッジ情報
            }
        """
        total_patients = len(patients_df)

        # Merkle Treeを構築
        self.merkle_tree = MerkleTree()
        patient_hashes = []

        for idx, row in patients_df.iterrows():
            patient_data = row.to_dict()
            patient_hash = self.hash_patient_data(patient_data)
            self.merkle_tree.add_leaf_hash(patient_hash)
            patient_hashes.append({
                'index': idx,
                'hash': patient_hash
            })

        merkle_root = self.merkle_tree.build()

        # サンプルインデックスを計算（等間隔）
        sample_indices = self._select_sample_indices(total_patients, sample_size)

        # サンプル患者のZKP証明を生成
        sample_proofs = []
        for idx in sample_indices:
            patient_data = patients_df.iloc[idx].to_dict()

            try:
                # ZKP証明を生成
                zkp_proof = self.zkp_service.generate_proof(patient_data)

                # Merkle Proofを取得
                merkle_proof = self.merkle_tree.get_proof(idx)

                sample_proofs.append({
                    'patient_index': idx,
                    'patient_hash': patient_hashes[idx]['hash'],
                    'zkp_proof': zkp_proof['proof'],
                    'public_signals': zkp_proof['public_signals'],
                    'data_hash': zkp_proof['data_hash'],
                    'merkle_proof': merkle_proof,
                    'is_valid': zkp_proof.get('is_valid', '1')
                })
            except (ValueError, subprocess.CalledProcessError) as e:
                # データが範囲外の場合はスキップしてログ
                sample_proofs.append({
                    'patient_index': idx,
                    'patient_hash': patient_hashes[idx]['hash'],
                    'error': str(e),
                    'zkp_proof': None
                })

        # 統計情報を計算
        successful_proofs = len([p for p in sample_proofs if p.get('zkp_proof')])

        return {
            'merkle_root': merkle_root,
            'merkle_tree_info': {
                'leaf_count': total_patients,
                'tree_height': len(self.merkle_tree.tree)
            },
            'sample_proofs': sample_proofs,
            'coverage': {
                'total_patients': total_patients,
                'sampled_patients': len(sample_indices),
                'successful_proofs': successful_proofs,
                'coverage_percentage': (successful_proofs / total_patients) * 100,
                'sample_indices': sample_indices
            },
            'verification_key': self.zkp_service.get_verification_key()
        }

    def _select_sample_indices(self, total: int, sample_size: int) -> List[int]:
        """
        等間隔でサンプルインデックスを選択

        Args:
            total: 総数
            sample_size: サンプルサイズ

        Returns:
            List[int]: サンプルインデックスのリスト
        """
        if sample_size >= total:
            return list(range(total))

        # 等間隔でサンプリング
        step = total / sample_size
        return [int(i * step) for i in range(sample_size)]

    def verify_batch_proof(
        self,
        merkle_root: str,
        sample_proofs: List[Dict],
        verification_key: Dict
    ) -> Dict:
        """
        バッチZKP証明を検証

        Args:
            merkle_root: Merkle Root
            sample_proofs: サンプルZKP証明
            verification_key: 検証鍵

        Returns:
            Dict: 検証結果
        """
        results = []

        for proof_data in sample_proofs:
            if proof_data.get('error'):
                results.append({
                    'patient_index': proof_data['patient_index'],
                    'zkp_valid': False,
                    'merkle_valid': False,
                    'error': proof_data['error']
                })
                continue

            # ZKP証明を検証
            zkp_valid = self.zkp_service.verify_proof(
                proof_data['zkp_proof'],
                proof_data['public_signals']
            )

            # Merkle Proofを検証
            merkle_valid = self.merkle_tree.verify_proof(
                proof_data['patient_hash'],
                proof_data['merkle_proof'],
                merkle_root
            )

            results.append({
                'patient_index': proof_data['patient_index'],
                'zkp_valid': zkp_valid,
                'merkle_valid': merkle_valid
            })

        # 全体の検証結果
        all_zkp_valid = all(r.get('zkp_valid', False) for r in results)
        all_merkle_valid = all(r.get('merkle_valid', False) for r in results)

        return {
            'overall_valid': all_zkp_valid and all_merkle_valid,
            'zkp_verification': {
                'all_valid': all_zkp_valid,
                'passed': sum(1 for r in results if r.get('zkp_valid')),
                'total': len(results)
            },
            'merkle_verification': {
                'all_valid': all_merkle_valid,
                'passed': sum(1 for r in results if r.get('merkle_valid')),
                'total': len(results)
            },
            'individual_results': results
        }


_GLOBAL_CONTEXT = None


def _get_shared_context():
    """
    標準的なCKKSコンテキストを使い回す。
    ローカル環境用の十分なパラメータ設定。
    """
    global _GLOBAL_CONTEXT
    if _GLOBAL_CONTEXT is None:
        ctx = ts.context(
            ts.SCHEME_TYPE.CKKS,
            poly_modulus_degree=8192,  # 標準的なセキュリティレベル
            coeff_mod_bit_sizes=[60, 40, 40, 60]  # 複数の乗算レベルをサポート
        )
        # 加算とスカラー倍のみなのでGalois/Relinキーは生成しない
        ctx.global_scale = 2**40
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
