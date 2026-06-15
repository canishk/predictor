from typing import Any


def empty_form() -> dict[str, Any]:
    return {
        "results": [],
        "goals_scored": 0,
        "goals_conceded": 0,
        "matches": [],
        "avg_goal_difference": 0.0,
    }


def _match_has_score(match: dict[str, Any]) -> bool:
    score = match.get("score", {}).get("fullTime", {})
    return score.get("home") is not None and score.get("away") is not None


def build_team_form_map(matches: list[dict[str, Any]], *, limit: int = 5) -> dict[int, dict[str, Any]]:
    finished = [
        match for match in matches if match.get("status") == "FINISHED" and _match_has_score(match)
    ]

    team_matches: dict[int, list[dict[str, Any]]] = {}
    for match in finished:
        for team_key in ("homeTeam", "awayTeam"):
            team = match.get(team_key, {})
            team_id = team.get("id")
            if team_id is None:
                continue
            team_matches.setdefault(team_id, []).append(match)

    form_map: dict[int, dict[str, Any]] = {}
    for team_id, match_list in team_matches.items():
        recent = sorted(match_list, key=lambda match: match.get("utcDate", ""), reverse=True)[:limit]
        chronological = sorted(recent, key=lambda match: match.get("utcDate", ""))
        form_map[team_id] = compute_form(chronological, team_id)

    return form_map


def compute_form(match_list: list[dict[str, Any]], team_id: int) -> dict[str, Any]:
    results: list[str] = []
    goals_scored = 0
    goals_conceded = 0
    matches_detail: list[dict[str, Any]] = []

    for match in match_list:
        home = match.get("homeTeam", {})
        away = match.get("awayTeam", {})
        score = match.get("score", {}).get("fullTime", {})
        home_goals = score.get("home")
        away_goals = score.get("away")

        if home_goals is None or away_goals is None:
            continue

        is_home = home.get("id") == team_id
        team_goals = home_goals if is_home else away_goals
        opp_goals = away_goals if is_home else home_goals
        goals_scored += team_goals
        goals_conceded += opp_goals

        if team_goals > opp_goals:
            results.append("W")
        elif team_goals < opp_goals:
            results.append("L")
        else:
            results.append("D")

        opponent = away.get("name") if is_home else home.get("name")
        matches_detail.append(
            {
                "opponent": opponent,
                "result": results[-1],
                "goals_scored": team_goals,
                "goals_conceded": opp_goals,
                "date": match.get("utcDate"),
            }
        )

    avg_goal_diff = 0.0
    if matches_detail:
        diffs = [m["goals_scored"] - m["goals_conceded"] for m in matches_detail]
        avg_goal_diff = sum(diffs) / len(diffs)

    return {
        "results": results,
        "goals_scored": goals_scored,
        "goals_conceded": goals_conceded,
        "matches": matches_detail,
        "avg_goal_difference": avg_goal_diff,
    }
