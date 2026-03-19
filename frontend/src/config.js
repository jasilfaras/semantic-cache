const DEFAULT_API_BASE_URL = 'http://localhost:8000'
const DEFAULT_MAX_QUERY_LENGTH = 2000

function normalizeBaseUrl(value) {
  return value.trim().replace(/\/+$/, '')
}

function normalizePositiveInteger(value, fallback) {
  const parsedValue = Number.parseInt(value, 10)
  return Number.isFinite(parsedValue) && parsedValue > 0 ? parsedValue : fallback
}

export const appConfig = Object.freeze({
  apiBaseUrl: normalizeBaseUrl(
    import.meta.env.VITE_API_BASE_URL ?? DEFAULT_API_BASE_URL,
  ),
  maxQueryLength: normalizePositiveInteger(
    import.meta.env.VITE_MAX_QUERY_LENGTH ?? `${DEFAULT_MAX_QUERY_LENGTH}`,
    DEFAULT_MAX_QUERY_LENGTH,
  ),
})
