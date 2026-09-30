/** PolyGraphe's mark: a heartbeat on the interactive blue. */
export function BrandMark({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" aria-hidden="true" className={className}>
      <rect width="32" height="32" className="fill-interactive" />
      <polyline
        points="4,18 10,18 12.5,13 15.5,24 18.5,8 21,18 28,18"
        fill="none"
        strokeWidth="2"
        className="stroke-white"
      />
    </svg>
  );
}
