export interface MatchSummary {
  match_id: number;
  home_team: string;
  away_team: string;
  kickoff: string;
  status: string;
  day_bucket: string;
  home_score: number | null;
  away_score: number | null;
  winner_prediction: string | null;
  home_win_probability: number | null;
  away_win_probability: number | null;
  goal_difference: number | null;
  confidence: number | null;
}

export interface TeamForm {
  results: string[];
  goals_scored: number;
  goals_conceded: number;
  matches: Array<{
    opponent: string;
    result: string;
    goals_scored: number;
    goals_conceded: number;
    date: string;
  }>;
  avg_goal_difference: number;
}

export interface MatchDetail {
  fixture: {
    match_id: number;
    home_team: string;
    away_team: string;
    kickoff: string;
    status: string;
    group: string | null;
    stage: string | null;
    matchday: number | null;
    day_bucket: string;
    home_score: number | null;
    away_score: number | null;
  };
  prediction: {
    winner: string | null;
    home_win_probability: number | null;
    away_win_probability: number | null;
    draw_probability: number | null;
    goal_difference: number | null;
    confidence: number | null;
    explanation: {
      summary?: string;
      factors?: Array<{ name: string; value: string; impact: string }>;
    };
  };
  recent_form: {
    home: TeamForm;
    away: TeamForm;
  };
  market_data: {
    event_title: string | null;
    market_question: string | null;
    outcomes: Array<{ label: string; probability: number }>;
    volume: number | null;
    liquidity: number | null;
    draw_probability: number | null;
  };
}

const REFRESH_MS = 60 * 60 * 1000;

export async function fetchMatches(): Promise<MatchSummary[]> {
  const res = await fetch("/api/matches");
  if (!res.ok) throw new Error("Failed to load matches");
  return res.json();
}

export async function fetchMatchDetail(id: string): Promise<MatchDetail> {
  const res = await fetch(`/api/matches/${id}`);
  if (!res.ok) throw new Error("Failed to load match detail");
  return res.json();
}

export { REFRESH_MS };
