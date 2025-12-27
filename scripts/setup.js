/**
 * ZKP回路のセットアップスクリプト
 *
 * このスクリプトは以下を行います：
 * 1. Circom回路のコンパイル
 * 2. Powers of Tau セレモニー
 * 3. 証明鍵と検証鍵の生成
 */

const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');
const util = require('util');

const execPromise = util.promisify(exec);

const CIRCUITS_DIR = path.join(__dirname, '../circuits');
const KEYS_DIR = path.join(__dirname, '../keys');
const BUILD_DIR = path.join(CIRCUITS_DIR, 'build');

// ディレクトリ作成
if (!fs.existsSync(BUILD_DIR)) {
    fs.mkdirSync(BUILD_DIR, { recursive: true });
}

async function compileCircuit() {
    console.log('📝 Circom回路をコンパイル中...');

    try {
        const { stdout, stderr } = await execPromise(
            `circom ${CIRCUITS_DIR}/data_verification.circom --r1cs --wasm --sym -o ${BUILD_DIR}`
        );

        if (stderr) {
            console.log('警告:', stderr);
        }

        console.log('✓ 回路のコンパイルが完了しました');
        return true;
    } catch (error) {
        console.error('❌ コンパイルエラー:', error.message);
        return false;
    }
}

async function generatePowersOfTau() {
    console.log('🔑 Powers of Tau セレモニーを実行中...');

    const ptauFile = path.join(KEYS_DIR, 'pot12_final.ptau');

    // すでに存在する場合はスキップ
    if (fs.existsSync(ptauFile)) {
        console.log('✓ Powers of Tau ファイルは既に存在します');
        return true;
    }

    try {
        // 新しいPowers of Tauを開始
        console.log('  新しいセレモニーを開始...');
        await execPromise(
            `snarkjs powersoftau new bn128 12 ${KEYS_DIR}/pot12_0000.ptau -v`
        );

        // 貢献
        console.log('  貢献を追加...');
        await execPromise(
            `snarkjs powersoftau contribute ${KEYS_DIR}/pot12_0000.ptau ${KEYS_DIR}/pot12_0001.ptau --name="First contribution" -v -e="random text"`
        );

        // フェーズ2準備
        console.log('  フェーズ2を準備...');
        await execPromise(
            `snarkjs powersoftau prepare phase2 ${KEYS_DIR}/pot12_0001.ptau ${ptauFile} -v`
        );

        // 一時ファイル削除
        fs.unlinkSync(path.join(KEYS_DIR, 'pot12_0000.ptau'));
        fs.unlinkSync(path.join(KEYS_DIR, 'pot12_0001.ptau'));

        console.log('✓ Powers of Tau セレモニーが完了しました');
        return true;
    } catch (error) {
        console.error('❌ Powers of Tau エラー:', error.message);
        return false;
    }
}

async function generateKeys() {
    console.log('🔐 証明鍵と検証鍵を生成中...');

    try {
        const r1csFile = path.join(BUILD_DIR, 'data_verification.r1cs');
        const ptauFile = path.join(KEYS_DIR, 'pot12_final.ptau');
        const zkeyFile = path.join(KEYS_DIR, 'data_verification_0000.zkey');
        const finalZkeyFile = path.join(KEYS_DIR, 'data_verification_final.zkey');
        const vkeyFile = path.join(KEYS_DIR, 'verification_key.json');

        // zkey生成
        console.log('  zkey生成中...');
        await execPromise(
            `snarkjs groth16 setup ${r1csFile} ${ptauFile} ${zkeyFile}`
        );

        // 貢献
        console.log('  貢献を追加中...');
        await execPromise(
            `snarkjs zkey contribute ${zkeyFile} ${finalZkeyFile} --name="1st Contributor" -v -e="another random text"`
        );

        // 検証鍵をエクスポート
        console.log('  検証鍵をエクスポート中...');
        await execPromise(
            `snarkjs zkey export verificationkey ${finalZkeyFile} ${vkeyFile}`
        );

        // 一時ファイル削除
        fs.unlinkSync(zkeyFile);

        console.log('✓ 鍵の生成が完了しました');
        console.log(`  証明鍵: ${finalZkeyFile}`);
        console.log(`  検証鍵: ${vkeyFile}`);

        return true;
    } catch (error) {
        console.error('❌ 鍵生成エラー:', error.message);
        return false;
    }
}

async function printCircuitInfo() {
    console.log('\n📊 回路情報:');

    try {
        const { stdout } = await execPromise(
            `snarkjs r1cs info ${BUILD_DIR}/data_verification.r1cs`
        );
        console.log(stdout);
    } catch (error) {
        console.error('回路情報の取得に失敗:', error.message);
    }
}

async function main() {
    console.log('='.repeat(60));
    console.log('ZKP回路セットアップ開始');
    console.log('='.repeat(60));
    console.log('');

    // 1. 回路のコンパイル
    const compileSuccess = await compileCircuit();
    if (!compileSuccess) {
        console.error('セットアップ失敗: コンパイルエラー');
        process.exit(1);
    }

    console.log('');

    // 2. Powers of Tau
    const tauSuccess = await generatePowersOfTau();
    if (!tauSuccess) {
        console.error('セットアップ失敗: Powers of Tau エラー');
        process.exit(1);
    }

    console.log('');

    // 3. 鍵生成
    const keysSuccess = await generateKeys();
    if (!keysSuccess) {
        console.error('セットアップ失敗: 鍵生成エラー');
        process.exit(1);
    }

    console.log('');

    // 4. 回路情報表示
    await printCircuitInfo();

    console.log('');
    console.log('='.repeat(60));
    console.log('✅ セットアップが完了しました！');
    console.log('='.repeat(60));
}

main().catch(console.error);
