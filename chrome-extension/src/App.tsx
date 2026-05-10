import React, { useState, useRef, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Brain, Save, Settings, X, CheckCircle2, XCircle, Loader2, BookOpen, ChevronRight } from 'lucide-react'
import { PromptInputBox } from '@/components/ui/ai-prompt-box'

const API_BASE = 'http://127.0.0.1:8000'

// ── Types ──────────────────────────────────────────────────────────────────
interface Source { title: string; url?: string }
interface Message {
  id: string
  role: 'user' | 'assistant'
  text: string
  sources?: Source[]
  latency?: number
  isError?: boolean
}
type StatusType = 'processing' | 'success' | 'error'
interface StatusState { type: StatusType; message: string }

// ── Status Bar ─────────────────────────────────────────────────────────────
const StatusBar: React.FC<{ status: StatusState; onDismiss: () => void }> = ({ status, onDismiss }) => {
  const colors: Record<StatusType, string> = {
    processing: 'bg-amber-500/10 border-amber-500/30 text-amber-300',
    success: 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300',
    error: 'bg-red-500/10 border-red-500/30 text-red-300',
  }
  const Icon = status.type === 'processing' ? Loader2 : status.type === 'success' ? CheckCircle2 : XCircle
  return (
    <motion.div
      initial={{ height: 0, opacity: 0 }}
      animate={{ height: 'auto', opacity: 1 }}
      exit={{ height: 0, opacity: 0 }}
      transition={{ duration: 0.2 }}
      className={`flex items-center gap-2 px-4 py-2 border-b text-xs font-medium ${colors[status.type]}`}
    >
      <Icon className={`w-3.5 h-3.5 flex-shrink-0 ${status.type === 'processing' ? 'animate-spin' : ''}`} />
      <span className="flex-1">{status.message}</span>
      {status.type !== 'processing' && (
        <button onClick={onDismiss} className="opacity-60 hover:opacity-100 transition-opacity">
          <X className="w-3 h-3" />
        </button>
      )}
    </motion.div>
  )
}

