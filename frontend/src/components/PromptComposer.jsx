const QUICK_PROMPTS = [
  'Explain semantic caching in plain English.',
  'Why would a cache hit reduce latency for repeated prompts?',
  'Compare vector search with exact-match caching.',
]

export function PromptComposer({
  disabled,
  maxLength,
  onChange,
  onKeyDown,
  onQuickFill,
  onSubmit,
  statusText,
  textareaRef,
  value,
}) {
  return (
    <form onSubmit={onSubmit} className="mt-auto" noValidate>
      <div className="terminal-panel rounded-[26px] border border-dashed border-[#ff6b4a]/55 bg-[#151513]/95 p-4 sm:p-5">
        <div className="flex items-start gap-4">
          <span className="pt-2 text-xl text-[#ff6b4a] sm:text-2xl" aria-hidden="true">
            &gt;
          </span>

          <textarea
            ref={textareaRef}
            rows={1}
            maxLength={maxLength}
            value={value}
            onChange={(event) => onChange(event.target.value)}
            onKeyDown={onKeyDown}
            disabled={disabled}
            placeholder='ask semantic-cache "how does vector similarity reduce cost?"'
            className="max-h-[220px] min-h-[3.5rem] flex-1 resize-none overflow-y-auto bg-transparent text-sm leading-7 text-[#f7efe7] outline-none placeholder:text-[#807871] disabled:cursor-not-allowed disabled:text-[#8f8780] sm:text-[15px]"
          />

          <button
            type="submit"
            disabled={disabled || !value.trim()}
            className="rounded-[14px] border border-[#ff6b4a]/60 bg-[#ff6b4a]/10 px-4 py-3 text-[11px] font-medium uppercase tracking-[0.28em] text-[#ff6b4a] transition hover:bg-[#ff6b4a]/18 disabled:cursor-not-allowed disabled:border-[#ff6b4a]/20 disabled:bg-transparent disabled:text-[#7d746e]"
          >
            {disabled ? 'WAIT' : 'RUN'}
          </button>
        </div>

        <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-[#ff6b4a]/14 pt-3">
          <div className="flex flex-wrap items-center gap-3 text-[10px] uppercase tracking-[0.26em] text-[#8a817b] sm:text-[11px]">
            <span>{statusText}</span>
            <span>enter send</span>
            <span>shift+enter newline</span>
            <span>/clear reset</span>
            <span>/help commands</span>
          </div>
          <span className="text-[10px] uppercase tracking-[0.26em] text-[#8a817b] sm:text-[11px]">
            {`${value.length}/${maxLength}`}
          </span>
        </div>

        <div className="mt-4 flex flex-wrap gap-2">
          {QUICK_PROMPTS.map((prompt) => (
            <button
              key={prompt}
              type="button"
              onClick={() => onQuickFill(prompt)}
              className="rounded-full border border-dashed border-[#ff6b4a]/28 px-3 py-2 text-[10px] uppercase tracking-[0.22em] text-[#c7b8af] transition hover:border-[#ff6b4a]/50 hover:bg-[#ff6b4a]/8 hover:text-[#fff3ee] sm:text-[11px]"
            >
              {prompt}
            </button>
          ))}
        </div>
      </div>
    </form>
  )
}
