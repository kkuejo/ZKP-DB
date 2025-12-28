"""
データ提供者側API
- 暗号化・ZKPパッケージ作成
- 復号サービス（セキュリティチェック付き）
"""
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import pickle
import tempfile
import shutil
from pathlib import Path
import pandas as pd
import tenseal as ts
import io
import zipfile

from encryption_service import EncryptionService, ZKPService, create_data_package
from security_checks import SecurityChecker, PrivacyBudgetManager, log_security_event

app = Flask(__name__)
CORS(app)  # フロントエンドからのリクエストを許可

# セキュリティコンポーネント
security_checker = SecurityChecker()
budget_manager = PrivacyBudgetManager(total_budget=10.0)

# 秘密鍵を保管（実際の運用ではセキュアなストレージを使用）
secret_contexts = {}


@app.route('/api/health', methods=['GET'])
def health_check():
    """ヘルスチェック"""
    return jsonify({'status': 'healthy', 'service': 'provider-api'})


@app.route('/api/encrypt', methods=['POST'])
def encrypt_data():
    """
    患者データを暗号化し、ZKP証明を生成してパッケージを作成

    Request:
        - file: CSVファイル（multipart/form-data）

    Response:
        - ZIP file containing:
          - encrypted_data.pkl
          - public_context.pkl
          - proof.json
          - public_signals.json
          - verification_key.json
          - metadata.json
    """
    try:
        # ファイルを取得
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # CSVを読み込み
        csv_content = file.read().decode('utf-8')
        df = pd.read_csv(io.StringIO(csv_content))

        # k-匿名性チェック
        if len(df) < 100:
            log_security_event(
                'k-anonymity-violation',
                'provider',
                f'Attempted to encrypt {len(df)} records (minimum 100 required)',
                'WARNING'
            )
            return jsonify({
                'error': 'k-anonymity violation',
                'message': f'Need at least 100 records, got {len(df)}'
            }), 400

        # 暗号化サービス
        encryption_service = EncryptionService()
        encrypted_package = encryption_service.encrypt_patient_data(df)

        # ZKPサービス
        zkp_service = ZKPService()

        # サンプルとして最初の患者データのZKP証明を生成
        first_patient = df.iloc[0].to_dict()

        try:
            zkp_proof = zkp_service.generate_proof(first_patient)
        except ValueError as e:
            log_security_event(
                'zkp-generation-failed',
                'provider',
                f'Invalid data ranges: {str(e)}',
                'ERROR'
            )
            return jsonify({
                'error': 'Invalid data',
                'message': str(e)
            }), 400

        # 秘密鍵を保存（provider_idで管理）
        provider_id = f"provider_{len(secret_contexts)}"
        secret_contexts[provider_id] = encryption_service.context

        # ZIPファイルを作成
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # 暗号化データ
            zip_file.writestr('encrypted_data.pkl', encrypted_package['encrypted_data'])

            # 公開コンテキスト
            zip_file.writestr('public_context.pkl', encrypted_package['context_public'])

            # ZKP証明
            import json
            zip_file.writestr('proof.json', json.dumps(zkp_proof['proof'], indent=2))
            zip_file.writestr('public_signals.json',
                            json.dumps(zkp_proof['public_signals'], indent=2))

            # 検証鍵
            verification_key = zkp_service.get_verification_key()
            zip_file.writestr('verification_key.json',
                            json.dumps(verification_key, indent=2))

            # メタデータ
            metadata = {
                **encrypted_package['metadata'],
                'data_hash': zkp_proof['data_hash'],
                'provider_id': provider_id,
                'package_created': pd.Timestamp.now().isoformat()
            }
            zip_file.writestr('metadata.json', json.dumps(metadata, indent=2))

        zip_buffer.seek(0)

        log_security_event(
            'data-package-created',
            provider_id,
            f'Created encrypted package with {len(df)} records',
            'INFO'
        )

        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name='encrypted_package.zip'
        )

    except Exception as e:
        log_security_event(
            'encryption-error',
            'provider',
            f'Error during encryption: {str(e)}',
            'ERROR'
        )
        return jsonify({'error': str(e)}), 500


