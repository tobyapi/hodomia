export function PlayerIcon({ name }: { name: "play" | "pause" | "start" | "repeat" | "back10" | "forward10" }) {
  return <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    {name === "play" && <path d="m9 5 11 7-11 7Z" fill="currentColor" stroke="none" />}
    {name === "pause" && <><path d="M8 5v14M16 5v14" strokeWidth="4" /></>}
    {name === "start" && <><path d="M6 5v14" /><path d="M18 5 8 12l10 7Z" fill="currentColor" stroke="none" /></>}
    {name === "repeat" && <><path d="m17 2 4 4-4 4M3 11V9a3 3 0 0 1 3-3h15M7 22l-4-4 4-4m14-3v4a3 3 0 0 1-3 3H3" /></>}
    {(name === "back10" || name === "forward10") && <>
      <g transform={name === "forward10" ? "translate(24 0) scale(-1 1)" : undefined}>
        <path d="M4 8a8 8 0 1 1-1 7M4 3v5h5" />
      </g>
      <path d="m7.5 11 2-1v7m5-7a2 2 0 0 1 2 2v3a2 2 0 0 1-4 0v-3a2 2 0 0 1 2-2Z" strokeWidth="1.4" />
    </>}
  </svg>;
}
