/**
 * ゼロ知識証明の生成スクリプト
 *
 * 患者データから証明を生成します
 */

const fs = require('fs');
const path = require('path');
const snarkjs = require('snarkjs');

const CIRCUITS_DIR = path.join(__dirname, '../circuits/build');
const KEYS_DIR = path.join(__dirname, '../keys');
const DATA_DIR = path.join(__dirname, '../data');
const PROOFS_DIR = path.join(__dirname, '../proofs');

// proofsディレクトリが存在しない場合は作成
if (!fs.existsSync(PROOFS_DIR)) {
    fs.mkdirSync(PROOFS_DIR, { recursive: true });
}

async function generateProof(patientData, salt) {
    console.log('🔒 証明を生成中...');
    console.log(`患者ID: ${patientData.patient_id}`);

    // 入力データを準備
    const input = {
        age: patientData.age,
        blood_pressure_systolic: patientData.blood_pressure_systolic,
        blood_pressure_diastolic: patientData.blood_pressure_diastolic,
        blood_sugar: patientData.blood_sugar,
        cholesterol: patientData.cholesterol,
        salt: salt
    };

    console.log('入力データ:');
    console.log(`  年齢: ${input.age}`);
    console.log(`  収縮期血圧: ${input.blood_pressure_systolic} mmHg`);
    console.log(`  拡張期血圧: ${input.blood_pressure_diastolic} mmHg`);
    console.log(`  血糖値: ${input.blood_sugar} mg/dL`);
    console.log(`  コレステロール: ${input.cholesterol} mg/dL`);

    try {
        // Witnessを計算
        const wasmFile = path.join(CIRCUITS_DIR, 'data_verification_js/data_verification.wasm');
        const wtnsFile = path.join(PROOFS_DIR, `witness_${patientData.patient_id}.wtns`);

        console.log('  Witnessを計算中...');
        await snarkjs.wtns.calculate(input, wasmFile, wtnsFile);

        // 証明を生成
        const zkeyFile = path.join(KEYS_DIR, 'data_verification_final.zkey');

        console.log('  証明を生成中...');
        const { proof, publicSignals } = await snarkjs.groth16.prove(zkeyFile, wtnsFile);

        // 証明を保存
        const proofFile = path.join(PROOFS_DIR, `proof_${patientData.patient_id}.json`);
        const publicFile = path.join(PROOFS_DIR, `public_${patientData.patient_id}.json`);

        fs.writeFileSync(proofFile, JSON.stringify(proof, null, 2));
        fs.writeFileSync(publicFile, JSON.stringify(publicSignals, null, 2));

        console.log('✓ 証明の生成が完了しました');
        console.log(`  証明ファイル: ${proofFile}`);
        console.log(`  公開シグナル: ${publicFile}`);

        // パブリックシグナルの内容
        console.log('\n公開情報:');
        console.log(`  データハッシュ: ${publicSignals[0]}`);
        console.log(`  有効性: ${publicSignals[1] === '1' ? '有効' : '無効'}`);
        console.log(`  Salt: ${salt}`);

        return { proof, publicSignals };

    } catch (error) {
        console.error('❌ 証明生成エラー:', error.message);
        throw error;
    }
}

async function main() {
    console.log('='.repeat(60));
    console.log('ゼロ知識証明生成');
    console.log('='.repeat(60));
    console.log('');

    // 患者データを読み込み
    const patientsFile = path.join(DATA_DIR, 'patients.json');
    const patients = JSON.parse(fs.readFileSync(patientsFile, 'utf8'));

    console.log(`✓ ${patients.length}人の患者データを読み込みました\n`);

    // 最初の5人の患者について証明を生成（デモ用）
    const numProofs = Math.min(5, patients.length);
    console.log(`${numProofs}人の患者について証明を生成します...\n`);

    for (let i = 0; i < numProofs; i++) {
        const patient = patients[i];
        const salt = Math.floor(Math.random() * 1000000); // ランダムなsalt

        console.log(`[${i + 1}/${numProofs}]`);
        await generateProof(patient, salt);
        console.log('');
    }

    console.log('='.repeat(60));
    console.log('✅ すべての証明が生成されました！');
    console.log('='.repeat(60));
}

// コマンドライン引数で単一の患者の証明を生成することも可能
if (require.main === module) {
    const args = process.argv.slice(2);

    if (args.length === 2 && args[0] === '--patient') {
        // 特定の患者IDで証明を生成
        const patientId = args[1];
        const patientsFile = path.join(DATA_DIR, 'patients.json');
        const patients = JSON.parse(fs.readFileSync(patientsFile, 'utf8'));
        const patient = patients.find(p => p.patient_id === patientId);

        if (patient) {
            const salt = Math.floor(Math.random() * 1000000);
            generateProof(patient, salt).catch(console.error);
        } else {
            console.error(`患者ID ${patientId} が見つかりません`);
            process.exit(1);
        }
    } else {
        main().catch(console.error);
    }
}

module.exports = { generateProof };
