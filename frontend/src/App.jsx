import React, { useState } from 'react'
import axios from 'axios'
import { Sparkles, Loader2 } from 'lucide-react'
import JDInput from './components/JDInput'
import ResumeUpload from './components/ResumeUpload'
import ResultList from './components/ResultList'

export default function App() {
  const [jd, setJd] = useState('')
  const [files, setFiles] = useState([])
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [uploadProgress, setUploadProgress] = useState(0)
  const [uploadPhase, setUploadPhase] = useState('')

  const canSubmit = jd.trim().length > 0 && files.length > 0 && !loading

  const handleSubmit = async () => {
    if (!canSubmit) return

    setLoading(true)
    setError('')
    setResults(null)
    setUploadProgress(0)
    setUploadPhase('uploading')

    const formData = new FormData()
    formData.append('jd', jd)
    files.forEach((file) => {
      formData.append('files', file)
    })

    try {
      // 上传阶段：并行执行真实上传 + 进度动画
      let uploadDone = false
      const responsePromise = axios.post('/api/match', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 300000,
        onUploadProgress: (e) => {
          const total = e.total || e.estimated || 0
          if (total) {
            const pct = Math.round((e.loaded / total) * 100)
            if (pct >= 100) uploadDone = true
            setUploadProgress(Math.min(pct, 99))
          }
        },
      })

      // 平滑进度动画：确保上传阶段至少显示 800ms
      await new Promise((resolve) => {
        let progress = 0
        const interval = setInterval(() => {
          if (uploadDone && progress >= 80) {
            progress = 100
          } else if (uploadDone) {
            progress = Math.min(progress + 15, 99)
          } else {
            progress = Math.min(progress + 8, 90)
          }
          setUploadProgress(progress)
          if (progress >= 100) {
            clearInterval(interval)
            resolve()
          }
        }, 100)
      })

      // 切换到 AI 评估阶段
      setUploadPhase('processing')

      const response = await responsePromise
      setResults(response.data.results)
    } catch (err) {
      if (err.response) {
        setError(err.response.data.detail || '服务器错误，请稍后重试')
      } else if (err.code === 'ECONNABORTED') {
        setError('请求超时，请检查 LLM 服务是否正常运行')
      } else {
        setError('网络错误，请检查后端服务是否启动')
      }
    } finally {
      setLoading(false)
      setUploadPhase('')
      setUploadProgress(0)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50/30 to-purple-50/20">
      {/* Header */}
      <header className="border-b border-gray-200/80 bg-white/70 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center gap-3">
          <div className="w-9 h-9 bg-gradient-to-br from-blue-600 to-purple-600 rounded-xl flex items-center justify-center">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-gray-900">Resume Matcher</h1>
            <p className="text-xs text-gray-500">AI 驱动的简历匹配评估系统</p>
          </div>
        </div>
      </header>

      {/* Main */}
      <main className="max-w-5xl mx-auto px-6 py-8 space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <JDInput value={jd} onChange={setJd} />
          <ResumeUpload files={files} onFilesChange={setFiles} />
        </div>

        {/* Submit Button */}
        <div className="flex justify-center">
          <button
            onClick={handleSubmit}
            disabled={!canSubmit}
            className={`
              px-8 py-3 rounded-xl font-medium text-sm transition-all
              flex items-center gap-2
              ${canSubmit
                ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg shadow-blue-500/25 hover:shadow-xl hover:shadow-blue-500/30 hover:-translate-y-0.5'
                : 'bg-gray-200 text-gray-400 cursor-not-allowed'
              }
            `}
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                AI 评估中，请耐心等待...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                开始匹配评估
              </>
            )}
          </button>
        </div>

        {/* Progress Bar */}
        {loading && uploadPhase && (
          <div className="max-w-md mx-auto w-full space-y-2">
            <div className="flex items-center justify-between text-xs text-gray-500">
              <span>
                {uploadPhase === 'uploading' ? '📤 上传文件中...' : '🤖 AI 评估中，请耐心等待...'}
              </span>
              <span>
                {uploadPhase === 'uploading' ? `${uploadProgress}%` : ''}
              </span>
            </div>
            <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
              {uploadPhase === 'uploading' ? (
                <div
                  className="h-full bg-gradient-to-r from-blue-500 to-purple-500 rounded-full transition-all duration-300 ease-out"
                  style={{ width: `${uploadProgress}%` }}
                />
              ) : (
                <div className="h-full bg-gradient-to-r from-blue-500 to-purple-500 rounded-full animate-progress-indeterminate" />
              )}
            </div>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-sm text-red-600 text-center">
            {error}
          </div>
        )}

        {/* Results */}
        {results && <ResultList results={results} jd={jd} />}
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-200/60 mt-12">
        <div className="max-w-5xl mx-auto px-6 py-4 text-center text-xs text-gray-400">
          Powered by Qwen 3.6 35B &middot; Resume Matcher v1.0
        </div>
      </footer>
    </div>
  )
}
