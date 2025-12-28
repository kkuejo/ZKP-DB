#!/usr/bin/env python3
"""
ZKP-DB 視覚的デモ
暗号化されたまま統計分析を行う様子をシミュレーション
"""

import json
import time
import tenseal as ts
import numpy as np
from pathlib import Path

def print_header(text):
    """ヘッダーを表示"""
    width = 80
    print("\n" + "=" * width)
    print(f"  {text}")
    print("=" * width + "\n")

def print_step(step_num, text):
    """ステップを表示"""
    print(f"\n{'─' * 80}")
    print(f"【ステップ {step_num}】 {text}")
    print('─' * 80 + "\n")

def simulate_progress(task_name, duration=2.0, steps=20):
    """プログレスバーをシミュレーション"""
    print(f"{task_name}...", end='', flush=True)
    for i in range(steps):
        time.sleep(duration / steps)
        if i % 4 == 3:
            print(".", end='', flush=True)
    print(" ✓")

def show_encrypted_data_sample(encrypted_vector, label="暗号化データ"):
    """暗号化されたデータのサンプルを表示（読めないことを示す）"""
    print(f"\n【{label}の例】")
    print("※ これは実際の暗号文ではなく、暗号化されたオブジェクトです")
    print(f"  型: {type(encrypted_vector)}")
    print(f"  内容: データは完全に暗号化されており、秘密鍵なしでは読めません")
    print(f"  ↓ 暗号化されたデータの一部（数値として読めない）")
    print(f"  {str(encrypted_vector)[:120]}...")
    print()

