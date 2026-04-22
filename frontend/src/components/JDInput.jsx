import React from 'react'
import { FileText } from 'lucide-react'

export default function JDInput({ value, onChange }) {
  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
      <div className="flex items-center gap-3 mb-4">
        <div className="w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center">
          <FileText className="w-5 h-5 text-blue-600" />
        </div>
        <div>
          <h2 className="text-lg font-semibold text-gray-900">岗位描述 (JD)</h2>
          <p className="text-sm text-gray-500">输入目标岗位的职位描述</p>
        </div>
      </div>
      <textarea
        className="w-full h-48 p-4 border border-gray-200 rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm leading-relaxed placeholder:text-gray-400"
        placeholder="请粘贴或输入岗位描述（JD），例如：&#10;&#10;岗位名称：高级前端工程师&#10;职责：负责公司核心产品的前端架构设计与开发...&#10;要求：3年以上前端开发经验，精通 React/Vue..."
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
    </div>
  )
}
