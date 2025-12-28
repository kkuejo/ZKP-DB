import { useState } from 'react'
import axios from 'axios'
import './App.css'

function App() {
  // ZKP検証用の状態
  const [proofFile, setProofFile] = useState(null)
  const [publicSignalsFile, setPublicSignalsFile] = useState(null)
  const [verificationResult, setVerificationResult] = useState(null)
  const [showProofDetails, setShowProofDetails] = useState(false)

  // 準同型演算用の状態
  const [encryptedPackage, setEncryptedPackage] = useState(null)
  const [computeOperation, setComputeOperation] = useState('mean')
  const [computeField, setComputeField] = useState('age')
  const [computeResult, setComputeResult] = useState(null)
  const [availableFields, setAvailableFields] = useState([])

  // 復号リクエスト用の状態
  const [purchaserId, setPurchaserId] = useState('pharma_company_123')
  const [encryptedResult, setEncryptedResult] = useState('')
  const [encryptedResultFile, setEncryptedResultFile] = useState(null)
  const [manualPackage, setManualPackage] = useState(null)
  const [decryptionResult, setDecryptionResult] = useState(null)
  const [manualTab, setManualTab] = useState('form') // form | python
  const [computeMode, setComputeMode] = useState('simple') // simple | python
  const apiBase = import.meta.env.VITE_API_BASE || '/api'

  // 共通の状態
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // ZKP検証
  const handleProofFileChange = (e) => {
    setProofFile(e.target.files[0])
    setError(null)
  }

  const handlePublicSignalsFileChange = (e) => {
    setPublicSignalsFile(e.target.files[0])
    setError(null)
  }

  const handleVerify = async (e) => {
    e.preventDefault()

    if (!proofFile || !publicSignalsFile) {
      setError('証明ファイルと公開信号ファイルの両方を選択してください')
      return
    }

    setLoading(true)
    setError(null)
    setVerificationResult(null)

    try {
      const proofText = await proofFile.text()
      const publicSignalsText = await publicSignalsFile.text()

      const proof = JSON.parse(proofText)
      const publicSignals = JSON.parse(publicSignalsText)

      const response = await axios.post(`${apiBase}/verify-proof`, {
        proof,
        public_signals: publicSignals
      })

      setVerificationResult(response.data)
    } catch (err) {
      console.error('Error:', err)
      setError(err.response?.data?.error || err.message || '検証中にエラーが発生しました')
    } finally {
      setLoading(false)
    }
  }

  // 暗号化パッケージのアップロード
  const handlePackageChange = async (e) => {
    const file = e.target.files[0]
    setEncryptedPackage(file)
    setError(null)
    setComputeResult(null)

    // パッケージ内のメタデータを読み取って利用可能なフィールドを取得
    if (file) {
      try {
        // Note: ZIPファイルの中身を直接読むにはライブラリが必要
        // 今回は一般的なフィールドをデフォルトで表示
        setAvailableFields(['age', 'blood_pressure_systolic', 'blood_pressure_diastolic',
                           'blood_sugar', 'cholesterol', 'bmi'])
      } catch (err) {
        console.error('Error reading package:', err)
      }
    }
  }

  const handleManualPackageChange = (e) => {
    const file = e.target.files[0]
    setManualPackage(file || null)
    setError(null)
  }

  const handleEncryptedResultFileChange = (e) => {
    const file = e.target.files[0]
    setEncryptedResultFile(file || null)
    // ファイルを選択したらテキスト入力はクリアして扱いやすくする
    if (file) {
      setEncryptedResult('')
    }
    setError(null)
  }

  // 準同型演算の実行
  const handleCompute = async (e) => {
    e.preventDefault()

    if (!encryptedPackage) {
      setError('暗号化パッケージを選択してください')
      return
    }

    setLoading(true)
    setError(null)
    setComputeResult(null)

    try {
      // ステップ1: 準同型演算を実行
      const formData = new FormData()
      formData.append('encrypted_package', encryptedPackage)
      formData.append('operation', computeOperation)
      formData.append('field', computeField)

      const computeResponse = await axios.post(`${apiBase}/compute`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })

      const { encrypted_result, metadata, provider_id } = computeResponse.data

      // ステップ2: 暗号化された結果を復号
      const decryptResponse = await axios.post(`${apiBase}/decrypt`, {
        provider_id: provider_id,
        purchaser_id: purchaserId,
        encrypted_result: encrypted_result,
        metadata: metadata
      })

      setComputeResult({
        operation: metadata.operation,
        field: metadata.field,
        sample_size: metadata.sample_size,
        result: decryptResponse.data.result,
        remaining_budget: decryptResponse.data.remaining_budget,
        remaining_requests: decryptResponse.data.remaining_requests
      })

    } catch (err) {
      console.error('Error:', err)
      setError(err.response?.data?.error || err.message || '計算中にエラーが発生しました')
    } finally {
      setLoading(false)
    }
  }

  // 手動復号リクエスト
  const handleDecrypt = async (e) => {
    e.preventDefault()

    if (!manualPackage && !encryptedResult.trim() && !encryptedResultFile) {
      setError('暗号化された結果を入力するかファイルを選択してください')
      return
    }

    setLoading(true)
    setError(null)
    setDecryptionResult(null)

    try {
      const formData = new FormData()
      formData.append('purchaser_id', purchaserId)

      if (manualPackage) {
        formData.append('encrypted_package', manualPackage)
      }

      if (encryptedResultFile) {
        formData.append('encrypted_result_file', encryptedResultFile)
      } else if (encryptedResult.trim()) {
        formData.append('encrypted_result', encryptedResult.trim())
      }

      const response = await axios.post(`${apiBase}/decrypt`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })

      setDecryptionResult(response.data)
    } catch (err) {
      console.error('Error:', err)
      setError(err.response?.data?.error || err.message || '復号中にエラーが発生しました')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container">
      <header>
        <h1>💊 ZKP-DB データ購入者</h1>
        <p className="subtitle">データの検証と暗号化されたまま分析</p>
      </header>

      <main>
        {/* ZKP証明検証セクション */}
        <div className="card">
          <h2>🔍 ZKP証明の検証</h2>
          <p className="description">
            データ提供者から受け取った証明書を検証し、データの正当性を確認します。
          </p>
          <button
            type="button"
            className="secondary-btn"
            onClick={() => setShowProofDetails((v) => !v)}
            disabled={loading}
          >
            {showProofDetails ? '詳細を隠す' : '詳細説明'}
          </button>
          {showProofDetails && (
            <div className="info-box">
              <h3>proof.json / public_signals.json とは？</h3>
              <p><strong>proof.json:</strong> 証明本体。暗号化された計算で使った制約を満たすことを示す暗号学的証明（Groth16形式）。</p>
              <p><strong>public_signals.json:</strong> 検証に必要な公開信号。今回の回路では、入力データのハッシュと「検証OK」を表すフラグなどが含まれます。</p>
              <p><strong>何を証明しているか:</strong> 患者データの各フィールドが事前に定めた範囲・形式に収まっていることを、データ内容を明かさずに証明します。検証成功＝提供データが回路条件を満たしていることを意味します。</p>
            </div>
          )}

          <form onSubmit={handleVerify}>
            <div className="form-group">
              <label>proof.json</label>
              <input
                type="file"
                accept=".json"
                onChange={handleProofFileChange}
                disabled={loading}
              />
            </div>

            <div className="form-group">
              <label>public_signals.json</label>
              <input
                type="file"
                accept=".json"
                onChange={handlePublicSignalsFileChange}
                disabled={loading}
              />
            </div>

            <button type="submit" disabled={!proofFile || !publicSignalsFile || loading} className="submit-btn">
              {loading ? '検証中...' : '証明書を検証'}
            </button>
          </form>

          {verificationResult && (
            <div className={`message ${verificationResult.valid ? 'success' : 'error'}`}>
              <strong>{verificationResult.valid ? '✅ 検証成功' : '❌ 検証失敗'}:</strong>
              <p>{verificationResult.message}</p>
            </div>
          )}
        </div>

        <div className="tab-header">
          <button
            type="button"
            className={computeMode === 'simple' ? 'tab active' : 'tab'}
            onClick={() => setComputeMode('simple')}
            disabled={loading}
          >
            簡単な統計量の計算
          </button>
          <button
            type="button"
            className={computeMode === 'python' ? 'tab active' : 'tab'}
            onClick={() => setComputeMode('python')}
            disabled={loading}
          >
            Pythonを用いた複雑な統計量の計算
          </button>
        </div>

        {/* 簡単な統計量計算セクション */}
        {computeMode === 'simple' && (
        <div className="card">
          <h2>🧮 簡単な統計量の計算</h2>
          <p className="description">
            暗号化パッケージをアップロードして準同型計算を実行し、暗号化された結果をデータ提供者APIに送り返して復号します（フロント側に秘密鍵は届きません）。
          </p>

          <form onSubmit={handleCompute}>
            <div className="form-group">
              <label>暗号化パッケージ (encrypted_package.zip)</label>
              <input
                type="file"
                accept=".zip"
                onChange={handlePackageChange}
                disabled={loading}
              />
              {encryptedPackage && (
                <p className="file-info">選択されたファイル: {encryptedPackage.name}</p>
              )}
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>統計計算</label>
                <select
                  value={computeOperation}
                  onChange={(e) => setComputeOperation(e.target.value)}
                  disabled={loading}
                >
                  <option value="mean">平均 (mean)</option>
                  <option value="sum">合計 (sum)</option>
                  <option value="count">カウント (count)</option>
                </select>
              </div>

              <div className="form-group">
                <label>対象フィールド</label>
                {availableFields.length > 0 ? (
                  <select
                    value={computeField}
                    onChange={(e) => setComputeField(e.target.value)}
                    disabled={loading}
                  >
                    {availableFields.map(f => (
                      <option key={f} value={f}>{f}</option>
                    ))}
                  </select>
                ) : (
                  <input
                    type="text"
                    value={computeField}
                    onChange={(e) => setComputeField(e.target.value)}
                    placeholder="age"
                    disabled={loading}
                  />
                )}
              </div>

              <div className="form-group">
                <label>Purchaser ID</label>
                <input
                  type="text"
                  value={purchaserId}
                  onChange={(e) => setPurchaserId(e.target.value)}
                  disabled={loading}
                />
              </div>
            </div>

            <button type="submit" disabled={!encryptedPackage || loading} className="submit-btn">
              {loading ? '計算中...' : '暗号化されたまま計算実行'}
            </button>
          </form>

          {computeResult && (
            <div className="message success">
              <strong>✅ 計算完了:</strong>
              <div className="result-details">
                <p><strong>操作:</strong> {computeResult.operation}</p>
                <p><strong>フィールド:</strong> {computeResult.field}</p>
                <p><strong>サンプル数:</strong> {computeResult.sample_size}</p>
                <p><strong>結果:</strong> {JSON.stringify(computeResult.result)}</p>
                <p><strong>残りバジェット:</strong> {computeResult.remaining_budget}</p>
                <p><strong>残りリクエスト数:</strong> {computeResult.remaining_requests}</p>
              </div>
            </div>
          )}

          <div className="info-box">
            <p><strong>💡 ヒント:</strong></p>
            <p>
              計算結果は暗号化されたままサーバーに送られ、データ提供者APIで復号されます。秘密鍵はフロントに届きません。
              より複雑な計算が必要な場合は、Pythonスクリプトで暗号化計算→「Pythonを用いた複雑な統計量の計算」タブからAPI復号を行ってください。
            </p>
          </div>
        </div>
        )}

        {/* 複雑な統計量（Python計算 + API復号）セクション */}
        {computeMode === 'python' && (
        <div className="card">
          <h2>🔓 Pythonを用いた複雑な統計量の計算</h2>
          <p className="description">
            Pythonスクリプトなどで計算した暗号化結果を、データ提供者のAPIに送信して復号します。
            必要な情報だけを入力すれば、メタデータは暗号化パッケージから自動的に取得されます。
          </p>

          <div className="tab-header">
            <button
              type="button"
              className={manualTab === 'form' ? 'tab active' : 'tab'}
              onClick={() => setManualTab('form')}
              disabled={loading}
            >
              APIで復号
            </button>
            <button
              type="button"
              className={manualTab === 'python' ? 'tab active' : 'tab'}
              onClick={() => setManualTab('python')}
              disabled={loading}
            >
              Pythonでの分析方法
            </button>
          </div>

          {manualTab === 'form' ? (
          <form onSubmit={handleDecrypt}>
            <div className="form-row">
              <div className="form-group">
                <label>Purchaser ID</label>
                <input
                  type="text"
                  value={purchaserId}
                  onChange={(e) => setPurchaserId(e.target.value)}
                  disabled={loading}
                />
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>暗号化パッケージ (encrypted_package.zip)</label>
                <input
                  type="file"
                  accept=".zip"
                  onChange={handleManualPackageChange}
                  disabled={loading}
                />
                {manualPackage && (
                  <p className="file-info">メタデータを読み取るために {manualPackage.name} を利用します</p>
                )}
              </div>

              <div className="form-group">
                <label>暗号化された結果ファイル</label>
                <input
                  type="file"
                  accept=".txt,.json"
                  onChange={handleEncryptedResultFileChange}
                  disabled={loading}
                />
                {encryptedResultFile && (
                  <p className="file-info">選択されたファイル: {encryptedResultFile.name}</p>
                )}
              </div>
            </div>

            <div className="form-group">
              <label>暗号化された結果 (16進数) ※ファイルを選ばない場合はこちらに貼り付け</label>
              <textarea
                value={encryptedResult}
                onChange={(e) => setEncryptedResult(e.target.value)}
                placeholder="Pythonスクリプトで出力された暗号化データの16進数表現..."
                rows="4"
                disabled={loading}
              />
            </div>

            <button
              type="submit"
              disabled={(!encryptedResult.trim() && !encryptedResultFile && !manualPackage) || loading}
              className="submit-btn"
            >
              {loading ? '復号中...' : '復号リクエストを送信'}
            </button>
          </form>
          ) : (
            <div className="info-box python-guide">
              <h3>Pythonでの分析手順</h3>
              <p>暗号化パッケージを使ってローカルで計算し、暗号化された結果をフロントの「APIで復号」タブから送信して復号します。</p>
              <ol>
                <li>データ提供者から受け取った <code><span className="highlight-red">encrypted_package.zip</span></code> を手元に置く</li>
                <li>下記サンプルスクリプトを保存し、<code>python analyze_encrypted.py <span className="highlight-red">path/to/encrypted_package.zip</span></code> などで実行</li>
                <li>出力される暗号化結果（ファイルまたは16進数）を「APIで復号」タブでパッケージと一緒に送信</li>
              </ol>

              <p><strong>サンプル1: 暗号化結果をファイル出力（バイナリ）</strong></p>
              <pre className="code-block">
{`import sys, json, pickle, zipfile, tempfile
from pathlib import Path
import tenseal as ts

def load_package(zip_path):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp = Path(temp_dir)
        with zipfile.ZipFile(zip_path, 'r') as z:
            z.extractall(temp)
        enc_data = pickle.load(open(temp/'encrypted_data.pkl', 'rb'))
        context = ts.context_from(open(temp/'public_context.pkl', 'rb').read())
        metadata = json.load(open(temp/'metadata.json', 'r'))
    return enc_data, context, metadata

if len(sys.argv) < 2:
    print("Usage: python analyze_encrypted.py <encrypted_package.zip>")
    sys.exit(1)

enc_data, context, metadata = load_package(sys.argv[1])
field = 'age'  # 計算したいフィールド名
vectors = [ts.ckks_vector_from(context, b) for b in enc_data[field]]
sample_size = len(vectors)
total = vectors[0]
for v in vectors[1:]:
    total += v
mean_vec = total * (1.0 / sample_size)
encrypted_result_bytes = mean_vec.serialize()

out_path = Path("encrypted_result.bin")  # 保存先を必要に応じて変更
out_path.write_bytes(encrypted_result_bytes)

print("provider_id:", metadata["provider_id"])
print("sample_size:", sample_size)
print("encrypted_result file:", out_path)`}
              </pre>

              <p><strong>サンプル2: 暗号化結果を16進文字列で出力</strong></p>
              <pre className="code-block">
{`# python analyze_hex.py <encrypted_package.zip>
import sys, json, pickle, zipfile, tempfile
from pathlib import Path
import tenseal as ts

def load_package(zip_path):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp = Path(temp_dir)
        with zipfile.ZipFile(zip_path, 'r') as z:
            z.extractall(temp)
        enc_data = pickle.load(open(temp/'encrypted_data.pkl', 'rb'))
        context = ts.context_from(open(temp/'public_context.pkl', 'rb').read())
        metadata = json.load(open(temp/'metadata.json', 'r'))
    return enc_data, context, metadata

if len(sys.argv) < 2:
    print("Usage: python analyze_hex.py <encrypted_package.zip>")
    sys.exit(1)

enc_data, context, metadata = load_package(sys.argv[1])
field = 'age'
vectors = [ts.ckks_vector_from(context, b) for b in enc_data[field]]
sample_size = len(vectors)
total = vectors[0]
for v in vectors[1:]:
    total += v
mean_vec = total * (1.0 / sample_size)
encrypted_result_hex = mean_vec.serialize().hex()

print("provider_id:", metadata["provider_id"])
print("sample_size:", sample_size)
print("encrypted_result_hex:")
print(encrypted_result_hex)`}
              </pre>

                <p>サンプルスクリプトはリポジトリの <code>purchaser_compute.py</code> でも拡張版を用意しています。複雑な統計が必要な場合はそちらを使ってください。</p>
              </div>
            )}
          </div>
        )}

        {decryptionResult && (
            <div className="message success">
              <strong>✅ 復号成功:</strong>
              <div className="result-details">
                <p><strong>結果:</strong> {JSON.stringify(decryptionResult.result)}</p>
                <p><strong>残りバジェット:</strong> {decryptionResult.remaining_budget}</p>
                <p><strong>残りリクエスト数:</strong> {decryptionResult.remaining_requests}</p>
              </div>
            </div>
          )}

        {error && (
          <div className="message error">
            <strong>❌ エラー:</strong> {error}
          </div>
        )}

        {/* セキュリティ情報 */}
        <div className="info-card">
          <h3>🔒 セキュリティ制限</h3>
          <ul>
            <li>✅ k-匿名性: 最低100件のデータを含む統計のみ復号可能</li>
            <li>✅ 集約統計のみ: 個別データの復号は拒否されます</li>
            <li>✅ レート制限: 1時間あたり100リクエストまで</li>
            <li>✅ 攻撃検出: 類似クエリによるデータ再構成攻撃を検出</li>
          </ul>

          <div className="warning">
            <strong>⚠️ 重要:</strong>
            <p>
              これらの制限は「APIを通じた復号」に適用されます。ローカルでPython計算をしても、復号リクエストでは個別データは不可で、集約統計（平均・合計・標準偏差など）に限定されます。
            </p>
          </div>
        </div>
      </main>
    </div>
  )
}

export default App
