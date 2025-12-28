import { useState } from 'react'
import axios from 'axios'
import './App.css'

function App() {
  const [proofFile, setProofFile] = useState(null)
  const [publicSignalsFile, setPublicSignalsFile] = useState(null)
  const [verificationResult, setVerificationResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // 復号リクエスト用の状態
  const [providerId, setProviderId] = useState('provider_0')
  const [purchaserId, setPurchaserId] = useState('pharma_company_123')
  const [encryptedResult, setEncryptedResult] = useState('')
  const [operation, setOperation] = useState('mean')
  const [field, setField] = useState('age')
  const [sampleSize, setSampleSize] = useState('100')
  const [decryptionResult, setDecryptionResult] = useState(null)

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
      // ファイルを読み込み
      const proofText = await proofFile.text()
      const publicSignalsText = await publicSignalsFile.text()

      const proof = JSON.parse(proofText)
      const publicSignals = JSON.parse(publicSignalsText)

      // APIに検証リクエスト
      const response = await axios.post('/api/verify-proof', {
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

  const handleDecrypt = async (e) => {
    e.preventDefault()

    if (!encryptedResult.trim()) {
      setError('暗号化された結果を入力してください')
      return
    }

    setLoading(true)
    setError(null)
    setDecryptionResult(null)

    try {
      const response = await axios.post('/api/decrypt', {
        provider_id: providerId,
        purchaser_id: purchaserId,
        encrypted_result: encryptedResult,
        metadata: {
          operation,
          field,
          sample_size: parseInt(sampleSize),
          filters: {}
        }
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

        {/* 復号リクエストセクション */}
        <div className="card">
          <h2>🔓 計算結果の復号</h2>
          <p className="description">
            暗号化されたまま計算した結果を、データ提供者のAPIに送信して復号します。
          </p>

          <form onSubmit={handleDecrypt}>
            <div className="form-row">
              <div className="form-group">
                <label>Provider ID</label>
                <input
                  type="text"
                  value={providerId}
                  onChange={(e) => setProviderId(e.target.value)}
                  disabled={loading}
                />
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

            <div className="form-row">
              <div className="form-group">
                <label>操作</label>
                <select value={operation} onChange={(e) => setOperation(e.target.value)} disabled={loading}>
                  <option value="mean">平均 (mean)</option>
                  <option value="sum">合計 (sum)</option>
                  <option value="std">標準偏差 (std)</option>
                  <option value="count">カウント (count)</option>
                </select>
              </div>

              <div className="form-group">
                <label>フィールド</label>
                <input
                  type="text"
                  value={field}
                  onChange={(e) => setField(e.target.value)}
                  placeholder="age, blood_pressure, etc."
                  disabled={loading}
                />
              </div>

              <div className="form-group">
                <label>サンプルサイズ</label>
                <input
                  type="number"
                  value={sampleSize}
                  onChange={(e) => setSampleSize(e.target.value)}
                  min="100"
                  disabled={loading}
                />
              </div>
            </div>

            <div className="form-group">
              <label>暗号化された結果 (16進数)</label>
              <textarea
                value={encryptedResult}
                onChange={(e) => setEncryptedResult(e.target.value)}
                placeholder="暗号化されたデータの16進数表現..."
                rows="4"
                disabled={loading}
              />
            </div>

            <button type="submit" disabled={!encryptedResult || loading} className="submit-btn">
              {loading ? '復号中...' : '復号リクエストを送信'}
            </button>
          </form>

          {decryptionResult && (
            <div className="message success">
              <strong>✅ 復号成功:</strong>
              <p>結果: {JSON.stringify(decryptionResult.result)}</p>
              <p>残りバジェット: {decryptionResult.remaining_budget}</p>
              <p>残りリクエスト数: {decryptionResult.remaining_requests}</p>
            </div>
          )}
        </div>

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
              個別患者データの復号は、プライバシー保護のため許可されません。
              集約統計（平均、合計、標準偏差など）のみ利用可能です。
            </p>
          </div>
        </div>
      </main>
    </div>
  )
}

export default App
