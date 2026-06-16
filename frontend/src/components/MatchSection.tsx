import MatchCard from "../components/MatchCard";
import type { MatchSummary } from "../api";

interface Props {
  title: string;
  matches: MatchSummary[];
  emptyLabel?: string;
}

export default function MatchSection({ title, matches, emptyLabel = "No matches." }: Props) {
  return (
    <section className="space-y-4">
      <h2 className="text-xl font-bold tracking-tight text-emerald-400">
        {title}{matches.length > 0 ? ` (${matches.length})` : ""}
      </h2>
      {matches.length === 0 ? (
        <p className="rounded-xl border border-dashed border-slate-700 p-6 text-center text-slate-500">
          {emptyLabel}
        </p>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {matches.map((match) => (
            <MatchCard key={match.match_id} match={match} />
          ))}
        </div>
      )}
    </section>
  );
}
