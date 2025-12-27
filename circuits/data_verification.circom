pragma circom 2.0.0;

include "../node_modules/circomlib/circuits/poseidon.circom";
include "../node_modules/circomlib/circuits/comparators.circom";

/*
 * 医療データ検証回路
 *
 * この回路は以下を証明します：
 * 1. データが正しいハッシュ値を持つこと
 * 2. データが有効な範囲内にあること（年齢、血圧など）
 */

template RangeCheck(min, max) {
    signal input value;
    signal output valid;

    // 最小値チェック
    component geMin = GreaterEqThan(32);
    geMin.in[0] <== value;
    geMin.in[1] <== min;

    // 最大値チェック
    component leMax = LessEqThan(32);
    leMax.in[0] <== value;
    leMax.in[1] <== max;

    // 両方の条件が満たされている
    valid <== geMin.out * leMax.out;
}

template MedicalDataVerification() {
    // プライベート入力（秘密にしたいデータ）
    signal input age;
    signal input blood_pressure_systolic;
    signal input blood_pressure_diastolic;
    signal input blood_sugar;
    signal input cholesterol;

    // パブリック入力（公開される情報）
    signal input salt;  // ランダムな値（セキュリティ向上のため）

    // パブリック出力
    signal output dataHash;
    signal output isValid;

    // 1. データのハッシュ値を計算
    component hasher = Poseidon(6);
    hasher.inputs[0] <== age;
    hasher.inputs[1] <== blood_pressure_systolic;
    hasher.inputs[2] <== blood_pressure_diastolic;
    hasher.inputs[3] <== blood_sugar;
    hasher.inputs[4] <== cholesterol;
    hasher.inputs[5] <== salt;

    dataHash <== hasher.out;

    // 2. データの妥当性チェック

    // 年齢: 0-120歳
    component ageCheck = RangeCheck(0, 120);
    ageCheck.value <== age;

    // 収縮期血圧: 80-200 mmHg
    component bpSystolicCheck = RangeCheck(80, 200);
    bpSystolicCheck.value <== blood_pressure_systolic;

    // 拡張期血圧: 50-130 mmHg
    component bpDiastolicCheck = RangeCheck(50, 130);
    bpDiastolicCheck.value <== blood_pressure_diastolic;

    // 血糖値: 50-300 mg/dL
    component bloodSugarCheck = RangeCheck(50, 300);
    bloodSugarCheck.value <== blood_sugar;

    // コレステロール: 100-400 mg/dL
    component cholesterolCheck = RangeCheck(100, 400);
    cholesterolCheck.value <== cholesterol;

    // すべてのチェックが通ったか確認
    signal check1;
    signal check2;
    signal check3;
    signal check4;

    check1 <== ageCheck.valid * bpSystolicCheck.valid;
    check2 <== check1 * bpDiastolicCheck.valid;
    check3 <== check2 * bloodSugarCheck.valid;
    check4 <== check3 * cholesterolCheck.valid;

    isValid <== check4;

    // isValidが1であることを制約
    isValid === 1;
}

component main {public [salt]} = MedicalDataVerification();
