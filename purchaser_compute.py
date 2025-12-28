#!/usr/bin/env python3
"""
データ購入者用の準同型演算スクリプト

このスクリプトは、暗号化パッケージを読み込んで独自の統計計算を実行し、
暗号化された結果を出力します。結果はAPIで復号してもらいます。

使い方:
    python purchaser_compute.py encrypted_package.zip

出力:
    - 暗号化された結果（16進数）
    - メタデータ（operation, field, sample_size）
"""

import sys
import pickle
import zipfile
import tempfile
import json
from pathlib import Path
import tenseal as ts
import numpy as np


def extract_package(zip_path):
    """
    暗号化パッケージを解凍して中身を読み込む

    Args:
        zip_path: ZIPファイルのパス

    Returns:
        dict: {
            'encrypted_data': 暗号化データ,
            'context': 公開コンテキスト,
            'metadata': メタデータ,
            'provider_id': Provider ID
        }
    """
    temp_dir = tempfile.mkdtemp()
    temp_path = Path(temp_dir)

    # ZIPを解凍
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(temp_path)

    # 暗号化データを読み込み
    with open(temp_path / 'encrypted_data.pkl', 'rb') as f:
        encrypted_data = pickle.load(f)

    # 公開コンテキストを読み込み
    with open(temp_path / 'public_context.pkl', 'rb') as f:
        context_bytes = f.read()
        context = ts.context_from(context_bytes)

    # メタデータを読み込み
    with open(temp_path / 'metadata.json', 'r') as f:
        metadata = json.load(f)

    return {
        'encrypted_data': encrypted_data,
        'context': context,
        'metadata': metadata,
        'provider_id': metadata.get('provider_id', 'unknown')
    }


def compute_mean(encrypted_vectors):
    """
    暗号化されたベクトルの平均を計算

    Args:
        encrypted_vectors: List[CKKSVector]

    Returns:
        CKKSVector: 暗号化された平均値
    """
    total = encrypted_vectors[0]
    for vec in encrypted_vectors[1:]:
        total = total + vec

    mean = total * (1.0 / len(encrypted_vectors))
    return mean


def compute_sum(encrypted_vectors):
    """
    暗号化されたベクトルの合計を計算

    Args:
        encrypted_vectors: List[CKKSVector]

    Returns:
        CKKSVector: 暗号化された合計値
    """
    total = encrypted_vectors[0]
    for vec in encrypted_vectors[1:]:
        total = total + vec

    return total


def compute_variance(encrypted_vectors):
    """
    暗号化されたベクトルの分散を計算（近似）

    注意: 準同型暗号では正確な分散計算は困難なため、
    この実装は平方和の平均から平均の平方を引く方法を使用します。

    Args:
        encrypted_vectors: List[CKKSVector]

    Returns:
        CKKSVector: 暗号化された分散値（近似）
    """
    n = len(encrypted_vectors)

    # 平均を計算
    mean = compute_mean(encrypted_vectors)

    # 各要素を二乗
    squared_vectors = [vec * vec for vec in encrypted_vectors]

    # 二乗の平均を計算
    mean_of_squares = compute_mean(squared_vectors)

    # 分散 = E[X^2] - E[X]^2
    variance = mean_of_squares - (mean * mean)

    return variance


def compute_weighted_sum(encrypted_vectors, weights):
    """
    重み付き合計を計算

    Args:
        encrypted_vectors: List[CKKSVector]
        weights: List[float] - 各ベクトルの重み

    Returns:
        CKKSVector: 暗号化された重み付き合計
    """
    if len(encrypted_vectors) != len(weights):
        raise ValueError("Number of vectors must match number of weights")

    # 最初のベクトルに重みを掛ける
    result = encrypted_vectors[0] * weights[0]

    # 残りのベクトルを重み付きで加算
    for vec, weight in zip(encrypted_vectors[1:], weights[1:]):
        result = result + (vec * weight)

    return result


def compute_correlation(encrypted_vectors_x, encrypted_vectors_y):
    """
    2つのフィールド間の相関を計算（近似）

    注意: 準同型暗号での相関計算は非常に複雑です。
    この実装は簡略化された近似を使用します。

    Args:
        encrypted_vectors_x: List[CKKSVector] - フィールドX
        encrypted_vectors_y: List[CKKSVector] - フィールドY

    Returns:
        CKKSVector: 暗号化された相関係数（近似）
    """
    if len(encrypted_vectors_x) != len(encrypted_vectors_y):
        raise ValueError("Both fields must have the same number of samples")

    n = len(encrypted_vectors_x)

    # E[XY]を計算
    xy_products = [x * y for x, y in zip(encrypted_vectors_x, encrypted_vectors_y)]
    mean_xy = compute_mean(xy_products)

    # E[X]とE[Y]を計算
    mean_x = compute_mean(encrypted_vectors_x)
    mean_y = compute_mean(encrypted_vectors_y)

    # 共分散の近似: Cov(X,Y) ≈ E[XY] - E[X]E[Y]
    covariance = mean_xy - (mean_x * mean_y)

    return covariance