@app.route('/api/decrypt', methods=['POST'])
def decrypt_result():
    """
    暗号化された計算結果を復号
    セキュリティチェック付き

    Request JSON:
        {
            "provider_id": "provider_0",
            "purchaser_id": "pharma_company_123",
            "encrypted_result": "hex encoded pickled data",
            "metadata": {
                "operation": "mean",
                "field": "age",
                "sample_size": 100,
                "filters": {...}
            }
        }

    Response JSON:
        {
            "result": [55.2],
            "metadata": {...},
            "remaining_budget": 10.0,
            "remaining_requests": 95,
            "status": "success"
        }
    """
    try:
        data = request.get_json()

        # 必須フィールドのチェック
        required_fields = ['provider_id', 'purchaser_id', 'encrypted_result', 'metadata']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        provider_id = data['provider_id']
        purchaser_id = data['purchaser_id']
        encrypted_result_hex = data['encrypted_result']
        metadata = data['metadata']

        # === セキュリティチェック開始 ===

        # 1. メタデータ検証
        try:
            security_checker.validate_metadata(metadata)
        except ValueError as e:
            log_security_event(
                'invalid-metadata',
                purchaser_id,
                str(e),
                'WARNING'
            )
            return jsonify({'error': str(e)}), 400

        # 2. k-匿名性チェック
        try:
            security_checker.check_k_anonymity(metadata['sample_size'], min_k=100)
        except ValueError as e:
            log_security_event(
                'k-anonymity-violation',
                purchaser_id,
                str(e),
                'WARNING'
            )
            return jsonify({'error': str(e)}), 403

        # 3. 集約統計のみ許可
        try:
            security_checker.check_aggregate_query(metadata)
        except ValueError as e:
            log_security_event(
                'individual-data-request',
                purchaser_id,
                str(e),
                'WARNING'
            )
            return jsonify({'error': str(e)}), 403

        # 4. レート制限チェック
        try:
            security_checker.check_rate_limit(purchaser_id, max_requests=100,
                                            time_window_minutes=60)
        except ValueError as e:
            log_security_event(
                'rate-limit-exceeded',
                purchaser_id,
                str(e),
                'WARNING'
            )
            remaining = security_checker.get_remaining_requests(purchaser_id)
            return jsonify({
                'error': str(e),
                'remaining_requests': remaining,
                'retry_after': 3600
            }), 429

        # 5. データ再構成攻撃検出
        try:
            security_checker.detect_reconstruction_attack(
                purchaser_id, metadata,
                similarity_threshold=5,
                time_window_hours=24
            )
        except ValueError as e:
            log_security_event(
                'reconstruction-attack-detected',
                purchaser_id,
                str(e),
                'CRITICAL'
            )
            return jsonify({'error': str(e)}), 403

        # 6. プライバシーバジェットチェック（今回はepsilon=0.0）
        epsilon = metadata.get('privacy_budget', 0.0)
        try:
            budget_manager.check_budget(purchaser_id, epsilon)
        except ValueError as e:
            log_security_event(
                'privacy-budget-exceeded',
                purchaser_id,
                str(e),
                'WARNING'
            )
            return jsonify({
                'error': str(e),
                'remaining_budget': budget_manager.get_remaining_budget(purchaser_id)
            }), 403

        # === セキュリティチェック完了 ===

        # 秘密鍵を取得
        if provider_id not in secret_contexts:
            return jsonify({'error': 'Invalid provider_id'}), 404

        context = secret_contexts[provider_id]

        # 暗号化された結果をデコード
        encrypted_result_bytes = bytes.fromhex(encrypted_result_hex)
        encrypted_result = pickle.loads(encrypted_result_bytes)

        # 復号
        if isinstance(encrypted_result, list):
            # リストの場合
            decrypted_result = [item.decrypt()[0] for item in encrypted_result]
        else:
            # 単一値の場合
            decrypted_result = encrypted_result.decrypt()

        # バジェット消費
        budget_manager.consume_budget(purchaser_id, epsilon)

        # 残りリクエスト数
        remaining_requests = security_checker.get_remaining_requests(purchaser_id)

        log_security_event(
            'decryption-success',
            purchaser_id,
            f"Decrypted {metadata['operation']} on {metadata.get('field', 'unknown')}",
            'INFO'
        )

        return jsonify({
            'result': decrypted_result if isinstance(decrypted_result, list)
                     else decrypted_result.tolist(),
            'metadata': metadata,
            'remaining_budget': budget_manager.get_remaining_budget(purchaser_id),
            'remaining_requests': remaining_requests,
            'status': 'success'
        })

    except Exception as e:
        log_security_event(
            'decryption-error',
            data.get('purchaser_id', 'unknown'),
            f'Error during decryption: {str(e)}',
            'ERROR'
        )
        return jsonify({'error': str(e)}), 500


@app.route('/api/verify-proof', methods=['POST'])
def verify_proof():
    """
    ZKP証明を検証

    Request JSON:
        {
            "proof": {...},
            "public_signals": [...]
        }

    Response JSON:
        {
            "valid": true/false,
            "message": "..."
        }
    """
    try:
        data = request.get_json()

        if 'proof' not in data or 'public_signals' not in data:
            return jsonify({'error': 'Missing proof or public_signals'}), 400

        zkp_service = ZKPService()
        is_valid = zkp_service.verify_proof(data['proof'], data['public_signals'])

        return jsonify({
            'valid': is_valid,
            'message': 'Proof verification successful' if is_valid
                      else 'Proof verification failed'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("Starting Provider API...")
    print("Endpoints:")
    print("  POST /api/encrypt - Encrypt patient data and generate ZKP")
    print("  POST /api/decrypt - Decrypt computation results (with security checks)")
    print("  POST /api/verify-proof - Verify ZKP proof")
    print("\nSecurity features enabled:")
    print("  ✓ k-anonymity check (minimum 100 records)")
    print("  ✓ Aggregate-only queries")
    print("  ✓ Rate limiting (100 requests/hour)")
    print("  ✓ Reconstruction attack detection")
    print("  ✓ Privacy budget management")
    print("\nRunning on http://localhost:5000")
    app.run(debug=True, port=5000)
