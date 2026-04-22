import React, { useState } from 'react'
import { Trophy, ChevronDown, ChevronUp, AlertCircle, CheckCircle, XCircle, MessageSquare, Loader2, Eye, EyeOff } from 'lucide-react'

function QuestionCard({ q }) {
  const [showAnswer, setShowAnswer] = useState(false)

  return (
    <div className="bg-white border border-gray-100 rounded-lg p-3">
      <div className="flex items-start gap-2">
        <span className="text-xs font-bold text-indigo-500 bg-indigo-50 rounded px-1.5 py-0.5 flex-shrink-0">
          Q{q.id}
        </span>
        <div className="flex-1 min-w-0">
          <p className="text-xs font-medium text-gray-800 leading-relaxed">{q.question}</p>
          <div className="flex items-center gap-3 mt-1.5">
            <span className="text-[10px] bg-gray-100 text-gray-500 px-1.5 py-0.5 rounded">
              {q.category}
            </span>
            <span className="text-[10px] text-gray-400">
              考察意图：{q.intent}
            </span>
          </div>
          {q.reference_answer && (
            <div className="mt-2">
              <button
                onClick={(e) => { e.stopPropagation(); setShowAnswer(!showAnswer) }}
                className="flex items-center gap-1 text-[10px] text-amber-600 hover:text-amber-700 transition-colors"
              >
                {showAnswer ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
                {showAnswer ? '收起参考答案' : '查看参考答案'}
              </button>
              {showAnswer && (
                <div className="mt-1.5 bg-amber-50 border border-amber-100 rounded px-2.5 py-1.5">
                  <p className="text-xs text-amber-800 leading-relaxed">{q.reference_answer}</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function ScoreBar({ label, score }) {
  const getColor = (s) => {
    if (s >= 80) return 'bg-emerald-500'
    if (s >= 60) return 'bg-blue-500'
    if (s >= 40) return 'bg-yellow-500'
    return 'bg-red-500'
  }

  return (
    <div className="flex items-center gap-3">
      <span className="text-xs text-gray-500 w-20 flex-shrink-0">{label}</span>
      <div className="flex-1 bg-gray-100 rounded-full h-2">
        <div
          className={`h-2 rounded-full transition-all duration-700 ${getColor(score)}`}
          style={{ width: `${score}%` }}
        />
      </div>
      <span className="text-xs font-semibold text-gray-700 w-8 text-right">{score}</span>
    </div>
  )
}

function getRankBadge(index) {
  if (index === 0) return { bg: 'bg-yellow-100', text: 'text-yellow-700', icon: '🥇' }
  if (index === 1) return { bg: 'bg-gray-100', text: 'text-gray-600', icon: '🥈' }
  if (index === 2) return { bg: 'bg-orange-100', text: 'text-orange-700', icon: '🥉' }
  return { bg: 'bg-gray-50', text: 'text-gray-500', icon: `#${index + 1}` }
}

function ResultCard({ result, index, jd }) {
  const [expanded, setExpanded] = useState(false)
  const [questions, setQuestions] = useState(null)
  const [loadingQuestions, setLoadingQuestions] = useState(false)
  const [questionsError, setQuestionsError] = useState('')
  const badge = getRankBadge(index)

  const handleGenerateQuestions = async (e) => {
    e.stopPropagation()
    if (loadingQuestions || (questions && questions.length > 0)) return
    setLoadingQuestions(true)
    setQuestionsError('')
    setQuestions([])

    try {
      const response = await fetch('/api/interview-questions-stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ resume_text: result.resume_text, jd }),
      })

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}))
        throw new Error(errData.detail || '生成面试问题失败')
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })

        // 按 SSE 事件边界分割
        const parts = buffer.split('\n\n')
        buffer = parts.pop() // 保留未完成的部分

        for (const part of parts) {
          for (const line of part.split('\n')) {
            const trimmed = line.trim()
            if (!trimmed.startsWith('data: ')) continue
            const data = trimmed.slice(6)
            if (data === '[DONE]') continue

            try {
              const parsed = JSON.parse(data)
              if (parsed.error) throw new Error(parsed.error)
              setQuestions((prev) => [...(prev || []), parsed])
            } catch (parseErr) {
              if (parseErr.message && !parseErr.message.includes('JSON'))
                throw parseErr
            }
          }
        }
      }

      // 处理 buffer 中可能残留的最后一条事件
      if (buffer.trim()) {
        for (const line of buffer.split('\n')) {
          const trimmed = line.trim()
          if (!trimmed.startsWith('data: ')) continue
          const data = trimmed.slice(6)
          if (data === '[DONE]') continue
          try {
            const parsed = JSON.parse(data)
            if (parsed.error) throw new Error(parsed.error)
            setQuestions((prev) => [...(prev || []), parsed])
          } catch (_) { /* ignore trailing partial */ }
        }
      }
    } catch (err) {
      setQuestionsError(err.message || '生成面试问题失败')
    } finally {
      setLoadingQuestions(false)
    }
  }

  const getScoreColor = (s) => {
    if (s >= 80) return 'text-emerald-600'
    if (s >= 60) return 'text-blue-600'
    if (s >= 40) return 'text-yellow-600'
    return 'text-red-600'
  }

  if (result.error) {
    return (
      <div className="bg-white rounded-xl border border-red-200 p-5">
        <div className="flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
          <div>
            <p className="text-sm font-medium text-gray-900">{result.candidate_name || result.filename}</p>
            {result.candidate_name && <p className="text-xs text-gray-400">{result.filename}</p>}
            <p className="text-xs text-red-500 mt-0.5">{result.error}</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
      <div
        className="p-5 cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className={`w-10 h-10 rounded-xl flex items-center justify-center text-sm font-bold ${badge.bg} ${badge.text}`}>
              {badge.icon}
            </span>
            <div>
              <p className="text-sm font-medium text-gray-900">{result.candidate_name || result.filename}</p>
              <p className="text-xs text-gray-400">{result.candidate_name ? result.filename : ''}</p>
              <p className="text-xs text-gray-500 mt-0.5 line-clamp-1">{result.summary}</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="text-right">
              <p className={`text-2xl font-bold ${getScoreColor(result.overall_score)}`}>
                {result.overall_score}
              </p>
              <p className="text-xs text-gray-400">综合得分</p>
            </div>
            {expanded ? (
              <ChevronUp className="w-5 h-5 text-gray-400" />
            ) : (
              <ChevronDown className="w-5 h-5 text-gray-400" />
            )}
          </div>
        </div>
      </div>

      {expanded && (
        <div className="px-5 pb-5 border-t border-gray-100 pt-4 space-y-4">
          <div className="space-y-2.5">
            <ScoreBar label="技能匹配" score={result.skill_score} />
            <ScoreBar label="经验匹配" score={result.experience_score} />
            <ScoreBar label="教育背景" score={result.education_score} />
            <ScoreBar label="综合素质" score={result.soft_skill_score} />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2 flex items-center gap-1">
                <CheckCircle className="w-3.5 h-3.5 text-emerald-500" /> 优势
              </h4>
              <ul className="space-y-1">
                {result.strengths.map((s, i) => (
                  <li key={i} className="text-xs text-gray-600 flex items-start gap-1.5">
                    <span className="text-emerald-400 mt-0.5">+</span> {s}
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2 flex items-center gap-1">
                <XCircle className="w-3.5 h-3.5 text-red-400" /> 不足
              </h4>
              <ul className="space-y-1">
                {result.weaknesses.map((w, i) => (
                  <li key={i} className="text-xs text-gray-600 flex items-start gap-1.5">
                    <span className="text-red-400 mt-0.5">-</span> {w}
                  </li>
                ))}
              </ul>
            </div>
          </div>

          <div className="bg-gray-50 rounded-lg p-3">
            <p className="text-xs text-gray-600 leading-relaxed">{result.summary}</p>
          </div>

          {/* 生成面试问题按钮 */}
          <div className="pt-2 border-t border-gray-100">
            <button
              onClick={handleGenerateQuestions}
              disabled={loadingQuestions}
              className={`
                flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-medium transition-all
                ${loadingQuestions
                  ? 'bg-gray-100 text-gray-400 cursor-wait'
                  : questions && questions.length > 0
                    ? 'bg-emerald-50 text-emerald-600 cursor-default'
                    : 'bg-indigo-50 text-indigo-600 hover:bg-indigo-100'
                }
              `}
            >
              {loadingQuestions ? (
                <><Loader2 className="w-3.5 h-3.5 animate-spin" /> 正在生成面试问题{questions && questions.length > 0 ? ` (${questions.length}/10)` : '...'}</>
              ) : questions && questions.length > 0 ? (
                <><MessageSquare className="w-3.5 h-3.5" /> 已生成 {questions.length} 个面试问题</>
              ) : (
                <><MessageSquare className="w-3.5 h-3.5" /> 生成面试问题</>
              )}
            </button>

            {questionsError && (
              <p className="text-xs text-red-500 mt-2">{questionsError}</p>
            )}

            {questions && questions.length > 0 && (
              <div className="mt-3 space-y-2.5">
                {questions.map((q) => (
                  <QuestionCard key={q.id} q={q} />
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default function ResultList({ results, jd }) {
  if (!results || results.length === 0) return null

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 bg-purple-100 rounded-xl flex items-center justify-center">
          <Trophy className="w-5 h-5 text-purple-600" />
        </div>
        <div>
          <h2 className="text-lg font-semibold text-gray-900">匹配结果</h2>
          <p className="text-sm text-gray-500">共 {results.length} 份简历，按匹配度降序排列</p>
        </div>
      </div>

      <div className="space-y-3">
        {results.map((result, index) => (
          <ResultCard key={index} result={result} index={index} jd={jd} />
        ))}
      </div>
    </div>
  )
}