def main():
    """メイン処理"""
    if len(sys.argv) < 2:
        print("使い方: python purchaser_compute.py <encrypted_package.zip>")
        print("\n例:")
        print("  python purchaser_compute.py encrypted_package.zip")
        sys.exit(1)

    zip_path = sys.argv[1]

    if not Path(zip_path).exists():
        print(f"エラー: ファイルが見つかりません: {zip_path}")
        sys.exit(1)

    print("=" * 60)
    print("ZKP-DB 購入者用準同型演算スクリプト")
    print("=" * 60)
    print()

    # パッケージを読み込み
    print(f"[1/4] 暗号化パッケージを読み込んでいます: {zip_path}")
    package = extract_package(zip_path)

    print(f"✓ Provider ID: {package['provider_id']}")
    print(f"✓ 利用可能なフィールド: {list(package['encrypted_data'].keys())}")
    print(f"✓ サンプル数: {package['metadata']['total_records']}")
    print()

    # 利用可能な計算を表示
    print("[2/4] 実行する計算を選択してください:")
    print("  1. 平均 (mean)")
    print("  2. 合計 (sum)")
    print("  3. 分散 (variance) - 近似")
    print("  4. 重み付き合計 (weighted_sum)")
    print("  5. 相関 (correlation) - 2つのフィールド間")
    print()

    choice = input("選択 (1-5): ").strip()

    # フィールドを選択
    print()
    print("[3/4] 対象フィールドを選択してください:")
    fields = list(package['encrypted_data'].keys())
    for i, field in enumerate(fields, 1):
        print(f"  {i}. {field}")
    print()

    field_choice = input(f"選択 (1-{len(fields)}): ").strip()
    field_idx = int(field_choice) - 1
    field = fields[field_idx]

    # 暗号化ベクトルを復元
    field_data_bytes = package['encrypted_data'][field]
    encrypted_vectors = [
        ts.ckks_vector_from(package['context'], vec_bytes)
        for vec_bytes in field_data_bytes
    ]

    sample_size = len(encrypted_vectors)

    print()
    print(f"[4/4] 計算を実行しています...")

    # 計算を実行
    if choice == '1':
        # 平均
        result = compute_mean(encrypted_vectors)
        operation = 'mean'
        print(f"✓ 暗号化されたまま平均を計算しました")

    elif choice == '2':
        # 合計
        result = compute_sum(encrypted_vectors)
        operation = 'sum'
        print(f"✓ 暗号化されたまま合計を計算しました")

    elif choice == '3':
        # 分散
        result = compute_variance(encrypted_vectors)
        operation = 'variance'
        print(f"✓ 暗号化されたまま分散を計算しました（近似）")

    elif choice == '4':
        # 重み付き合計
        print("\n重みを入力してください（カンマ区切り）:")
        print(f"例: {','.join(['1.0'] * min(3, sample_size))}")
        weights_str = input(f"重み ({sample_size}個必要): ").strip()
        weights = [float(w.strip()) for w in weights_str.split(',')]

        if len(weights) != sample_size:
            print(f"エラー: 重みの数が一致しません（{len(weights)} vs {sample_size}）")
            sys.exit(1)

        result = compute_weighted_sum(encrypted_vectors, weights)
        operation = 'weighted_sum'
        print(f"✓ 暗号化されたまま重み付き合計を計算しました")

    elif choice == '5':
        # 相関
        print("\n2つ目のフィールドを選択してください:")
        for i, f in enumerate(fields, 1):
            if f != field:
                print(f"  {i}. {f}")

        field2_choice = input(f"選択 (1-{len(fields)}): ").strip()
        field2_idx = int(field2_choice) - 1
        field2 = fields[field2_idx]

        field2_data_bytes = package['encrypted_data'][field2]
        encrypted_vectors_y = [
            ts.ckks_vector_from(package['context'], vec_bytes)
            for vec_bytes in field2_data_bytes
        ]

        result = compute_correlation(encrypted_vectors, encrypted_vectors_y)
        operation = 'correlation'
        field = f"{field}_{field2}_correlation"
        print(f"✓ 暗号化されたまま相関を計算しました（近似）")

    else:
        print("無効な選択です")
        sys.exit(1)

    # 結果を16進数でシリアライズ
    encrypted_result_hex = result.serialize().hex()

    print()
    print("=" * 60)
    print("計算完了！")
    print("=" * 60)
    print()
    print("暗号化された結果（16進数）:")
    print("-" * 60)
    print(encrypted_result_hex)
    print("-" * 60)
    print()
    print("次の手順で復号してください:")
    print("  1. http://localhost:3001 の「計算結果の復号（手動）」を開く")
    print("  2. 暗号化パッケージ (encrypted_package.zip) をアップロード")
    print("  3. 上記の16進数を貼り付けるかファイルでアップロード")
    print("  4. Purchaser ID を入力して送信 -> API経由で復号")
    print()
    print("CLIで直接復号する場合のcurl例:")
    print(f"""curl -X POST http://localhost:5000/api/decrypt \\
  -F "purchaser_id=<your_purchaser_id>" \\
  -F "encrypted_package=@{zip_path}" \\
  -F "encrypted_result={encrypted_result_hex[:32]}..." """)


if __name__ == '__main__':
    main()
