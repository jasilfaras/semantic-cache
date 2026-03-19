import { useEffect, useEffectEvent, useMemo, useRef, useState } from 'react'
import { MessageRow } from './components/MessageRow'
import { PromptComposer } from './components/PromptComposer'
import { SessionHeader } from './components/SessionHeader'
import { appConfig } from './config'
import {
  TERMINAL_STATES,
  buildStatusPresentation,
  createAssistantMessage,
  createErrorMessage,
  createSystemMessage,
  createUserMessage,
  getHelpMessage,
  getInitialMessages,
} from './lib/messages'
import { askSemanticCache } from './lib/semanticCacheApi'

function App() {
  const [messages, setMessages] = useState(getInitialMessages)
  const [query, setQuery] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [terminalState, setTerminalState] = useState(TERMINAL_STATES.ready)
  const [lastLatencyMs, setLastLatencyMs] = useState(null)
  const chatEndRef = useRef(null)
  const textareaRef = useRef(null)
  const activeRequestRef = useRef(null)

  const appendMessage = (message) => {
    setMessages((currentMessages) => [...currentMessages, message])
  }

  const resetSession = () => {
    setMessages(getInitialMessages())
    setTerminalState(TERMINAL_STATES.ready)
    setLastLatencyMs(null)
  }

  const scrollToBottom = useEffectEvent((behavior = 'smooth') => {
    chatEndRef.current?.scrollIntoView({ behavior, block: 'end' })
  })

  useEffect(() => {
    scrollToBottom(isSubmitting ? 'auto' : 'smooth')
  }, [isSubmitting, messages])

  useEffect(() => {
    const textarea = textareaRef.current

    if (!textarea) {
      return
    }

    textarea.style.height = '0px'
    textarea.style.height = `${Math.min(textarea.scrollHeight, 220)}px`
  }, [query])

  useEffect(() => {
    return () => {
      activeRequestRef.current?.abort()
    }
  }, [])

  const handleQuickFill = (nextQuery) => {
    setQuery(nextQuery)
    textareaRef.current?.focus()
  }

  const handleSubmit = async (event) => {
    event.preventDefault()

    const trimmedQuery = query.trim()

    if (!trimmedQuery || isSubmitting) {
      return
    }

    setQuery('')

    if (trimmedQuery === '/clear') {
      resetSession()
      return
    }

    appendMessage(createUserMessage(trimmedQuery))

    if (trimmedQuery === '/help') {
      appendMessage(createSystemMessage(getHelpMessage(appConfig.apiBaseUrl)))
      return
    }

    const controller = new AbortController()
    activeRequestRef.current = controller
    setIsSubmitting(true)
    setTerminalState(TERMINAL_STATES.searching)

    const startedAt = performance.now()

    try {
      const result = await askSemanticCache(trimmedQuery, {
        signal: controller.signal,
      })
      const latencyMs = Math.round(performance.now() - startedAt)

      appendMessage(
        createAssistantMessage({
          answer: result.answer,
          cacheHit: result.cacheHit,
          latencyMs,
          score: result.score,
        }),
      )

      setLastLatencyMs(latencyMs)
      setTerminalState(
        result.cacheHit ? TERMINAL_STATES.cacheHit : TERMINAL_STATES.generated,
      )
    } catch (error) {
      if (error instanceof DOMException && error.name === 'AbortError') {
        return
      }

      const message =
        error instanceof Error
          ? error.message
          : 'The terminal could not reach the local semantic cache backend.'

      appendMessage(createErrorMessage(message))
      setTerminalState(TERMINAL_STATES.fault)
    } finally {
      if (activeRequestRef.current === controller) {
        activeRequestRef.current = null
      }
      setIsSubmitting(false)
    }
  }

  const handleKeyDown = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      handleSubmit(event)
    }
  }

  const sessionMetrics = useMemo(() => {
    const assistantMessages = messages.filter((message) => message.role === 'assistant')
    const cacheHitMessages = assistantMessages.filter(
      (message) => message.kind === 'CACHE_HIT',
    )

    return {
      averageScore: cacheHitMessages.length
        ? (
            cacheHitMessages.reduce(
              (total, message) =>
                total + (typeof message.score === 'number' ? message.score : 0),
              0,
            ) / cacheHitMessages.length
          ).toFixed(2)
        : '--',
      hitRate: assistantMessages.length
        ? `${Math.round((cacheHitMessages.length / assistantMessages.length) * 100)}%`
        : '--',
      lastQuery:
        [...messages].reverse().find((message) => message.role === 'user')?.content ??
        'awaiting first query',
      queryCount: assistantMessages.length,
    }
  }, [messages])
  const { statusText, statusTone } = buildStatusPresentation(terminalState)

  return (
    <div className="min-h-screen bg-transparent px-3 py-3 text-stone-100 sm:px-5 lg:px-8">
      <main className="terminal-shell mx-auto flex min-h-[calc(100svh-1.5rem)] max-w-[1400px] flex-col overflow-hidden rounded-[28px] border border-white/6 bg-[#1a1a1a]/95 shadow-[0_36px_120px_rgba(0,0,0,0.58)]">
        <SessionHeader
          averageScore={sessionMetrics.averageScore}
          hitRate={sessionMetrics.hitRate}
          lastLatencyMs={lastLatencyMs}
          lastQuery={sessionMetrics.lastQuery}
          queryCount={sessionMetrics.queryCount}
          statusText={statusText}
          statusTone={statusTone}
        />

        <section className="terminal-scroll flex-1 overflow-y-auto px-4 py-6 sm:px-6">
          <div className="mx-auto max-w-5xl space-y-6">
            {messages.map((message) => (
              <MessageRow key={message.id} message={message} />
            ))}

            {isSubmitting ? (
              <div className="space-y-1 text-left">
                <div className="text-xs uppercase tracking-[0.2em] text-stone-500">
                  [SYSTEM]
                </div>
                <p className="whitespace-pre-wrap break-words pl-6 text-[15px] leading-7 text-stone-500">
                  probing the semantic cache and waiting on the local model...
                </p>
              </div>
            ) : null}

            <div ref={chatEndRef} />
          </div>
        </section>

        <footer className="border-t border-white/8 bg-[#151515]/95 px-4 py-4 sm:px-6">
          <div className="mx-auto max-w-5xl">
            <PromptComposer
              disabled={isSubmitting}
              maxLength={appConfig.maxQueryLength}
              onChange={setQuery}
              onKeyDown={handleKeyDown}
              onQuickFill={handleQuickFill}
              onSubmit={handleSubmit}
              statusText={statusText}
              textareaRef={textareaRef}
              value={query}
            />
          </div>
        </footer>
      </main>
    </div>
  )
}

export default App
