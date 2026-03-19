export const TERMINAL_STATES = Object.freeze({
  ready: 'LOCAL_READY',
  searching: 'SEARCHING_VECTOR_SPACE',
  cacheHit: 'CACHE_SHORTCUT',
  generated: 'LLM_STREAMING',
  fault: 'FAULT',
})

const INITIAL_SYSTEM_COPY =
  'semantic cache online. embeddings: nomic-embed-text. generation: llama3. use /help for commands.'

export function createSystemMessage(content) {
  return {
    id: crypto.randomUUID(),
    role: 'system',
    kind: 'SYSTEM',
    content,
    createdAt: Date.now(),
  }
}

export function createUserMessage(content) {
  return {
    id: crypto.randomUUID(),
    role: 'user',
    kind: 'USER',
    content,
    createdAt: Date.now(),
  }
}

export function createAssistantMessage({ answer, cacheHit, latencyMs, score }) {
  return {
    id: crypto.randomUUID(),
    role: 'assistant',
    kind: cacheHit ? 'CACHE_HIT' : 'LLM_GEN',
    content: answer,
    createdAt: Date.now(),
    latencyMs,
    score,
  }
}

export function createErrorMessage(content) {
  return {
    id: crypto.randomUUID(),
    role: 'error',
    kind: 'ERROR',
    content,
    createdAt: Date.now(),
  }
}

export function getInitialMessages() {
  return [createSystemMessage(INITIAL_SYSTEM_COPY)]
}

export function getHelpMessage(apiBaseUrl) {
  return `local commands:\n/help show command hints\n/clear reset chat history\nall other input is posted to ${apiBaseUrl}/ask`
}

export function truncate(value, maxLength = 56) {
  if (!value) {
    return ''
  }

  return value.length <= maxLength ? value : `${value.slice(0, maxLength - 1)}…`
}

export function buildStatusPresentation(terminalState) {
  switch (terminalState) {
    case TERMINAL_STATES.searching:
      return {
        statusText: 'embedding query + searching vector index',
        statusTone: 'text-stone-400',
      }
    case TERMINAL_STATES.cacheHit:
      return {
        statusText: 'cache hit returned instantly',
        statusTone: 'text-[#ff6b4a]',
      }
    case TERMINAL_STATES.generated:
      return {
        statusText: 'cache miss. local model generated a new answer',
        statusTone: 'text-stone-400',
      }
    case TERMINAL_STATES.fault:
      return {
        statusText: 'fault detected. inspect local services',
        statusTone: 'text-red-300',
      }
    default:
      return {
        statusText: 'local stack ready',
        statusTone: 'text-stone-400',
      }
  }
}
