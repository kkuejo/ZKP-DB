"""
データ提供者側API
- 暗号化・ZKPパッケージ作成
- 復号サービス（セキュリティチェック付き）
"""
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import pickle
import tempfile
from pathlib import Path
import pandas as pd
import tenseal as ts
import io
import zipfile
import json

from encryption_service import EncryptionService, ZKPService
from security_checks import SecurityChecker, PrivacyBudgetManager, log_security_event

app = Flask(__name__)
CORS(app)  # フロントエンドからのリクエストを許可

# セキュリティコンポーネント
security_checker = SecurityChecker()
budget_manager = PrivacyBudgetManager(total_budget=10.0)

# 秘密鍵を保管（実際の運用ではセキュアなストレージを使用）
secret_contexts = {}
SECRET_CONTEXT_DIR = Path(__file__).parent / 'secret_contexts'
SECRET_CONTEXT_DIR.mkdir(exist_ok=True)


def _load_secret_context(provider_id: str):
    """Load secret context from disk into memory if available."""
    if provider_id in secret_contexts:
        return secret_contexts[provider_id]

    ctx_path = SECRET_CONTEXT_DIR / f'{provider_id}.bin'
    if ctx_path.exists():
        try:
            secret_contexts[provider_id] = ts.context_from(ctx_path.read_bytes())
            return secret_contexts[provider_id]
        except Exception as e:
            log_security_event(
                'secret-context-load-failed',
                provider_id,
                f'Failed to load secret context: {str(e)}',
                'ERROR'
            )
    return None


def _persist_secret_context(provider_id: str, context_bytes: bytes, context_obj):
    """Persist secret context in memory and on disk."""
    secret_contexts[provider_id] = context_obj
    try:
        (SECRET_CONTEXT_DIR / f'{provider_id}.bin').write_bytes(context_bytes)
    except Exception as e:
        log_security_event(
            'secret-context-save-failed',
            provider_id,
            f'Failed to persist secret context: {str(e)}',
            'WARNING'
        )


def _generate_provider_id():
    """Generate a provider id without colliding with stored contexts."""
    idx = 0
    while True:
        candidate = f'provider_{idx}'
        if candidate not in secret_contexts and not (SECRET_CONTEXT_DIR / f'{candidate}.bin').exists():
            return candidate
        idx += 1


# 既存の秘密鍵コンテキストを事前ロード（サーバー再起動対策）
for ctx_file in SECRET_CONTEXT_DIR.glob('*.bin'):
    try:
        provider_id_from_file = ctx_file.stem
        secret_contexts[provider_id_from_file] = ts.context_from(ctx_file.read_bytes())
    except Exception as e:
        log_security_event(
            'secret-context-preload-failed',
            ctx_file.name,
            f'Failed to preload secret context: {str(e)}',
            'WARNING'
        )


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

        # CSVを読み込み（エンコーディング自動検出）
        csv_bytes = file.read()

        # 複数のエンコーディングを試行
        for encoding in ['utf-8', 'shift-jis', 'cp932', 'latin1']:
            try:
                csv_content = csv_bytes.decode(encoding)
                df = pd.read_csv(io.StringIO(csv_content))
                break
            except (UnicodeDecodeError, pd.errors.ParserError):
                if encoding == 'latin1':  # 最後のエンコーディング
                    raise ValueError(f"Could not decode CSV file with supported encodings")
                continue

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
        provider_id = _generate_provider_id()
        secret_context_bytes = encryption_service.serialize_context_for_storage()
        _persist_secret_context(provider_id, secret_context_bytes, encryption_service.context)

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
        metadata = None
        encrypted_result_hex = None
        provider_id = None
        purchaser_id = None

        # JSON or multipart両対応
        if request.content_type and 'multipart/form-data' in request.content_type:
            purchaser_id = request.form.get('purchaser_id')
            provider_id = request.form.get('provider_id')
            encrypted_result_hex = request.form.get('encrypted_result')

            # ファイルで暗号化結果が送られてきた場合
            if not encrypted_result_hex and 'encrypted_result_file' in request.files:
                encrypted_result_hex = request.files['encrypted_result_file'].read().decode()

            # metadataがJSON文字列として送られる場合
            if request.form.get('metadata'):
                metadata = json.loads(request.form.get('metadata'))

            # encrypted_package.zipが送られてきた場合はメタデータを抽出
            if 'encrypted_package' in request.files:
                package_file = request.files['encrypted_package']
                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_path = Path(temp_dir)
                    zip_path = temp_path / 'package.zip'
                    package_file.save(zip_path)

                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        zip_ref.extractall(temp_path)

                    metadata_path = temp_path / 'metadata.json'
                    if metadata_path.exists():
                        with open(metadata_path, 'r') as f:
                            metadata = json.load(f)
                            provider_id = provider_id or metadata.get('provider_id')
        else:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Invalid request body'}), 400

            provider_id = data.get('provider_id')
            purchaser_id = data.get('purchaser_id')
            encrypted_result_hex = data.get('encrypted_result')
            metadata = data.get('metadata')

        # 必須フィールドのチェック
        required_fields = {
            'provider_id': provider_id,
            'purchaser_id': purchaser_id,
            'encrypted_result': encrypted_result_hex,
            'metadata': metadata
        }
        for field, value in required_fields.items():
            if value is None:
                return jsonify({'error': f'Missing required field: {field}'}), 400

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
        context = _load_secret_context(provider_id)
        if not context:
            return jsonify({
                'error': 'Secret key not available for this provider',
                'message': 'Data provider needs to keep the private key online for decryption.'
            }), 404

        encrypted_result_hex = encrypted_result_hex.strip()

        # 暗号化された結果をデコード
        encrypted_result_bytes = bytes.fromhex(encrypted_result_hex)

        # バイト列からCKKSVectorを復元
        try:
            encrypted_vector = ts.ckks_vector_from(context, encrypted_result_bytes)
            # 復号
            decrypted_result = encrypted_vector.decrypt()
        except Exception as e:
            # pickleでシリアライズされている場合（レガシー対応）
            encrypted_result = pickle.loads(encrypted_result_bytes)
            if isinstance(encrypted_result, list):
                decrypted_result = [item.decrypt()[0] for item in encrypted_result]
            else:
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
            purchaser_id or 'unknown',
            f'Error during decryption: {str(e)}',
            'ERROR'
        )
        return jsonify({'error': str(e)}), 500


