import type { MatchSummary } from "./api";

function localDayKey(d: Date): string {
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function addDays(d: Date, days: number): Date {
  const next = new Date(d);
  next.setDate(next.getDate() + days);
  return next;
}

function sortByKickoff(matches: MatchSummary[]): MatchSummary[] {
  return [...matches].sort(
    (a, b) => new Date(a.kickoff).getTime() - new Date(b.kickoff).getTime(),
  );
}

function sortByKickoffDesc(matches: MatchSummary[]): MatchSummary[] {
  return [...matches].sort(
    (a, b) => new Date(b.kickoff).getTime() - new Date(a.kickoff).getTime(),
  );
}

function isFinishedWithScore(match: MatchSummary): boolean {
  return (
    match.status === "FINISHED" &&
    match.home_score !== null &&
    match.away_score !== null
  );
}

export function groupMatchesByLocalDay(matches: MatchSummary[]) {
  const today = localDayKey(new Date());
  const tomorrow = localDayKey(addDays(new Date(), 1));
  const yesterday = localDayKey(addDays(new Date(), -1));

  const todayMatches = sortByKickoff(
    matches.filter((m) => localDayKey(new Date(m.kickoff)) === today),
  );
  const tomorrowMatches = sortByKickoff(
    matches.filter((m) => localDayKey(new Date(m.kickoff)) === tomorrow),
  );
  const yesterdayRecent = sortByKickoffDesc(
    matches.filter((m) => localDayKey(new Date(m.kickoff)) === yesterday && isFinishedWithScore(m)),
  ).slice(0, 2);

  return { today: todayMatches, tomorrow: tomorrowMatches, yesterdayRecent };
}
