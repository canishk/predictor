from datetime import datetime

from pydantic import BaseModel, Field


class MatchSummary(BaseModel):
    match_id: int
    home_team: str
    away_team: str
    kickoff: datetime
    status: str
    day_bucket: str
    home_score: int | None = None
    away_score: int | None = None
    winner_prediction: str | None = None
    home_win_probability: float | None = None
    away_win_probability: float | None = None
    goal_difference: int | None = None
    confidence: int | None = None


class TeamFormSchema(BaseModel):
    results: list[str] = Field(default_factory=list)
    goals_scored: int = 0
    goals_conceded: int = 0
    matches: list[dict] = Field(default_factory=list)
    avg_goal_difference: float = 0.0


class MarketDataSchema(BaseModel):
    event_title: str | None = None
    market_question: str | None = None
    outcomes: list[dict] = Field(default_factory=list)
    volume: float | None = None
    liquidity: float | None = None
    draw_probability: float | None = None


class PredictionDetailSchema(BaseModel):
    winner: str | None = None
    home_win_probability: float | None = None
    away_win_probability: float | None = None
    draw_probability: float | None = None
    goal_difference: int | None = None
    confidence: int | None = None
    explanation: dict = Field(default_factory=dict)


class FixtureSchema(BaseModel):
    match_id: int
    home_team: str
    away_team: str
    kickoff: datetime
    status: str
    group: str | None = None
    stage: str | None = None
    matchday: int | None = None
    day_bucket: str
    home_score: int | None = None
    away_score: int | None = None


class MatchDetailResponse(BaseModel):
    fixture: FixtureSchema
    prediction: PredictionDetailSchema
    recent_form: dict[str, TeamFormSchema]
    market_data: MarketDataSchema


class RefreshResponse(BaseModel):
    processed: int
    today: int
    tomorrow: int