@app.route('/api/compute', methods=['POST'])
def compute_homomorphic():
    """
    暗号化されたデータに対して準同型演算を実行

    Request (multipart/form-data):
        - encrypted_package: ZIPファイル（暗号化パッケージ）
        - operation: 統計計算の種類 (mean, sum, std, variance, count, min, max)
        - field: 計算対象のフィールド名

    Response JSON:
        {
            "encrypted_result": "hex string",
            "metadata": {...},
            "provider_id": "provider_0"
        }
    """
    try:
        # ファイルとパラメータを取得
        if 'encrypted_package' not in request.files:
            return jsonify({'error': 'No encrypted package provided'}), 400

        package_file = request.files['encrypted_package']
        operation = request.form.get('operation', 'mean')
        field = request.form.get('field', 'age')

        # ZIPファイルを一時ディレクトリに解凍
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            zip_path = temp_path / 'package.zip'

            # ZIPファイルを保存
            package_file.save(zip_path)

            # 解凍
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_path)

            # 暗号化データと公開コンテキストを読み込み
            with open(temp_path / 'encrypted_data.pkl', 'rb') as f:
                encrypted_data = pickle.load(f)

            with open(temp_path / 'public_context.pkl', 'rb') as f:
                context_bytes = f.read()
                context = ts.context_from(context_bytes)

            # メタデータを読み込み
            with open(temp_path / 'metadata.json', 'r') as f:
                metadata = json.load(f)
                provider_id = metadata.get('provider_id', 'unknown')

            # 秘密鍵がサーバーに存在するか確認
            if not _load_secret_context(provider_id):
                return jsonify({
                    'error': 'Secret key not available on provider server',
                    'message': 'Please ensure the provider keeps the private key online before computing.'
                }), 400

            # 指定されたフィールドのデータを取得
            if field not in encrypted_data:
                return jsonify({'error': f'Field {field} not found in encrypted data'}), 400

            field_data_bytes = encrypted_data[field]

            # バイト列からCKKSVectorに変換
            encrypted_vectors = [
                ts.ckks_vector_from(context, vec_bytes)
                for vec_bytes in field_data_bytes
            ]

            sample_size = len(encrypted_vectors)

            # 準同型演算を実行
            if operation == 'mean':
                # 平均 = 合計 / 個数
                total = encrypted_vectors[0]
                for vec in encrypted_vectors[1:]:
                    total = total + vec
                result = total * (1.0 / sample_size)

            elif operation == 'sum':
                # 合計
                result = encrypted_vectors[0]
                for vec in encrypted_vectors[1:]:
                    result = result + vec

            elif operation == 'count':
                # 個数（暗号化されたスカラー値として返す）
                result = ts.ckks_vector(context, [float(sample_size)])

            elif operation in ['std', 'variance', 'min', 'max']:
                # これらの演算は準同型暗号では直接計算が困難
                # 近似的な実装または代替手段が必要
                return jsonify({
                    'error': f'Operation {operation} requires decryption',
                    'suggestion': 'Use Python script for advanced operations'
                }), 400

            else:
                return jsonify({'error': f'Unsupported operation: {operation}'}), 400

            # 結果を16進数でシリアライズ
            encrypted_result_hex = result.serialize().hex()

            return jsonify({
                'encrypted_result': encrypted_result_hex,
                'metadata': {
                    'operation': operation,
                    'field': field,
                    'sample_size': sample_size,
                    'filters': {}
                },
                'provider_id': provider_id,
                'message': f'Computed {operation} on {field} (encrypted)'
            })

    except Exception as e:
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
