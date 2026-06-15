import { fetchMatches } from "../api";
import MatchSection from "../components/MatchSection";
import { usePolling } from "../hooks";

export default function HomePage() {
  const { data, loading, error, reload } = usePolling(fetchMatches);

  if (loading && !data) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-48 animate-pulse rounded bg-slate-800" />
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="h-48 animate-pulse rounded-xl bg-slate-800" />
          <div className="h-48 animate-pulse rounded-xl bg-slate-800" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-xl border border-rose-800 bg-rose-950/40 p-6 text-center">
        <p className="text-rose-300">{error}</p>
        <button onClick={reload} className="mt-4 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium hover:bg-emerald-500">
          Retry
        </button>
      </div>
    );
  }

  const matches = data ?? [];
  const today = matches.filter((m) => m.day_bucket === "today");
  const tomorrow = matches.filter((m) => m.day_bucket === "tomorrow");

  return (
    <div className="space-y-10">
      <header>
        <h1 className="text-3xl font-bold tracking-tight">World Cup Predictor</h1>
        <p className="mt-2 text-slate-400">Polymarket insights + Football-Data form. Auto-refreshes every 15 minutes.</p>
      </header>
      <MatchSection title="Today" matches={today} />
      <MatchSection title="Tomorrow" matches={tomorrow} />
    </div>
  );
}