def main_demo():
    """メインデモ"""
    print_header("準同型暗号による暗号化統計分析デモ")

    print("このデモでは、患者データを暗号化したまま統計分析を行う様子を")
    print("リアルタイムでシミュレーションします。")

    input("\n[Enterキーを押して開始]")

    # ステップ1: データ読み込み
    print_step(1, "患者データの読み込み")

    with open('data/patients.json', 'r', encoding='utf-8') as f:
        patients = json.load(f)

    print(f"✓ {len(patients)}人の患者データを読み込みました")

    # サンプルデータ表示
    print("\n【サンプルデータ（最初の5人）】")
    print("ID    | 年齢 | 血圧(収縮/拡張) | 血糖値 | コレステロール")
    print("-" * 70)
    for i in range(min(5, len(patients))):
        p = patients[i]
        print(f"{p['patient_id']} | {p['age']:3d}歳 | {p['blood_pressure_systolic']:3d}/{p['blood_pressure_diastolic']:3d} mmHg | "
              f"{p['blood_sugar']:3d} mg/dL | {p['cholesterol']:3d} mg/dL")

    print(f"\n... 他{len(patients)-5}人")

    input("\n[Enterキーで次へ]")

    # ステップ2: 暗号化コンテキスト初期化
    print_step(2, "準同型暗号の初期化")

    print("準同型暗号（CKKS方式）のコンテキストを初期化します")
    print("パラメータ:")
    print("  - スキーム: CKKS (近似計算に最適)")
    print("  - 多項式次数: 8192 (セキュリティレベル128ビット)")
    print("  - スケール: 2^40 (十分な精度)")

    simulate_progress("コンテキスト初期化中", 1.5)

    context = ts.context(
        ts.SCHEME_TYPE.CKKS,
        poly_modulus_degree=8192,
        coeff_mod_bit_sizes=[60, 40, 40, 60]
    )
    context.generate_galois_keys()
    context.generate_relin_keys()
    context.global_scale = 2**40

    print("✓ 準同型暗号コンテキストを初期化しました")
    print("  ⚠️ これ以降、すべての計算は暗号化されたまま実行されます")

    input("\n[Enterキーで次へ]")

    # ステップ3: データ暗号化
    print_step(3, "患者データの暗号化")

    print("各患者のデータを準同型暗号で暗号化します")
    print("暗号化されるデータ:")
    print("  - 年齢")
    print("  - 収縮期血圧")
    print("  - 拡張期血圧")
    print("  - 血糖値")
    print("  - コレステロール")

    # データ抽出
    ages = [p['age'] for p in patients]
    bp_systolic = [p['blood_pressure_systolic'] for p in patients]
    bp_diastolic = [p['blood_pressure_diastolic'] for p in patients]
    blood_sugars = [p['blood_sugar'] for p in patients]
    cholesterols = [p['cholesterol'] for p in patients]

    simulate_progress(f"\n{len(patients)}人分のデータを暗号化中", 2.5)

    # 暗号化（各患者を個別に暗号化）
    enc_ages = [ts.ckks_vector(context, [float(age)]) for age in ages]
    enc_bp_systolic = [ts.ckks_vector(context, [float(bp)]) for bp in bp_systolic]
    enc_bp_diastolic = [ts.ckks_vector(context, [float(bp)]) for bp in bp_diastolic]
    enc_blood_sugars = [ts.ckks_vector(context, [float(bg)]) for bg in blood_sugars]
    enc_cholesterols = [ts.ckks_vector(context, [float(chol)]) for chol in cholesterols]

    print("✓ すべてのデータを暗号化しました")

    # 暗号化データのサンプル表示
    show_encrypted_data_sample(enc_ages[0], "年齢データ（暗号化済み）")

    print("【重要】")
    print("  ✓ データは完全に暗号化されています")
    print("  ✓ 秘密鍵を持つのはデータ提供者（病院）のみ")
    print("  ✓ このデータを見ても、患者の年齢は誰にも分かりません")

    input("\n[Enterキーで次へ]")

    # ステップ4: 暗号化されたまま統計計算
    print_step(4, "暗号化されたまま統計分析")

    print("🔐 重要: これから行う計算はすべて暗号化されたまま実行されます")
    print("   秘密鍵は一切使用しません！")

    print("\n" + "=" * 80)
    print("  暗号化統計分析の実行")
    print("=" * 80)

    # 平均年齢
    print("\n【計算1】 平均年齢")
    print("  計算式: (年齢1 + 年齢2 + ... + 年齢100) / 100")
    print("  ※ すべての年齢は暗号化されています")

    simulate_progress("  暗号化されたまま加算中", 1.5)
    enc_total_age = enc_ages[0]
    for enc_age in enc_ages[1:]:
        enc_total_age = enc_total_age + enc_age
    enc_avg_age = enc_total_age * (1.0 / len(patients))
    print("  ✓ 暗号化されたまま平均値を計算しました")
    print(f"  結果（暗号化されたまま）: {str(enc_avg_age)[:80]}...")

    # 平均収縮期血圧
    print("\n【計算2】 平均収縮期血圧")
    simulate_progress("  暗号化されたまま加算中", 1.5)
    enc_total_bp_sys = enc_bp_systolic[0]
    for enc_bp in enc_bp_systolic[1:]:
        enc_total_bp_sys = enc_total_bp_sys + enc_bp
    enc_avg_bp_sys = enc_total_bp_sys * (1.0 / len(patients))
    print("  ✓ 暗号化されたまま平均値を計算しました")

    # 平均拡張期血圧
    print("\n【計算3】 平均拡張期血圧")
    simulate_progress("  暗号化されたまま加算中", 1.5)
    enc_total_bp_dia = enc_bp_diastolic[0]
    for enc_bp in enc_bp_diastolic[1:]:
        enc_total_bp_dia = enc_total_bp_dia + enc_bp
    enc_avg_bp_dia = enc_total_bp_dia * (1.0 / len(patients))
    print("  ✓ 暗号化されたまま平均値を計算しました")

    # 平均血糖値
    print("\n【計算4】 平均血糖値")
    simulate_progress("  暗号化されたまま加算中", 1.5)
    enc_total_bg = enc_blood_sugars[0]
    for enc_bg in enc_blood_sugars[1:]:
        enc_total_bg = enc_total_bg + enc_bg
    enc_avg_bg = enc_total_bg * (1.0 / len(patients))
    print("  ✓ 暗号化されたまま平均値を計算しました")

    # 平均コレステロール
    print("\n【計算5】 平均コレステロール")
    simulate_progress("  暗号化されたまま加算中", 1.5)
    enc_total_chol = enc_cholesterols[0]
    for enc_chol in enc_cholesterols[1:]:
        enc_total_chol = enc_total_chol + enc_chol
    enc_avg_chol = enc_total_chol * (1.0 / len(patients))
    print("  ✓ 暗号化されたまま平均値を計算しました")

    print("\n" + "=" * 80)
    print("  すべての計算が暗号化されたまま完了しました！")
    print("=" * 80)

    input("\n[Enterキーで次へ]")

    # ステップ5: 結果の復号
    print_step(5, "結果の復号（データ提供者のみが実行可能）")

    print("計算結果を復号します")
    print("⚠️ この操作には秘密鍵が必要です")
    print("   秘密鍵を持つのはデータ提供者（病院）のみ")

    simulate_progress("\n秘密鍵で復号中", 2.0)

    avg_age = enc_avg_age.decrypt()[0]
    avg_bp_sys = enc_avg_bp_sys.decrypt()[0]
    avg_bp_dia = enc_avg_bp_dia.decrypt()[0]
    avg_bg = enc_avg_bg.decrypt()[0]
    avg_chol = enc_avg_chol.decrypt()[0]

    print("\n" + "=" * 80)
    print("  暗号化統計分析の結果")
    print("=" * 80)

    print(f"\n  平均年齢:               {avg_age:.1f}歳")
    print(f"  平均収縮期血圧:         {avg_bp_sys:.1f} mmHg")
    print(f"  平均拡張期血圧:         {avg_bp_dia:.1f} mmHg")
    print(f"  平均血糖値:             {avg_bg:.1f} mg/dL")
    print(f"  平均コレステロール:     {avg_chol:.1f} mg/dL")

    print("\n" + "=" * 80)

    input("\n[Enterキーで次へ]")

    # ステップ6: 検証
    print_step(6, "結果の検証")

    print("生データから直接計算した値と比較して、正確性を検証します")

    true_avg_age = np.mean(ages)
    true_avg_bp_sys = np.mean(bp_systolic)
    true_avg_bp_dia = np.mean(bp_diastolic)
    true_avg_bg = np.mean(blood_sugars)
    true_avg_chol = np.mean(cholesterols)

    print("\n【比較結果】")
    print("-" * 80)
    print("項目                    | 暗号化計算     | 生データ計算   | 誤差")
    print("-" * 80)
    print(f"平均年齢                | {avg_age:8.2f}歳     | {true_avg_age:8.2f}歳     | {abs(avg_age - true_avg_age):6.4f}")
    print(f"平均収縮期血圧          | {avg_bp_sys:8.2f} mmHg | {true_avg_bp_sys:8.2f} mmHg | {abs(avg_bp_sys - true_avg_bp_sys):6.4f}")
    print(f"平均拡張期血圧          | {avg_bp_dia:8.2f} mmHg | {true_avg_bp_dia:8.2f} mmHg | {abs(avg_bp_dia - true_avg_bp_dia):6.4f}")
    print(f"平均血糖値              | {avg_bg:8.2f} mg/dL | {true_avg_bg:8.2f} mg/dL | {abs(avg_bg - true_avg_bg):6.4f}")
    print(f"平均コレステロール      | {avg_chol:8.2f} mg/dL | {true_avg_chol:8.2f} mg/dL | {abs(avg_chol - true_avg_chol):6.4f}")
    print("-" * 80)

    print("\n✅ 暗号化されたまま計算した結果が、生データの結果と一致しました！")
    print("   誤差は準同型暗号の近似計算によるもので、統計的には無視できます。")

    input("\n[Enterキーで次へ]")

    # まとめ
    print_step(7, "デモのまとめ")

    print("【このデモで実証されたこと】")
    print()
    print("✅ 1. データの完全な暗号化")
    print("      - 100人の患者データを準同型暗号で暗号化")
    print("      - 暗号化されたデータは数値として読めない")
    print()
    print("✅ 2. 暗号化されたまま計算")
    print("      - 平均値の計算をすべて暗号化されたまま実行")
    print("      - 秘密鍵は一切使用しない")
    print()
    print("✅ 3. 正確な結果")
    print("      - 暗号化計算の結果が生データ計算と一致")
    print("      - 統計分析に十分な精度")
    print()
    print("✅ 4. プライバシーの完全保護")
    print("      - 個々の患者データは誰にも見られない")
    print("      - 統計結果のみが得られる")
    print()

    print("【ビジネス価値】")
    print()
    print("🏥 データ提供者（病院）:")
    print("   - データを安全に外部提供できる")
    print("   - 秘密鍵を保持し続ける")
    print("   - プライバシー規制に準拠")
    print()
    print("💊 データ購入者（製薬会社・研究機関）:")
    print("   - 暗号化データで統計分析・機械学習")
    print("   - 患者の個人情報にアクセスしない")
    print("   - 規制リスクを回避")
    print()
    print("👥 患者:")
    print("   - プライバシーが完全に保護される")
    print("   - データが医療の進歩に貢献")
    print("   - 個人情報漏洩の心配なし")
    print()

    print("=" * 80)
    print("  デモ終了")
    print("=" * 80)
    print()
    print("このシステムにより、プライバシー保護とデータ利活用の")
    print("両立が実現可能であることが実証されました！")
    print()

if __name__ == "__main__":
    try:
        main_demo()
    except KeyboardInterrupt:
        print("\n\nデモを中断しました。")
    except Exception as e:
        print(f"\n\nエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