// ── Message Bubble ─────────────────────────────────────────────────────────
const MessageBubble: React.FC<{ msg: Message }> = ({ msg }) => {
  const isUser = msg.role === 'user'
  return (
    <motion.div
      initial={{ opacity: 0, y: 10, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.22, ease: 'easeOut' }}
      className={`flex gap-2 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}
    >
      {!isUser && (
        <div className="w-6 h-6 rounded-full bg-blue-600/80 flex items-center justify-center flex-shrink-0 mt-1 ring-1 ring-blue-500/40">
          <Brain className="w-3.5 h-3.5 text-white" />
        </div>
      )}
      <div className={`max-w-[80%] ${isUser ? 'items-end' : 'items-start'} flex flex-col gap-1.5`}>
        <div className={`px-3.5 py-2.5 rounded-2xl text-sm leading-relaxed ${
          isUser
            ? 'bg-blue-600 text-white rounded-br-sm shadow-lg shadow-blue-900/30'
            : msg.isError
            ? 'bg-red-950/60 text-red-300 border border-red-800/50 rounded-bl-sm'
            : 'bg-slate-800/80 text-slate-100 border border-slate-700/50 rounded-bl-sm backdrop-blur-sm'
        }`}>
          {msg.text}
        </div>

        {/* Source pills */}
        {msg.sources && msg.sources.length > 0 && (
          <div className="flex flex-wrap gap-1.5 px-1">
            {[...new Map(msg.sources.map(s => [s.title, s])).values()].map((src, i) => (
              <span key={i} className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-[10px] font-medium">
                <BookOpen className="w-2.5 h-2.5" />
                {src.title.length > 28 ? src.title.slice(0, 28) + '…' : src.title}
              </span>
            ))}
            {msg.latency && (
              <span className="text-[10px] text-slate-500 px-1 flex items-center">
                {(msg.latency / 1000).toFixed(1)}s
              </span>
            )}
          </div>
        )}
      </div>
    </motion.div>
  )
}

// ── Settings Drawer ────────────────────────────────────────────────────────
const SettingsDrawer: React.FC<{ folder: string; onFolderChange: (v: string) => void; onSave: () => void; onClose: () => void }> = ({ folder, onFolderChange, onSave, onClose }) => (
  <motion.div
    initial={{ opacity: 0, y: -8 }}
    animate={{ opacity: 1, y: 0 }}
    exit={{ opacity: 0, y: -8 }}
    transition={{ duration: 0.18 }}
    className="border-b border-slate-700/60 bg-slate-900/80 backdrop-blur-sm px-4 py-3"
  >
    <div className="flex items-center justify-between mb-3">
      <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Settings</span>
      <button onClick={onClose} className="text-slate-500 hover:text-slate-300 transition-colors">
        <X className="w-4 h-4" />
      </button>
    </div>
    <label className="block text-xs text-slate-300 mb-1.5 font-medium">Default Save Folder</label>
    <div className="flex gap-2">
      <div className="flex items-center flex-1 gap-1.5 bg-slate-800 border border-slate-700 rounded-xl px-3 py-2">
        <span className="text-slate-500 text-xs">vault /</span>
        <input
          value={folder}
          onChange={(e) => onFolderChange(e.target.value)}
          placeholder="articles"
          className="flex-1 bg-transparent text-slate-100 text-xs outline-none placeholder-slate-600"
        />
      </div>
      <button onClick={onSave} className="px-3 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-medium transition-colors flex items-center gap-1">
        Save <ChevronRight className="w-3 h-3" />
      </button>
    </div>
    <p className="text-[10px] text-slate-500 mt-1.5">Leave blank to auto-detect (articles, youtube, pdfs…)</p>
  </motion.div>
)

// ── Main App ───────────────────────────────────────────────────────────────
export default function App() {
  const [messages, setMessages] = useState<Message[]>([
    { id: 'welcome', role: 'assistant', text: "Hi! I'm Dhi, your Second Brain. Ask me anything from your knowledge vault, or press Save to capture this page." }
  ])
  const [isLoading, setIsLoading] = useState(false)
  const [status, setStatus] = useState<StatusState | null>(null)
  const [showSettings, setShowSettings] = useState(false)
  const [saveFolder, setSaveFolder] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)
  const statusTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Load saved settings
  useEffect(() => {
    if (typeof chrome !== 'undefined' && chrome.storage?.local) {
      chrome.storage.local.get(['defaultFolder'], (r) => {
        if (r.defaultFolder) setSaveFolder(r.defaultFolder)
      })
    }
  }, [])

  // Auto scroll
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  const showStatusFor = useCallback((s: StatusState, ms = 4000) => {
    setStatus(s)
    if (statusTimerRef.current) clearTimeout(statusTimerRef.current)
    if (s.type !== 'processing') {
      statusTimerRef.current = setTimeout(() => setStatus(null), ms)
    }
  }, [])

  // ── Save current page ──
  const handleSavePage = useCallback(async () => {
    showStatusFor({ type: 'processing', message: '⏳ Capturing current page…' })
    try {
      const tabs = await new Promise<chrome.tabs.Tab[]>((res) =>
        chrome.tabs.query({ active: true, lastFocusedWindow: true }, res)
      )
      const url = tabs[0]?.url
      if (!url || !url.startsWith('http')) {
        showStatusFor({ type: 'error', message: 'Only http/https pages can be saved.' })
        return
      }
      const folder = saveFolder.trim().replace(/^\/|\/$/g, '') || undefined
      const body: Record<string, unknown> = { url, tags: ['extension-capture'] }
      if (folder) body.folder = folder

      const res = await fetch(`${API_BASE}/api/ingest`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      const data = await res.json()
      if (data.status === 'success') {
        showStatusFor({ type: 'success', message: '✓ Page saved! Indexing in background…' })
        addMessage('assistant', `✓ Page captured and sent to your Second Brain${folder ? ` → vault/${folder}` : ''}. Indexing may take ~30s.`)
      } else {
        showStatusFor({ type: 'error', message: data.detail || 'Backend error' })
      }
    } catch (e) {
      showStatusFor({ type: 'error', message: 'Cannot reach backend — is Docker running?' })
    }
  }, [saveFolder, showStatusFor])

  // ── Chat send ──
  const handleSend = useCallback(async (message: string, _files?: File[]) => {
    if (!message.trim()) return
    const userMsg: Message = { id: Date.now().toString(), role: 'user', text: message }
    setMessages((prev) => [...prev, userMsg])
    setIsLoading(true)
    showStatusFor({ type: 'processing', message: '⏳ Searching your Second Brain…' })

    try {
      const res = await fetch(`${API_BASE}/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: message, top_k: 5 }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || `HTTP ${res.status}`)
      }
      const data = await res.json()
      setMessages((prev) => [...prev, {
        id: Date.now().toString() + '_ai',
        role: 'assistant',
        text: data.answer,
        sources: data.sources,
        latency: data.latency_ms,
      }])
      setStatus(null)
    } catch (e: unknown) {
      const msg = e instanceof Error && e.message.includes('fetch') ? 'Cannot reach backend — is Docker running on port 8000?' : (e instanceof Error ? e.message : 'Unknown error')
      setMessages((prev) => [...prev, { id: Date.now().toString() + '_err', role: 'assistant', text: `Error: ${msg}`, isError: true }])
      showStatusFor({ type: 'error', message: msg })
    } finally {
      setIsLoading(false)
    }
  }, [showStatusFor])

  const addMessage = (role: 'user' | 'assistant', text: string) => {
    setMessages((prev) => [...prev, { id: Date.now().toString(), role, text }])
  }

  const handleSaveSettings = () => {
    const folder = saveFolder.trim().replace(/^\/|\/$/g, '')
    if (typeof chrome !== 'undefined' && chrome.storage?.local) {
      chrome.storage.local.set({ defaultFolder: folder }, () => {
        showStatusFor({ type: 'success', message: '✓ Settings saved' }, 2000)
        setShowSettings(false)
      })
    } else {
      setShowSettings(false)
    }
  }

  return (
    <div className="flex flex-col h-screen bg-[#0D1117] overflow-hidden">
      {/* ── Header ── */}
      <header className="flex items-center justify-between px-4 py-3 bg-slate-900/80 backdrop-blur-sm border-b border-slate-700/60 flex-shrink-0">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-xl bg-gradient-to-br from-blue-500 to-violet-600 flex items-center justify-center shadow-lg shadow-blue-900/40 ring-1 ring-white/10">
            <Brain className="w-4 h-4 text-white" />
          </div>
          <div>
            <h1 className="text-sm font-semibold text-white leading-none">Dhi Brain</h1>
            <p className="text-[10px] text-slate-500 leading-none mt-0.5">Second Brain AI</p>
          </div>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={handleSavePage}
            disabled={isLoading}
            title="Save current page to Second Brain"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-blue-600/20 hover:bg-blue-600/40 border border-blue-500/30 text-blue-400 hover:text-blue-300 text-xs font-medium transition-all disabled:opacity-40"
          >
            <Save className="w-3.5 h-3.5" />
            Save
          </button>
          <button
            onClick={() => setShowSettings((p) => !p)}
            title="Settings"
            className={`p-2 rounded-xl transition-all ${showSettings ? 'bg-slate-700 text-white' : 'text-slate-500 hover:text-slate-300 hover:bg-slate-800'}`}
          >
            <Settings className="w-4 h-4" />
          </button>
        </div>
      </header>

      {/* ── Settings Drawer ── */}
      <AnimatePresence>
        {showSettings && (
          <SettingsDrawer folder={saveFolder} onFolderChange={setSaveFolder} onSave={handleSaveSettings} onClose={() => setShowSettings(false)} />
        )}
      </AnimatePresence>

      {/* ── Status Bar ── */}
      <AnimatePresence>
        {status && <StatusBar status={status} onDismiss={() => setStatus(null)} />}
      </AnimatePresence>

      {/* ── Messages ── */}
      <main className="flex-1 overflow-y-auto chat-scroll px-4 py-4 flex flex-col gap-4">
        <AnimatePresence initial={false}>
          {messages.map((msg) => <MessageBubble key={msg.id} msg={msg} />)}
        </AnimatePresence>

        {/* Loading dots */}
        <AnimatePresence>
          {isLoading && (
            <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="flex gap-2">
              <div className="w-6 h-6 rounded-full bg-blue-600/80 flex items-center justify-center flex-shrink-0 mt-1 ring-1 ring-blue-500/40">
                <Brain className="w-3.5 h-3.5 text-white" />
              </div>
              <div className="px-4 py-3 rounded-2xl rounded-bl-sm bg-slate-800/80 border border-slate-700/50 flex items-center gap-1.5">
                {[0, 1, 2].map((i) => (
                  <motion.div key={i} className="w-1.5 h-1.5 rounded-full bg-blue-400"
                    animate={{ scale: [1, 1.4, 1], opacity: [0.5, 1, 0.5] }}
                    transition={{ duration: 1, repeat: Infinity, delay: i * 0.2 }} />
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
        <div ref={bottomRef} />
      </main>

      {/* ── Prompt Input ── */}
      <div className="flex-shrink-0 px-3 pb-3 pt-2 bg-slate-900/50 backdrop-blur-sm border-t border-slate-700/40">
        <PromptInputBox
          onSend={handleSend}
          isLoading={isLoading}
          placeholder="Ask your Second Brain…"
          className="border-slate-700/60 bg-slate-900/90"
        />
      </div>
    </div>
  )
}
