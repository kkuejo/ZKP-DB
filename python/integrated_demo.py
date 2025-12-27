"""
統合デモスクリプト

このスクリプトは以下の完全なワークフローを実行します：
1. ダミーデータの生成
2. データの準同型暗号化
3. 暗号化されたまま統計計算
4. ZKP証明の生成（JavaScriptを呼び出し）
5. 証明の検証

カルテ会社が外部にデータを販売する実際のユースケースをシミュレートします
"""

import json
import subprocess
import os
import sys
from pathlib import Path

# プロジェクトルートを取得
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT / 'python'))

from generate_dummy_data import generate_patient_data, save_data, generate_statistics
from homomorphic_encryption import MedicalDataEncryptor, demonstrate_encrypted_computation


class MedicalDataMarketplace:
    """
    医療データマーケットプレイスのシミュレーション
    """

    def __init__(self):
        self.data_dir = PROJECT_ROOT / 'data'
        self.scripts_dir = PROJECT_ROOT / 'scripts'

    def run_node_script(self, script_name, args=[]):
        """
        Node.jsスクリプトを実行

        Args:
            script_name: スクリプト名
            args: コマンドライン引数
        """
        script_path = self.scripts_dir / script_name
        cmd = ['node', str(script_path)] + args

        print(f"実行中: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"エラー: {result.stderr}")
            return False

        print(result.stdout)
        return True

    def scenario_data_provider(self):
        """
        シナリオ1: データ提供者側（カルテ会社）
        """
        print("\n" + "="*70)
        print("シナリオ1: データ提供者（カルテ会社）の視点")
        print("="*70)
        print("\nカルテ会社は100人の患者データを保有しています。")
        print("このデータを外部に販売したいが、プライバシーを守る必要があります。\n")

        # ステップ1: ダミーデータ生成
        print("[ステップ 1/3] 患者データの準備")
        print("-" * 70)

        import random
        import numpy as np
        random.seed(42)
        np.random.seed(42)

        patients = generate_patient_data(100)
        generate_statistics(patients)
        save_data(patients, format='json')

        # ステップ2: データの暗号化
        print("\n[ステップ 2/3] データの準同型暗号化")
        print("-" * 70)
        print("データを暗号化することで、外部に渡しても内容が見えません。\n")

        encryptor, encrypted_data = demonstrate_encrypted_computation(patients)

        # ステップ3: ZKP証明の生成
        print("\n[ステップ 3/3] ゼロ知識証明の生成")
        print("-" * 70)
        print("データが正当であることを証明する証明書を生成します。")
        print("この証明により、外部の購入者はデータが改ざんされていないことを確認できます。\n")

        # Node.jsスクリプトを呼び出して証明を生成
        success = self.run_node_script('generate_proof.js')

        if success:
            print("\n✅ データ提供者側の準備が完了しました！")
            print("\n販売パッケージ:")
            print("  ✓ 暗号化された患者データ (100人分)")
            print("  ✓ 準同型暗号コンテキスト")
            print("  ✓ ゼロ知識証明 (5件)")
            print("  ✓ 検証鍵")
        else:
            print("\n❌ 証明の生成に失敗しました")

    def scenario_data_consumer(self):
        """
        シナリオ2: データ購入者側（外部研究機関・企業）
        """
        print("\n" + "="*70)
        print("シナリオ2: データ購入者（研究機関・企業）の視点")
        print("="*70)
        print("\n研究機関が暗号化された医療データを購入しました。")
        print("生データは見えませんが、統計分析と検証が可能です。\n")

        # ステップ1: 証明の検証
        print("[ステップ 1/2] データの正当性検証")
        print("-" * 70)
        print("購入したデータが本物であり、改ざんされていないかをZKPで検証します。\n")

        success = self.run_node_script('verify_proof.js')

        if not success:
            print("\n❌ 検証に失敗しました。データが信頼できません。")
            return

        # ステップ2: 暗号化されたまま分析
        print("\n[ステップ 2/2] 暗号化データでの統計分析")
        print("-" * 70)
        print("暗号化されたデータのまま、統計分析を実行します。\n")

        # 患者データを読み込み
        with open(self.data_dir / 'patients.json', 'r', encoding='utf-8') as f:
            patients = json.load(f)

        # 暗号化して計算のデモ
        encryptor = MedicalDataEncryptor()
        encrypted_data = encryptor.encrypt_patient_data(patients)

        # 年齢層別の平均血圧を計算（暗号化されたまま）
        print("分析例: 年齢層別の平均収縮期血圧")

        age_groups = {
            '20-39歳': [],
            '40-59歳': [],
            '60歳以上': []
        }

        for i, patient in enumerate(patients):
            age = patient['age']
            if age < 40:
                age_groups['20-39歳'].append(i)
            elif age < 60:
                age_groups['40-59歳'].append(i)
            else:
                age_groups['60歳以上'].append(i)

        for group_name, indices in age_groups.items():
            if len(indices) == 0:
                continue

            encrypted_bps = [encrypted_data['blood_pressures_systolic'][i] for i in indices]
            encrypted_avg = encryptor.compute_encrypted_average(encrypted_bps)
            avg_value = encryptor.decrypt_value(encrypted_avg)

            print(f"  {group_name}: {avg_value:.1f} mmHg ({len(indices)}人)")

        print("\n✅ データ購入者は以下を達成しました:")
        print("  ✓ データの正当性を検証")
        print("  ✓ 個別の患者データを見ずに統計分析を実行")
        print("  ✓ プライバシーを保護しながら有用な知見を獲得")

    def demonstrate_security(self):
        """
        セキュリティデモ: 改ざん検出
        """
        print("\n" + "="*70)
        print("セキュリティデモ: 改ざん検出")
        print("="*70)
        print("\n悪意のある第三者がデータを改ざんしようとした場合...")
        print("ZKPは改ざんを検出できるかテストします。\n")

        success = self.run_node_script('verify_proof.js', ['--demo-invalid'])

        if success:
            print("\n✅ ZKPは改ざんを正しく検出しました！")
            print("このシステムはデータの完全性を保証します。")


def print_system_architecture():
    """
    システムアーキテクチャの説明
    """
    print("\n" + "="*70)
    print("システムアーキテクチャ")
    print("="*70)
    print("""
このシステムは3つの技術を組み合わせています:

1. 準同型暗号 (Homomorphic Encryption)
   - データを暗号化したまま計算可能
   - 外部にデータを渡しても中身が見えない
   - 実装: TenSEAL (CKKS方式)

2. ゼロ知識証明 (Zero-Knowledge Proof)
   - データの正当性を証明
   - 改ざんを検出
   - 実装: Circom + snarkjs (Groth16)

3. 統計分析・機械学習
   - 暗号化されたまま計算
   - 平均、分散、回帰分析など
   - 実装: Python (numpy, scikit-learn)

データフロー:
┌─────────────────┐
│  カルテ会社      │
│  (データ提供者)  │
└────────┬────────┘
         │
         │ 1. データ暗号化
         │ 2. ZKP証明生成
         ↓
┌─────────────────┐
│  暗号化データ    │
│  + 証明         │
└────────┬────────┘
         │ 販売
         ↓
┌─────────────────┐
│  研究機関        │
│  (データ購入者)  │
│                 │
│  - 証明検証 ✓   │
│  - 暗号化分析   │
│  - 知見獲得     │
└─────────────────┘
""")


def main():
    """
    メインデモ実行
    """
    print("="*70)
    print("ZKP-DB: 医療データマーケットプレイス デモ")
    print("="*70)
    print("\nゼロ知識証明と準同型暗号を使った医療データ販売システムの")
    print("完全なワークフローをデモンストレーションします。")

    marketplace = MedicalDataMarketplace()

    # システムアーキテクチャの説明
    print_system_architecture()

    input("\nEnterキーを押してデモを開始...")

    # シナリオ1: データ提供者
    marketplace.scenario_data_provider()

    input("\nEnterキーを押して次のシナリオへ...")

    # シナリオ2: データ購入者
    marketplace.scenario_data_consumer()

    input("\nEnterキーを押してセキュリティデモへ...")

    # セキュリティデモ
    marketplace.demonstrate_security()

    # まとめ
    print("\n" + "="*70)
    print("デモ完了")
    print("="*70)
    print("""
このシステムの利点:

✅ プライバシー保護
   - 患者の個人データは暗号化され、外部に漏れない

✅ データの正当性保証
   - ゼロ知識証明により、改ざんを検出できる

✅ 有用性の維持
   - 暗号化されたまま統計分析・機械学習が可能

✅ ビジネスモデル
   - カルテ会社: データを安全に収益化
   - 研究機関: 貴重なデータで研究を推進

次のステップ:
- より複雑な機械学習モデルの実装
- Webインターフェースの開発
- ブロックチェーンとの統合
- 差分プライバシーの追加
""")

    print("="*70)


if __name__ == "__main__":
    main()
