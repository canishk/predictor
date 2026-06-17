export default function DisclaimerBanner() {
  return (
    <aside
      role="note"
      className="mb-6 rounded-xl border border-amber-700/50 bg-amber-950/30 p-4 text-amber-100"
    >
      <p className="text-sm font-semibold text-amber-400">Market data only.</p>
      <p className="mt-1 text-sm leading-relaxed">
        Predictions here reflect Polymarket trading interest and market odds, not forecasts of actual
        match scores or official results.
      </p>
    </aside>
  );
}
