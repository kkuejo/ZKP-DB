/**
 * ゼロ知識証明の検証スクリプト
 *
 * 生成された証明が正しいか検証します
 */

const fs = require('fs');
const path = require('path');
const snarkjs = require('snarkjs');

const KEYS_DIR = path.join(__dirname, '../keys');
const PROOFS_DIR = path.join(__dirname, '../proofs');

async function verifyProof(proofFile, publicFile) {
    console.log('🔍 証明を検証中...');

    try {
        // 検証鍵を読み込み
        const vkeyFile = path.join(KEYS_DIR, 'verification_key.json');
        const vkey = JSON.parse(fs.readFileSync(vkeyFile, 'utf8'));

        // 証明と公開シグナルを読み込み
        const proof = JSON.parse(fs.readFileSync(proofFile, 'utf8'));
        const publicSignals = JSON.parse(fs.readFileSync(publicFile, 'utf8'));

        console.log('検証データ:');
        console.log(`  証明ファイル: ${path.basename(proofFile)}`);
        console.log(`  データハッシュ: ${publicSignals[0]}`);
        console.log(`  有効性フラグ: ${publicSignals[1]}`);

        // 検証実行
        const isValid = await snarkjs.groth16.verify(vkey, publicSignals, proof);

        if (isValid) {
            console.log('\n✅ 証明は有効です！');
            console.log('このデータは:');
            console.log('  - 改ざんされていません');
            console.log('  - 正しい範囲内の値です');
            console.log('  - 実際のデータ値は秘匿されています');
            return true;
        } else {
            console.log('\n❌ 証明は無効です');
            console.log('データが改ざんされているか、範囲外の値が含まれています');
            return false;
        }

    } catch (error) {
        console.error('❌ 検証エラー:', error.message);
        throw error;
    }
}

async function verifyAllProofs() {
    console.log('='.repeat(60));
    console.log('すべての証明を検証');
    console.log('='.repeat(60));
    console.log('');

    // proofsディレクトリ内のすべての証明ファイルを取得
    const proofFiles = fs.readdirSync(PROOFS_DIR)
        .filter(file => file.startsWith('proof_') && file.endsWith('.json'));

    console.log(`${proofFiles.length}個の証明が見つかりました\n`);

    let validCount = 0;
    let invalidCount = 0;

    for (let i = 0; i < proofFiles.length; i++) {
        const proofFile = path.join(PROOFS_DIR, proofFiles[i]);
        const publicFile = proofFile.replace('proof_', 'public_');

        console.log(`[${i + 1}/${proofFiles.length}] ${proofFiles[i]}`);

        try {
            const isValid = await verifyProof(proofFile, publicFile);
            if (isValid) {
                validCount++;
            } else {
                invalidCount++;
            }
        } catch (error) {
            console.error('検証失敗:', error.message);
            invalidCount++;
        }

        console.log('');
    }

    console.log('='.repeat(60));
    console.log('検証結果サマリー');
    console.log('='.repeat(60));
    console.log(`総証明数: ${proofFiles.length}`);
    console.log(`有効: ${validCount}`);
    console.log(`無効: ${invalidCount}`);
    console.log('='.repeat(60));
}

async function demonstrateInvalidProof() {
    console.log('\n' + '='.repeat(60));
    console.log('デモ: 無効な証明の検出');
    console.log('='.repeat(60));
    console.log('');

    // 最初の証明ファイルを改ざん
    const proofFiles = fs.readdirSync(PROOFS_DIR)
        .filter(file => file.startsWith('proof_') && file.endsWith('.json'));

    if (proofFiles.length === 0) {
        console.log('証明ファイルが見つかりません');
        return;
    }

    const proofFile = path.join(PROOFS_DIR, proofFiles[0]);
    const publicFile = proofFile.replace('proof_', 'public_');

    // 公開シグナルを改ざん
    console.log('公開シグナルを改ざんしています...');
    const publicSignals = JSON.parse(fs.readFileSync(publicFile, 'utf8'));
    const originalHash = publicSignals[0];
    publicSignals[0] = (BigInt(publicSignals[0]) + BigInt(1)).toString(); // ハッシュを変更

    console.log(`元のハッシュ: ${originalHash}`);
    console.log(`改ざん後: ${publicSignals[0]}\n`);

    // 改ざんされたデータで検証
    try {
        const vkeyFile = path.join(KEYS_DIR, 'verification_key.json');
        const vkey = JSON.parse(fs.readFileSync(vkeyFile, 'utf8'));
        const proof = JSON.parse(fs.readFileSync(proofFile, 'utf8'));

        const isValid = await snarkjs.groth16.verify(vkey, publicSignals, proof);

        if (!isValid) {
            console.log('✅ 正しく改ざんを検出しました！');
            console.log('ZKPは改ざんを防ぐことができます。');
        } else {
            console.log('⚠️  改ざんが検出されませんでした（これは起こらないはずです）');
        }
    } catch (error) {
        console.error('検証エラー:', error.message);
    }

    console.log('='.repeat(60));
}

// メイン実行
if (require.main === module) {
    const args = process.argv.slice(2);

    if (args.length === 1 && args[0] === '--demo-invalid') {
        // 無効な証明のデモ
        demonstrateInvalidProof().catch(console.error);
    } else if (args.length === 2 && args[0] === '--file') {
        // 特定のファイルを検証
        const proofFile = path.join(PROOFS_DIR, args[1]);
        const publicFile = proofFile.replace('proof_', 'public_');
        verifyProof(proofFile, publicFile).catch(console.error);
    } else {
        // すべての証明を検証
        verifyAllProofs().catch(console.error);
    }
}

module.exports = { verifyProof };
