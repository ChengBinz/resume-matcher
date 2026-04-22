import React, { useRef } from 'react'
import { Upload, X, FileUp, Archive } from 'lucide-react'

const ACCEPTED_EXTENSIONS = ['.pdf', '.zip', '.tar', '.tar.gz', '.tgz', '.tar.bz2', '.tbz2']

function isAcceptedFile(name) {
  const lower = name.toLowerCase()
  return ACCEPTED_EXTENSIONS.some((ext) => lower.endsWith(ext))
}

function isArchiveFile(name) {
  const lower = name.toLowerCase()
  return ['.zip', '.tar', '.tar.gz', '.tgz', '.tar.bz2', '.tbz2'].some((ext) => lower.endsWith(ext))
}

export default function ResumeUpload({ files, onFilesChange }) {
  const fileInputRef = useRef(null)

  const dedup = (existing, incoming) => {
    const keys = new Set(existing.map((f) => `${f.name}_${f.size}`))
    return [...existing, ...incoming.filter((f) => !keys.has(`${f.name}_${f.size}`))]
  }

  const handleDrop = (e) => {
    e.preventDefault()
    const droppedFiles = Array.from(e.dataTransfer.files).filter((f) =>
      isAcceptedFile(f.name)
    )
    onFilesChange(dedup(files, droppedFiles))
  }

  const handleDragOver = (e) => {
    e.preventDefault()
  }

  const handleFileSelect = (e) => {
    const selected = Array.from(e.target.files).filter((f) => isAcceptedFile(f.name))
    onFilesChange(dedup(files, selected))
    e.target.value = ''
  }

  const removeFile = (index) => {
    onFilesChange(files.filter((_, i) => i !== index))
  }

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
      <div className="flex items-center gap-3 mb-4">
        <div className="w-10 h-10 bg-emerald-100 rounded-xl flex items-center justify-center">
          <Upload className="w-5 h-5 text-emerald-600" />
        </div>
        <div>
          <h2 className="text-lg font-semibold text-gray-900">上传简历</h2>
          <p className="text-sm text-gray-500">支持 PDF 和压缩包（zip/tar.gz）</p>
        </div>
      </div>

      <div
        className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center hover:border-blue-400 hover:bg-blue-50/50 transition-all cursor-pointer"
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onClick={() => fileInputRef.current?.click()}
      >
        <FileUp className="w-10 h-10 text-gray-400 mx-auto mb-3" />
        <p className="text-sm text-gray-600 mb-1">
          拖拽文件到此处，或 <span className="text-blue-600 font-medium">点击上传</span>
        </p>
        <p className="text-xs text-gray-400">支持 PDF 和压缩包（zip/tar.gz），压缩包内自动提取 PDF</p>
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".pdf,.zip,.tar,.tar.gz,.tgz,.tar.bz2,.tbz2"
          className="hidden"
          onChange={handleFileSelect}
        />
      </div>

      {files.length > 0 && (
        <div className="mt-4 space-y-2">
          {files.map((file, idx) => (
            <div
              key={idx}
              className="flex items-center justify-between bg-gray-50 px-4 py-2.5 rounded-lg"
            >
              <div className="flex items-center gap-2 min-w-0">
                {isArchiveFile(file.name)
                  ? <Archive className="w-4 h-4 text-amber-500 flex-shrink-0" />
                  : <FileUp className="w-4 h-4 text-gray-400 flex-shrink-0" />
                }
                <span className="text-sm text-gray-700 truncate">{file.name}</span>
                <span className="text-xs text-gray-400 flex-shrink-0">
                  {(file.size / 1024).toFixed(0)} KB
                </span>
              </div>
              <button
                onClick={() => removeFile(idx)}
                className="text-gray-400 hover:text-red-500 transition-colors ml-2"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
