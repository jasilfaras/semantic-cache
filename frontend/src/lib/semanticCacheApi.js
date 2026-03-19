import { appConfig } from '../config'

const ASK_ROUTE = '/ask'

function buildApiUrl(path) {
  return new URL(path, `${appConfig.apiBaseUrl}/`).toString()
}

export async function askSemanticCache(query, { signal } = {}) {
  const normalizedQuery = query.trim()

  if (!normalizedQuery) {
    throw new Error('Query must not be blank.')
  }

  const response = await fetch(buildApiUrl(ASK_ROUTE), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ query: normalizedQuery }),
    signal,
  })

  let payload = null

  try {
    payload = await response.json()
  } catch {
    throw new Error('The semantic cache backend returned an unreadable response.')
  }

  if (!response.ok) {
    throw new Error(
      payload?.detail || 'The semantic cache backend rejected the request.',
    )
  }

  if (typeof payload?.answer !== 'string' || !payload.answer.trim()) {
    throw new Error('The semantic cache backend did not return a usable answer.')
  }

  return {
    answer: payload.answer.trim(),
    cacheHit: Boolean(payload.cache_hit ?? payload.is_cached),
    score:
      typeof payload.similarity_score === 'number'
        ? payload.similarity_score
        : typeof payload.score === 'number'
          ? payload.score
          : null,
  }
}
