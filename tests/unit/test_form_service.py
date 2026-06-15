from app.services.form_service import build_team_form_map, compute_form, empty_form


def test_empty_form():
    form = empty_form()
    assert form["results"] == []
    assert form["avg_goal_difference"] == 0.0


def test_build_team_form_map_ignores_timed_matches():
    matches = [
        {
            "status": "TIMED",
            "utcDate": "2026-06-10T00:00:00Z",
            "homeTeam": {"id": 10, "name": "Argentina"},
            "awayTeam": {"id": 20, "name": "Brazil"},
        },
        {
            "status": "FINISHED",
            "utcDate": "2026-06-01T00:00:00Z",
            "homeTeam": {"id": 10, "name": "Argentina"},
            "awayTeam": {"id": 99, "name": "Other"},
            "score": {"fullTime": {"home": 2, "away": 0}},
        },
        {
            "status": "FINISHED",
            "utcDate": "2026-05-25T00:00:00Z",
            "homeTeam": {"id": 88, "name": "Other2"},
            "awayTeam": {"id": 10, "name": "Argentina"},
            "score": {"fullTime": {"home": 1, "away": 1}},
        },
    ]
    form_map = build_team_form_map(matches)
    assert form_map[10]["results"] == ["D", "W"]
    assert 20 not in form_map


def test_compute_form():
    matches = [
        {
            "utcDate": "2026-06-01T00:00:00Z",
            "homeTeam": {"id": 10, "name": "Argentina"},
            "awayTeam": {"id": 99, "name": "Other"},
            "score": {"fullTime": {"home": 2, "away": 0}},
        },
        {
            "utcDate": "2026-05-25T00:00:00Z",
            "homeTeam": {"id": 88, "name": "Other2"},
            "awayTeam": {"id": 10, "name": "Argentina"},
            "score": {"fullTime": {"home": 1, "away": 1}},
        },
    ]
    form = compute_form(matches, 10)
    assert form["results"] == ["W", "D"]
    assert form["goals_scored"] == 3
    assert form["goals_conceded"] == 1
