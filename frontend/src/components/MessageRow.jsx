const CLOCK_FORMATTER = new Intl.DateTimeFormat('en-US', {
  hour: '2-digit',
  minute: '2-digit',
  hour12: false,
})

const BADGE_COPY = {
  SYSTEM: {
    icon: '◇',
    label: '[LOCAL_READY]',
    className: 'border-white/10 bg-white/5 text-[#d2c8c0]',
  },
  CACHE_HIT: {
    icon: '⚡',
    label: '[CACHE_HIT]',
    className: 'border-[#ff6b4a]/35 bg-[#ff6b4a]/10 text-[#ffb8a8]',
  },
  LLM_GEN: {
    icon: '🐌',
    label: '[LLM_GEN]',
    className: 'border-[#ff6b4a]/20 bg-[#ff6b4a]/10 text-[#f4d4cb]',
  },
  ERROR: {
    icon: '!!',
    label: '[ERROR]',
    className: 'border-[#ff6b4a]/35 bg-[#ff6b4a]/12 text-[#ffd2c7]',
  },
}

function StatusBadge({ kind, score }) {
  const badge = BADGE_COPY[kind] ?? BADGE_COPY.SYSTEM
  const scoreLabel =
    kind === 'CACHE_HIT' && typeof score === 'number' ? ` ${score.toFixed(2)}` : ''

  return (
    <span
      className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-[10px] tracking-[0.28em] ${badge.className}`}
    >
      <span aria-hidden="true">{badge.icon}</span>
      <span>{`${badge.label}${scoreLabel}`}</span>
    </span>
  )
}

function getMessagePresentation(message) {
  if (message.role === 'user') {
    return {
      marker: '>',
      markerTone: 'border-[#ff6b4a]/45 bg-[#ff6b4a]/10 text-[#ff6b4a]',
      roleLabel: 'USER_CMD',
      wrapperTone: 'border-[#ff6b4a]/35 bg-[#221b19]/85',
    }
  }

  if (message.role === 'error') {
    return {
      marker: '!',
      markerTone: 'border-[#ff6b4a]/35 bg-[#ff6b4a]/10 text-[#ffd2c7]',
      roleLabel: 'FAULT',
      wrapperTone: 'border-[#ff6b4a]/35 bg-[#241918]/85',
    }
  }

  if (message.role === 'assistant') {
    return {
      marker: '█',
      markerTone: 'border-white/10 bg-white/5 text-[#e7d9cf]',
      roleLabel: 'CACHE_NODE',
      wrapperTone: 'border-white/8 bg-[#111110]/78',
    }
  }

  return {
    marker: '░',
    markerTone: 'border-white/10 bg-white/5 text-[#e7d9cf]',
    roleLabel: 'SYSTEM',
    wrapperTone: 'border-white/8 bg-[#111110]/78',
  }
}

export function MessageRow({ message }) {
  const isUser = message.role === 'user'
  const { marker, markerTone, roleLabel, wrapperTone } = getMessagePresentation(
    message,
  )
  const displayText = message.visibleContent ?? message.content

  return (
    <article
      className={`rounded-[22px] border border-dashed px-4 py-4 text-left shadow-[inset_0_0_0_1px_rgba(255,255,255,0.02)] transition-colors sm:px-5 ${wrapperTone}`}
    >
      <div className="flex flex-wrap items-center gap-3 text-[10px] uppercase tracking-[0.32em] text-[#9f958d] sm:text-[11px]">
        <span
          className={`inline-flex h-8 w-8 items-center justify-center rounded-md border border-dashed text-sm ${markerTone}`}
          aria-hidden="true"
        >
          {marker}
        </span>
        <span>{roleLabel}</span>
        <span className="text-[#847b75]">{CLOCK_FORMATTER.format(message.createdAt)}</span>
        {!isUser ? <StatusBadge kind={message.kind} score={message.score} /> : null}
        {typeof message.latencyMs === 'number' ? (
          <span className="text-[#7d756f]">{`${message.latencyMs}ms`}</span>
        ) : null}
      </div>

      <p className="mt-4 whitespace-pre-wrap break-words text-sm leading-7 text-[#f7efe7] sm:text-[15px]">
        {displayText}
      </p>
    </article>
  )
}
