"""
患者ダミーデータ生成スクリプト
100人の患者の医療データを生成します
"""

import json
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# 日本語の疾患名リスト
DISEASES = [
    "糖尿病",
    "高血圧",
    "脂質異常症",
    "心筋梗塞",
    "脳卒中",
    "慢性腎臓病",
    "COPD",
    "喘息",
    "がん（肺）",
    "がん（胃）",
    "がん（大腸）",
    "骨粗鬆症",
    "認知症",
    "うつ病"
]

# 治療法リスト
TREATMENTS = {
    "糖尿病": ["インスリン療法", "メトホルミン", "食事療法"],
    "高血圧": ["ARB", "カルシウム拮抗薬", "利尿薬"],
    "脂質異常症": ["スタチン", "フィブラート", "食事療法"],
    "心筋梗塞": ["抗血小板薬", "β遮断薬", "心臓リハビリ"],
    "脳卒中": ["抗凝固薬", "リハビリテーション", "血圧管理"],
    "慢性腎臓病": ["食事療法", "透析", "降圧薬"],
    "COPD": ["気管支拡張薬", "ステロイド", "酸素療法"],
    "喘息": ["吸入ステロイド", "β刺激薬", "環境調整"],
    "がん（肺）": ["化学療法", "放射線療法", "手術"],
    "がん（胃）": ["内視鏡的切除", "手術", "化学療法"],
    "がん（大腸）": ["手術", "化学療法", "放射線療法"],
    "骨粗鬆症": ["ビスホスホネート", "カルシウム補充", "運動療法"],
    "認知症": ["ドネペジル", "リハビリ", "介護支援"],
    "うつ病": ["SSRI", "認知行動療法", "心理療法"]
}

def generate_patient_data(num_patients=100):
    """
    患者データを生成

    Args:
        num_patients: 生成する患者数

    Returns:
        患者データのリスト
    """
    patients = []

    for i in range(num_patients):
        patient_id = f"P{i+1:04d}"

        # 年齢: 20-90歳
        age = random.randint(20, 90)

        # 性別
        gender = random.choice(["男性", "女性"])

        # 血圧: 年齢に応じて現実的な値
        base_bp_systolic = 110 + (age - 20) * 0.5
        blood_pressure_systolic = int(np.random.normal(base_bp_systolic, 15))
        blood_pressure_diastolic = int(blood_pressure_systolic * 0.6 + random.randint(-5, 5))

        # 血糖値: 70-200 mg/dL
        blood_sugar = int(np.random.normal(100, 20))
        blood_sugar = max(70, min(200, blood_sugar))

        # コレステロール: 150-300 mg/dL
        cholesterol = int(np.random.normal(220, 30))
        cholesterol = max(150, min(300, cholesterol))

        # BMI: 18-35
        bmi = round(np.random.normal(23, 3), 1)
        bmi = max(18, min(35, bmi))

        # 疾患（年齢が高いほど複数持つ可能性）
        num_diseases = 1 if age < 50 else random.randint(1, 3)
        diseases = random.sample(DISEASES, num_diseases)

        # 治療法
        treatments = []
        for disease in diseases:
            treatment = random.choice(TREATMENTS[disease])
            treatments.append(treatment)

        # 入院歴（0-5回）
        hospitalization_count = random.choices([0, 1, 2, 3, 4, 5],
                                              weights=[40, 30, 15, 10, 3, 2])[0]

        # 最終診察日
        days_ago = random.randint(1, 365)
        last_visit = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")

        patient = {
            "patient_id": patient_id,
            "age": age,
            "gender": gender,
            "blood_pressure_systolic": blood_pressure_systolic,
            "blood_pressure_diastolic": blood_pressure_diastolic,
            "blood_sugar": blood_sugar,
            "cholesterol": cholesterol,
            "bmi": bmi,
            "diseases": diseases,
            "treatments": treatments,
            "hospitalization_count": hospitalization_count,
            "last_visit": last_visit
        }

        patients.append(patient)

    return patients

def save_data(patients, format='json'):
    """
    データを保存

    Args:
        patients: 患者データリスト
        format: 保存形式 ('json' or 'csv')
    """
    if format == 'json':
        with open('data/patients.json', 'w', encoding='utf-8') as f:
            json.dump(patients, f, ensure_ascii=False, indent=2)
        print(f"✓ データをdata/patients.jsonに保存しました")

    elif format == 'csv':
        # CSVの場合、リスト型のフィールドを文字列に変換
        patients_csv = []
        for p in patients:
            p_copy = p.copy()
            p_copy['diseases'] = ', '.join(p['diseases'])
            p_copy['treatments'] = ', '.join(p['treatments'])
            patients_csv.append(p_copy)

        df = pd.DataFrame(patients_csv)
        df.to_csv('data/patients.csv', index=False, encoding='utf-8')
        print(f"✓ データをdata/patients.csvに保存しました")

def generate_statistics(patients):
    """
    データの統計情報を表示
    """
    print("\n" + "="*50)
    print("データ統計情報")
    print("="*50)

    ages = [p['age'] for p in patients]
    print(f"患者数: {len(patients)}人")
    print(f"平均年齢: {np.mean(ages):.1f}歳")
    print(f"年齢範囲: {min(ages)}-{max(ages)}歳")

    gender_count = {}
    for p in patients:
        gender = p['gender']
        gender_count[gender] = gender_count.get(gender, 0) + 1
    print(f"\n性別分布:")
    for gender, count in gender_count.items():
        print(f"  {gender}: {count}人 ({count/len(patients)*100:.1f}%)")

    disease_count = {}
    for p in patients:
        for disease in p['diseases']:
            disease_count[disease] = disease_count.get(disease, 0) + 1

    print(f"\n主要疾患分布（上位5位）:")
    sorted_diseases = sorted(disease_count.items(), key=lambda x: x[1], reverse=True)
    for disease, count in sorted_diseases[:5]:
        print(f"  {disease}: {count}人")

    blood_pressures = [p['blood_pressure_systolic'] for p in patients]
    print(f"\n平均収縮期血圧: {np.mean(blood_pressures):.1f} mmHg")

    blood_sugars = [p['blood_sugar'] for p in patients]
    print(f"平均血糖値: {np.mean(blood_sugars):.1f} mg/dL")

    cholesterols = [p['cholesterol'] for p in patients]
    print(f"平均コレステロール: {np.mean(cholesterols):.1f} mg/dL")

    print("="*50 + "\n")

if __name__ == "__main__":
    print("患者ダミーデータを生成中...")

    # 乱数シード固定（再現性のため）
    random.seed(42)
    np.random.seed(42)

    # 100人の患者データ生成
    patients = generate_patient_data(100)

    # 統計情報表示
    generate_statistics(patients)

    # データ保存
    save_data(patients, format='json')
    save_data(patients, format='csv')

    print("完了！")
