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

          <div className="file-explanation">
            <h4>encrypted_data.pkl（暗号化データ）</h4>
            <p><strong>用途:</strong> 患者データを準同型暗号（CKKS）で暗号化したデータ</p>
            <p><strong>特徴:</strong> 暗号化されたまま統計計算（平均、合計など）が可能</p>
          </div>

          <div className="file-explanation">
            <h4>public_context.pkl（公開鍵コンテキスト）</h4>
            <p><strong>用途:</strong> 購入者が暗号化データに対して準同型演算を実行するための公開鍵</p>
            <p><strong>重要:</strong> 秘密鍵は含まれないため、復号はできない</p>
          </div>

          <div className="file-explanation">
            <h4>proof.json（ZKP証明）</h4>
            <p><strong>用途:</strong> データの正当性を数学的に証明</p>
            <p><strong>内容:</strong> Groth16 zkSNARK形式の暗号学的証明データ</p>
            <p><strong>証明内容:</strong> 年齢、血圧、血糖値、コレステロールの範囲が有効であることを、実際の値を明かさずに証明</p>
            <p><strong>サイズ:</strong> 約1KB（非常にコンパクト）</p>
          </div>

          <div className="file-explanation">
            <h4>public_signals.json（公開信号）</h4>
            <p><strong>用途:</strong> ZKP証明を検証するための公開パラメータ</p>
            <p><strong>内容:</strong> データのハッシュ値、範囲チェック結果など</p>
            <p><strong>重要性:</strong> 改ざんされると証明が無効になる</p>
          </div>

          <div className="file-explanation">
            <h4>verification_key.json（検証鍵）</h4>
            <p><strong>用途:</strong> 購入者がZKP証明を独立して検証するための公開鍵</p>
            <p><strong>公開性:</strong> 誰でも使用可能。第三者による検証を可能にする</p>
          </div>

          <div className="file-explanation">
            <h4>metadata.json（メタデータ）</h4>
            <p><strong>用途:</strong> パッケージ全体の情報</p>
            <p><strong>内容:</strong> 患者数、フィールド名、暗号化パラメータ、Provider ID、データハッシュなど</p>
            <p><strong>用途:</strong> 復号API呼び出し時に必要</p>
          </div>

          <h3>🔒 セキュリティ要件</h3>
          <ul>
            <li>✅ k-匿名性: 最低100件のデータが必要</li>
            <li>✅ データ検証: 各フィールドが有効範囲内</li>
            <li>✅ ゼロ知識証明: データの正当性を数学的に証明</li>
            <li>✅ 準同型暗号: 暗号化されたまま統計計算可能</li>
          </ul>

          <h3>🔍 ZKPで検証している条件（範囲チェック）</h3>
          <p>以下の全ての条件を満たすことを、データの中身を明かさずに証明します：</p>
          <ul>
            <li><strong>年齢:</strong> 0歳 ≤ age ≤ 120歳</li>
            <li><strong>収縮期血圧:</strong> 80 mmHg ≤ blood_pressure_systolic ≤ 200 mmHg</li>
            <li><strong>拡張期血圧:</strong> 50 mmHg ≤ blood_pressure_diastolic ≤ 130 mmHg</li>
            <li><strong>血糖値:</strong> 50 mg/dL ≤ blood_sugar ≤ 300 mg/dL</li>
            <li><strong>コレステロール:</strong> 100 mg/dL ≤ cholesterol ≤ 400 mg/dL</li>
          </ul>

          <h3>🔐 ZKPによるデータ完全性の保証</h3>
          <ul>
            <li><strong>ハッシュ値の計算:</strong> 全フィールドをPoseidonハッシュ関数で集約し、改ざん検出が可能</li>
            <li><strong>数学的証明:</strong> Groth16 zkSNARKにより、上記の範囲チェックが全て通ったことを証明</li>
            <li><strong>第三者検証:</strong> 検証鍵 (verification_key.json) で誰でも証明の正当性を検証可能</li>
            <li><strong>偽造不可能性:</strong> 楕円曲線離散対数問題により、偽の証明を作成することは計算量的に不可能</li>
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
