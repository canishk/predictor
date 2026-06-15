import { Link } from "react-router-dom";
import type { MatchSummary } from "../api";
import { formatKickoff, formatPct } from "../hooks";

interface Props {
  match: MatchSummary;
}

function ConfidenceBadge({ value }: { value: number | null }) {
  if (value === null) return <span className="text-slate-500">N/A</span>;
  const color =
    value >= 70 ? "bg-emerald-500/20 text-emerald-300" : value >= 40 ? "bg-amber-500/20 text-amber-300" : "bg-rose-500/20 text-rose-300";
  return <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${color}`}>{value}</span>;
}

export default function MatchCard({ match }: Props) {
  return (
    <Link
      to={`/match/${match.match_id}`}
      className="block rounded-xl border border-slate-800 bg-pitch-800 p-4 shadow-lg transition hover:border-emerald-500/40 hover:shadow-emerald-900/20"
    >
      <div className="mb-3 flex items-center justify-between text-xs text-slate-400">
        <span>{formatKickoff(match.kickoff)}</span>
        <span className="uppercase">{match.status}</span>
      </div>

      <div className="mb-4 space-y-1">
        <p className="text-lg font-semibold">{match.home_team}</p>
        <p className="text-sm text-slate-400">vs</p>
        <p className="text-lg font-semibold">{match.away_team}</p>
      </div>

      <div className="grid grid-cols-2 gap-3 text-sm">
        <div>
          <p className="text-slate-500">Predicted winner</p>
          <p className="font-medium text-emerald-400">{match.winner_prediction ?? "—"}</p>
        </div>
        <div>
          <p className="text-slate-500">Home win</p>
          <p className="font-medium">{formatPct(match.home_win_probability)}</p>
        </div>
        <div>
          <p className="text-slate-500">Goal diff</p>
          <p className="font-medium">{match.goal_difference ?? "—"}</p>
        </div>
        <div>
          <p className="text-slate-500">Confidence</p>
          <ConfidenceBadge value={match.confidence} />
        </div>
      </div>
    </Link>
  );
}
