import { Link, useParams } from "react-router-dom";
import { fetchMatchDetail } from "../api";
import { formatKickoff, formatPct, usePolling } from "../hooks";

function FormRow({ label, form }: { label: string; form: { results: string[]; goals_scored: number; goals_conceded: number } }) {
  return (
    <div className="rounded-lg bg-pitch-900 p-4">
      <p className="mb-2 font-medium text-emerald-400">{label}</p>
      <p className="text-2xl tracking-widest">{form.results.join(" ") || "—"}</p>
      <p className="mt-2 text-sm text-slate-400">
        Goals: {form.goals_scored} scored / {form.goals_conceded} conceded
      </p>
    </div>
  );
}

function ProbabilityBar({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <div className="mb-1 flex justify-between text-sm">
        <span>{label}</span>
        <span>{formatPct(value)}</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-slate-800">
        <div className="h-full rounded-full bg-emerald-500" style={{ width: `${value * 100}%` }} />
      </div>
    </div>
  );
}

export default function MatchDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data, loading, error } = usePolling(() => fetchMatchDetail(id!), [id]);

  if (!id) return null;

  if (loading && !data) {
    return <div className="h-64 animate-pulse rounded-xl bg-slate-800" />;
  }

  if (error || !data) {
    return <p className="text-rose-300">{error ?? "Match not found"}</p>;
  }

  const { fixture, prediction, recent_form, market_data } = data;

  return (
    <div className="space-y-8">
      <Link to="/" className="text-sm text-emerald-400 hover:underline">
        ← Back to matches
      </Link>

      <header className="space-y-2">
        <p className="text-sm text-slate-400">{formatKickoff(fixture.kickoff)} · {fixture.stage ?? fixture.status}</p>
        <h1 className="text-3xl font-bold">
          {fixture.home_team} vs {fixture.away_team}
        </h1>
        {fixture.group && <p className="text-slate-400">Group {fixture.group.replace("GROUP_", "")}</p>}
      </header>

      <section className="rounded-xl border border-slate-800 bg-pitch-800 p-6">
        <h2 className="mb-4 text-lg font-semibold text-emerald-400">Prediction</h2>
        <div className="grid gap-4 sm:grid-cols-3">
          <div>
            <p className="text-slate-500">Winner</p>
            <p className="text-xl font-bold">{prediction.winner ?? "—"}</p>
          </div>
          <div>
            <p className="text-slate-500">Goal difference</p>
            <p className="text-xl font-bold">{prediction.goal_difference ?? "—"}</p>
          </div>
          <div>
            <p className="text-slate-500">Confidence</p>
            <p className="text-xl font-bold">{prediction.confidence ?? "—"}/100</p>
          </div>
        </div>
        {prediction.explanation?.summary && (
          <p className="mt-4 text-sm leading-relaxed text-slate-300">{prediction.explanation.summary}</p>
        )}
      </section>

      <section className="rounded-xl border border-slate-800 bg-pitch-800 p-6">
        <h2 className="mb-4 text-lg font-semibold text-emerald-400">Polymarket probabilities</h2>
        <div className="space-y-4">
          {prediction.home_win_probability !== null && (
            <ProbabilityBar label={fixture.home_team} value={prediction.home_win_probability} />
          )}
          {prediction.away_win_probability !== null && (
            <ProbabilityBar label={fixture.away_team} value={prediction.away_win_probability} />
          )}
          {prediction.draw_probability !== null && (
            <ProbabilityBar label="Draw" value={prediction.draw_probability} />
          )}
          {market_data.outcomes.map((o) => (
            <ProbabilityBar key={o.label} label={o.label} value={o.probability} />
          ))}
        </div>
        <div className="mt-6 grid gap-4 sm:grid-cols-2 text-sm">
          <div>
            <p className="text-slate-500">Market volume</p>
            <p className="font-medium">${(market_data.volume ?? 0).toLocaleString()}</p>
          </div>
          <div>
            <p className="text-slate-500">Market liquidity</p>
            <p className="font-medium">${(market_data.liquidity ?? 0).toLocaleString()}</p>
          </div>
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="text-lg font-semibold text-emerald-400">Recent form (last 5)</h2>
        <div className="grid gap-4 sm:grid-cols-2">
          <FormRow label={fixture.home_team} form={recent_form.home} />
          <FormRow label={fixture.away_team} form={recent_form.away} />
        </div>
      </section>

      {prediction.explanation?.factors && (
        <section className="rounded-xl border border-slate-800 bg-pitch-800 p-6">
          <h2 className="mb-4 text-lg font-semibold text-emerald-400">Prediction factors</h2>
          <ul className="space-y-2 text-sm">
            {prediction.explanation.factors.map((f) => (
              <li key={f.name} className="flex justify-between border-b border-slate-700/50 py-2">
                <span className="text-slate-400">{f.name}</span>
                <span>
                  {f.value} <span className="text-slate-500">({f.impact})</span>
                </span>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
