import React, { useState, useRef, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { MeshGradient } from '@paper-design/shaders-react'
import {
  Brain, Save, Settings, X, CheckCircle2, XCircle,
  Loader2, BookOpen, ChevronRight
} from 'lucide-react'
import { PromptInputBox } from '@/components/ui/ai-prompt-box'

const API_BASE = 'http://127.0.0.1:8000'

// ── Shared glass style (same as prompt box from glass-calendar) ────────────
const GLASS = 'rounded-3xl border border-white/10 bg-black/20 backdrop-blur-xl shadow-2xl'

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
  const textColor: Record<StatusType, string> = {
    processing: 'text-white/50',
    success: 'text-white/70',
    error: 'text-white/40',
  }
  const Icon = status.type === 'processing' ? Loader2 : status.type === 'success' ? CheckCircle2 : XCircle
  return (
    <motion.div
      initial={{ height: 0, opacity: 0 }}
      animate={{ height: 'auto', opacity: 1 }}
      exit={{ height: 0, opacity: 0 }}
      transition={{ duration: 0.15 }}
      className={`flex items-center gap-2 px-4 py-1.5 border-b border-white/5 ${textColor[status.type]}`}
    >
      <Icon className={`w-3 h-3 flex-shrink-0 ${status.type === 'processing' ? 'animate-spin' : ''}`} />
      <span className="flex-1 text-[10px] font-light tracking-wide">{status.message}</span>
      {status.type !== 'processing' && (
        <button onClick={onDismiss} className="opacity-30 hover:opacity-70 transition-opacity">
          <X className="w-2.5 h-2.5" />
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
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2, ease: 'easeOut' }}
      className={`flex gap-2.5 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}
    >
      {!isUser && (
        <div className="w-5 h-5 rounded-full bg-black/20 border border-white/10 flex items-center justify-center flex-shrink-0 mt-0.5 backdrop-blur-xl">
          <Brain className="w-2.5 h-2.5 text-white/40" />
        </div>
      )}
      <div className={`max-w-[82%] flex flex-col gap-1.5 ${isUser ? 'items-end' : 'items-start'}`}>
        <div className={`px-3 py-2 rounded-2xl text-[11px] font-light leading-relaxed tracking-wide ${
          isUser
            ? 'bg-white text-black rounded-br-sm'
            : msg.isError
            ? 'bg-black/20 backdrop-blur-xl border border-white/10 text-white/30 rounded-bl-sm italic'
            : 'bg-black/20 backdrop-blur-xl border border-white/10 text-white/80 rounded-bl-sm'
        }`}>
          {msg.text}
        </div>

        {msg.sources && msg.sources.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {[...new Map(msg.sources.map(s => [s.title, s])).values()].map((src, i) => (
              <span key={i} className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full border border-white/10 bg-black/20 backdrop-blur-sm text-white/30 text-[9px] font-light tracking-wide">
                <BookOpen className="w-2 h-2" />
                {src.title.length > 26 ? src.title.slice(0, 26) + '…' : src.title}
              </span>
            ))}
            {msg.latency && (
              <span className="text-[9px] text-white/20 font-light flex items-center px-1">
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
const SettingsDrawer: React.FC<{
  folder: string; onFolderChange: (v: string) => void; onSave: () => void; onClose: () => void
}> = ({ folder, onFolderChange, onSave, onClose }) => (
  <motion.div
    initial={{ opacity: 0, y: -6 }}
    animate={{ opacity: 1, y: 0 }}
    exit={{ opacity: 0, y: -6 }}
    transition={{ duration: 0.15 }}
    className="border-b border-white/5 bg-black/30 backdrop-blur-md px-4 py-3"
  >
    <div className="flex items-center justify-between mb-3">
      <span className="text-[9px] font-light text-white/30 uppercase tracking-[0.15em]">Settings</span>
      <button onClick={onClose} className="text-white/20 hover:text-white/50 transition-colors">
        <X className="w-3 h-3" />
      </button>
    </div>
    <label className="block text-[10px] text-white/40 mb-1.5 font-light tracking-wide">Default Save Folder</label>
    <div className="flex gap-2">
      <div className="flex items-center flex-1 gap-1.5 bg-black/20 border border-white/10 rounded-xl px-3 py-2">
        <span className="text-white/20 text-[10px] font-light">vault /</span>
        <input
          value={folder}
          onChange={(e) => onFolderChange(e.target.value)}
          placeholder="articles"
          className="flex-1 bg-transparent text-white/70 text-[10px] font-light outline-none placeholder-white/15 tracking-wide"
        />
      </div>
      <button
        onClick={onSave}
        className="px-3 py-2 rounded-xl bg-black/20 hover:bg-black/40 border border-white/10 text-white/60 text-[10px] font-light transition-all flex items-center gap-1"
      >
        Save <ChevronRight className="w-2.5 h-2.5" />
      </button>
    </div>
    <p className="text-[9px] text-white/20 mt-1.5 font-light">Leave blank to auto-detect</p>
  </motion.div>
)

// ── Main App ───────────────────────────────────────────────────────────────
export default function App() {
  const [messages, setMessages] = useState<Message[]>([
    { id: 'welcome', role: 'assistant', text: "Ask me anything from your knowledge vault." }
  ])
  const [isLoading, setIsLoading] = useState(false)
  const [status, setStatus] = useState<StatusState | null>(null)
  const [showSettings, setShowSettings] = useState(false)
  const [saveFolder, setSaveFolder] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)
  const statusTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    if (typeof chrome !== 'undefined' && chrome.storage?.local) {
      chrome.storage.local.get(['defaultFolder'], (r) => {
        if (r.defaultFolder) setSaveFolder(r.defaultFolder)
      })
    }
  }, [])

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

  const handleSavePage = useCallback(async () => {
    showStatusFor({ type: 'processing', message: 'Capturing page…' })
    try {
      const tabs = await new Promise<chrome.tabs.Tab[]>((res) =>
        chrome.tabs.query({ active: true, lastFocusedWindow: true }, res)
      )
      const url = tabs[0]?.url
      if (!url || !url.startsWith('http')) {
        showStatusFor({ type: 'error', message: 'Only http/https pages can be saved.' }); return
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
        showStatusFor({ type: 'success', message: `Saved${folder ? ` → vault/${folder}` : ''}. Indexing…` })
        addMessage('assistant', `Page captured. Indexing may take ~30s.`)
      } else {
        showStatusFor({ type: 'error', message: data.detail || 'Backend error' })
      }
    } catch {
      showStatusFor({ type: 'error', message: 'Cannot reach backend — is Docker running?' })
    }
  }, [saveFolder, showStatusFor])

  const handleSend = useCallback(async (message: string) => {
    if (!message.trim()) return
    setMessages((p) => [...p, { id: Date.now().toString(), role: 'user', text: message }])
    setIsLoading(true)
    showStatusFor({ type: 'processing', message: 'Searching your Second Brain…' })
    try {
      const res = await fetch(`${API_BASE}/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: message, top_k: 5 }),
      })
      if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.detail || `HTTP ${res.status}`) }
      const data = await res.json()
      setMessages((p) => [...p, {
        id: Date.now() + '_ai',
        role: 'assistant',
        text: data.answer,
        sources: data.sources,
        latency: data.latency_ms,
      }])
      setStatus(null)
    } catch (e: unknown) {
      const msg = e instanceof Error && e.message.includes('fetch')
        ? 'Cannot reach backend — is Docker running?'
        : (e instanceof Error ? e.message : 'Unknown error')
      setMessages((p) => [...p, { id: Date.now() + '_err', role: 'assistant', text: msg, isError: true }])
      showStatusFor({ type: 'error', message: msg })
    } finally {
      setIsLoading(false)
    }
  }, [showStatusFor])

  const addMessage = (role: 'user' | 'assistant', text: string) =>
    setMessages((p) => [...p, { id: Date.now().toString(), role, text }])

  const handleSaveSettings = () => {
    const folder = saveFolder.trim().replace(/^\/|\/$/g, '')
    if (typeof chrome !== 'undefined' && chrome.storage?.local) {
      chrome.storage.local.set({ defaultFolder: folder }, () => {
        showStatusFor({ type: 'success', message: 'Settings saved' }, 2000)
        setShowSettings(false)
      })
    } else { setShowSettings(false) }
  }

  return (
    <div className="flex flex-col h-screen overflow-hidden bg-black p-2.5 gap-2.5">

      {/* ── Floating Navbar pill (same glass as prompt box) ── */}
      <motion.header
        initial={{ opacity: 0, y: -8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className={`${GLASS} flex items-center justify-between px-4 py-2.5 flex-shrink-0`}
      >
        <div className="flex items-center gap-2.5">
          <div className="w-6 h-6 rounded-xl bg-black/30 border border-white/10 flex items-center justify-center">
            <Brain className="w-3 h-3 text-white/50" />
          </div>
          <div>
            <h1 className="text-[11px] font-light text-white/80 leading-none tracking-[0.08em] uppercase">Dhi Brain</h1>
            <p className="text-[9px] text-white/20 leading-none mt-0.5 font-light tracking-widest">second brain ai</p>
          </div>
        </div>

        <div className="flex items-center gap-1.5">
          <button
            onClick={handleSavePage}
            disabled={isLoading}
            title="Save current page"
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl border border-white/10 bg-black/20 hover:bg-black/40 text-white/40 hover:text-white/70 text-[10px] font-light tracking-wide transition-all disabled:opacity-30"
          >
            <Save className="w-3 h-3" />
            Save
          </button>
          <button
            onClick={() => setShowSettings((p) => !p)}
            className={`p-1.5 rounded-xl border transition-all ${
              showSettings
                ? 'bg-black/40 border-white/20 text-white/70'
                : 'border-transparent text-white/20 hover:text-white/50 hover:border-white/10'
            }`}
          >
            <Settings className="w-3.5 h-3.5" />
          </button>
        </div>
      </motion.header>

      {/* ── Main content card — chat + prompt share MeshGradient bg ── */}
      <motion.div
        initial={{ opacity: 0, scale: 0.99 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.35, delay: 0.05 }}
        className={`${GLASS} flex-1 relative overflow-hidden flex flex-col min-h-0`}
      >
        {/* Animated MeshGradient wallpaper — shared by messages + prompt */}
        <MeshGradient
          style={{ position: 'absolute', inset: 0, width: '100%', height: '100%' }}
          colors={['#000000', '#111111', '#1c1c1c', '#2a2a2a']}
          speed={0.4}
          distortion={0.6}
          swirl={0.08}
        />

        {/* Subtle vignette over the gradient */}
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-1/4 left-1/3 w-32 h-32 bg-white/[0.015] rounded-full blur-3xl animate-pulse" style={{ animationDuration: '6s' }} />
          <div className="absolute bottom-1/3 right-1/4 w-24 h-24 bg-white/[0.01] rounded-full blur-2xl animate-pulse" style={{ animationDuration: '4s', animationDelay: '1s' }} />
        </div>

        {/* ── Content layer over gradient ── */}
        <div className="absolute inset-0 flex flex-col min-h-0">

          {/* Settings Drawer */}
          <AnimatePresence>
            {showSettings && (
              <SettingsDrawer folder={saveFolder} onFolderChange={setSaveFolder} onSave={handleSaveSettings} onClose={() => setShowSettings(false)} />
            )}
          </AnimatePresence>

          {/* Status Bar */}
          <AnimatePresence>
            {status && <StatusBar status={status} onDismiss={() => setStatus(null)} />}
          </AnimatePresence>

          {/* Messages */}
          <main className="flex-1 overflow-y-auto chat-scroll px-4 py-5 flex flex-col gap-4 min-h-0">
            <AnimatePresence initial={false}>
              {messages.map((msg) => <MessageBubble key={msg.id} msg={msg} />)}
            </AnimatePresence>

            {/* Loading dots */}
            <AnimatePresence>
              {isLoading && (
                <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="flex gap-2.5">
                  <div className="w-5 h-5 rounded-full bg-black/20 border border-white/10 backdrop-blur-xl flex items-center justify-center flex-shrink-0 mt-0.5">
                    <Brain className="w-2.5 h-2.5 text-white/30" />
                  </div>
                  <div className="px-3 py-2 rounded-2xl rounded-bl-sm bg-black/20 backdrop-blur-xl border border-white/10 flex items-center gap-1.5">
                    {[0, 1, 2].map((i) => (
                      <motion.div key={i} className="w-1 h-1 rounded-full bg-white/30"
                        animate={{ opacity: [0.2, 0.8, 0.2] }}
                        transition={{ duration: 1.2, repeat: Infinity, delay: i * 0.2 }} />
                    ))}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
            <div ref={bottomRef} />
          </main>

          {/* Thin separator */}
          <div className="h-px mx-4 bg-white/5 flex-shrink-0" />

          {/* Prompt Box — glass floats on same gradient background */}
          <div className="flex-shrink-0 p-3">
            <PromptInputBox
              onSend={handleSend}
              isLoading={isLoading}
              placeholder="Ask your Second Brain…"
            />
          </div>
        </div>
      </motion.div>
    </div>
  )
}
