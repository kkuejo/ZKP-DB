import { useState } from 'react'
import axios from 'axios'
import './App.css'

function App() {
  const [file, setFile] = useState(null)
  const [dragActive, setDragActive] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)
  const apiBase = import.meta.env.VITE_API_BASE || '/api'

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0]
    if (selectedFile && selectedFile.name.endsWith('.csv')) {
      setFile(selectedFile)
      setError(null)
      setSuccess(null)
    } else {
      setError('CSVファイルを選択してください')
      setFile(null)
    }
  }

  const handleDragOver = (e) => {
    e.preventDefault()
    setDragActive(true)
  }

  const handleDragLeave = (e) => {
    e.preventDefault()
    setDragActive(false)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setDragActive(false)
    const droppedFile = e.dataTransfer.files?.[0]
    if (droppedFile) {
      if (droppedFile.name.endsWith('.csv')) {
        setFile(droppedFile)
        setError(null)
        setSuccess(null)
      } else {
        setError('CSVファイルをドロップしてください')
        setFile(null)
      }
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()

    if (!file) {
      setError('ファイルを選択してください')
      return
    }

    setLoading(true)
    setError(null)
    setSuccess(null)

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await axios.post(`${apiBase}/encrypt`, formData, {
        responseType: 'blob',
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })

      // ZIPファイルをダウンロード
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', 'encrypted_package.zip')
      document.body.appendChild(link)
      link.click()
      link.remove()

      setSuccess('暗号化パッケージを作成しました。ダウンロードを開始します...')
      setFile(null)
      // ファイル入力をリセット
      e.target.reset()
    } catch (err) {
      console.error('Error:', err)
      if (err.response && err.response.data) {
        // Blobからエラーメッセージを抽出
        const reader = new FileReader()
        reader.onload = () => {
          try {
            const errorData = JSON.parse(reader.result)
            setError(errorData.error || errorData.message || 'エラーが発生しました')
          } catch {
            setError('エラーが発生しました')
          }
        }
        reader.readAsText(err.response.data)
      } else {
        setError(err.message || 'サーバーに接続できません')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container">
      <header>
        <h1>🏥 ZKP-DB データ提供者</h1>
        <p className="subtitle">準同型暗号 + ゼロ知識証明によるプライバシー保護データ販売</p>
      </header>

      <main>
        <div className="card">
          <h2>患者データの暗号化</h2>
          <p className="description">
            患者データのCSVファイルをアップロードすると、準同型暗号で暗号化し、
            ゼロ知識証明で正当性を証明します。
          </p>

          <form onSubmit={handleSubmit}>
            <div
              className={`form-group drop-zone ${dragActive ? 'drag-active' : ''}`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
            >
              <label htmlFor="file-upload" className="file-label">
                <span className="file-icon">📁</span>
                <span>{file ? file.name : 'CSVファイルを選択またはドラッグ＆ドロップ'}</span>
              </label>
              <input
                id="file-upload"
                type="file"
                accept=".csv"
                onChange={handleFileChange}
                disabled={loading}
              />
              <p className="hint">ドラッグ＆ドロップでもアップロードできます</p>
            </div>

            {file && (
              <div className="file-info">
                <p>✓ ファイル: {file.name}</p>
                <p>✓ サイズ: {(file.size / 1024).toFixed(2)} KB</p>
              </div>
            )}

            <button type="submit" disabled={!file || loading} className="submit-btn">
              {loading ? '処理中...' : '暗号化して販売パッケージを作成'}
            </button>
          </form>

          {error && (
            <div className="message error">
              <strong>❌ エラー:</strong> {error}
            </div>
          )}

          {success && (
            <div className="message success">
              <strong>✅ 成功:</strong> {success}
            </div>
          )}
        </div>

        <div className="info-card">
          <h3>📦 販売パッケージの内容</h3>
          <ul>
            <li><strong>encrypted_data.pkl</strong> - 暗号化された患者データ</li>
            <li><strong>public_context.pkl</strong> - 公開鍵（購入者が計算に使用）</li>
            <li><strong>proof.json</strong> - ZKP証明（データの正当性を証明）</li>
            <li><strong>public_signals.json</strong> - 公開信号</li>
            <li><strong>verification_key.json</strong> - 検証鍵</li>
            <li><strong>metadata.json</strong> - メタデータ</li>
          </ul>

          <h3>🔒 セキュリティ要件</h3>
          <ul>
            <li>✅ k-匿名性: 最低100件のデータが必要</li>
            <li>✅ データ検証: 各フィールドが有効範囲内</li>
            <li>✅ ゼロ知識証明: データの正当性を数学的に証明</li>
            <li>✅ 準同型暗号: 暗号化されたまま統計計算可能</li>
          </ul>

          <h3>🔍 ZKPで検証している条件</h3>
          <ul>
            <li>年齢などの数値が事前に決めた範囲内であること</li>
            <li>血圧・血糖などの項目が不正な桁数/形式でないこと</li>
            <li>入力全体のハッシュ値が証明に含まれ、改ざんされていないこと</li>
            <li>検証鍵 (verification_key.json) で第三者が同じ検証を再現可能であること</li>
          </ul>

          <div className="warning">
            <strong>⚠️ 重要:</strong>
            <p>秘密鍵はサーバー側でのみ保持され、販売パッケージには含まれません。復号はAPI経由で処理されます。</p>
          </div>
        </div>
      </main>
    </div>
  )
}

export default App
