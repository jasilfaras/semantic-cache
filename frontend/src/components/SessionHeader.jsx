import { truncate } from '../lib/messages'

export function SessionHeader({
  averageScore,
  hitRate,
  lastLatencyMs,
  lastQuery,
  queryCount,
  statusText,
  statusTone,
}) {
  return (
    <header className="sticky top-0 z-10 border-b border-white/8 bg-[#1a1a1a]/95 backdrop-blur">
      <div className="flex items-center gap-3 border-b border-white/6 px-4 py-3 sm:px-6">
        <span className="h-3 w-3 rounded-full bg-[#ff7d66]" aria-hidden="true" />
        <span className="h-3 w-3 rounded-full bg-[#ffcc58]" aria-hidden="true" />
        <span className="h-3 w-3 rounded-full bg-[#86d15f]" aria-hidden="true" />
        <div className="ml-2 flex min-w-0 flex-1 flex-wrap items-center gap-x-4 gap-y-1 text-[11px] uppercase tracking-[0.28em] text-stone-500">
          <span className="text-[#ff6b4a]">Semantic Cache CLI</span>
          <span>{`queries ${queryCount.toString().padStart(2, '0')}`}</span>
          <span>{`hit rate ${hitRate}`}</span>
          <span>{`avg score ${averageScore}`}</span>
          <span>{`latency ${typeof lastLatencyMs === 'number' ? `${lastLatencyMs}ms` : '--'}`}</span>
        </div>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-3 text-[11px] uppercase tracking-[0.24em] sm:px-6">
        <div className={`min-w-0 ${statusTone}`}>{statusText}</div>
        <div className="min-w-0 text-right text-stone-600">
          <span className="text-stone-500">last query</span>
          <span className="ml-3 text-stone-400">{truncate(lastQuery, 72)}</span>
        </div>
      </div>
    </header>
  )
}
