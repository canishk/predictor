from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    football_data_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    short_name: Mapped[str | None] = mapped_column(String(60))
    tla: Mapped[str | None] = mapped_column(String(5))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    home_fixtures: Mapped[list["Fixture"]] = relationship(
        "Fixture", back_populates="home_team", foreign_keys="Fixture.home_team_id"
    )
    away_fixtures: Mapped[list["Fixture"]] = relationship(
        "Fixture", back_populates="away_team", foreign_keys="Fixture.away_team_id"
    )


class Fixture(Base):
    __tablename__ = "fixtures"

    match_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    home_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    away_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    utc_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    group_name: Mapped[str | None] = mapped_column("group", String(10))
    stage: Mapped[str | None] = mapped_column(String(40))
    matchday: Mapped[int | None] = mapped_column(Integer)
    day_bucket: Mapped[str] = mapped_column(String(20), index=True)
    home_score: Mapped[int | None] = mapped_column(Integer)
    away_score: Mapped[int | None] = mapped_column(Integer)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    home_team: Mapped["Team"] = relationship("Team", foreign_keys=[home_team_id], back_populates="home_fixtures")
    away_team: Mapped["Team"] = relationship("Team", foreign_keys=[away_team_id], back_populates="away_fixtures")
    prediction_markets: Mapped[list["PredictionMarket"]] = relationship(
        "PredictionMarket", back_populates="fixture"
    )
    predictions: Mapped[list["Prediction"]] = relationship("Prediction", back_populates="fixture")


class TeamNameMapping(Base):
    __tablename__ = "team_name_mappings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    canonical_name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    alias: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(30), default="seed")


class PredictionMarket(Base):
    __tablename__ = "prediction_markets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fixture_id: Mapped[int] = mapped_column(ForeignKey("fixtures.match_id"), nullable=False, index=True)
    polymarket_event_id: Mapped[str | None] = mapped_column(String(64))
    polymarket_market_id: Mapped[str | None] = mapped_column(String(64))
    event_title: Mapped[str | None] = mapped_column(String(255))
    market_question: Mapped[str | None] = mapped_column(String(500))
    outcomes_json: Mapped[str | None] = mapped_column(Text)
    clob_token_ids_json: Mapped[str | None] = mapped_column(Text)
    volume: Mapped[float | None] = mapped_column()
    liquidity: Mapped[float | None] = mapped_column()
    raw_json: Mapped[str | None] = mapped_column(Text)
    matched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    fixture: Mapped["Fixture"] = relationship("Fixture", back_populates="prediction_markets")


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fixture_id: Mapped[int] = mapped_column(ForeignKey("fixtures.match_id"), nullable=False, index=True)
    home_win_probability: Mapped[float | None] = mapped_column()
    away_win_probability: Mapped[float | None] = mapped_column()
    draw_probability: Mapped[float | None] = mapped_column()
    goal_difference: Mapped[int | None] = mapped_column(Integer)
    confidence: Mapped[int | None] = mapped_column(Integer)
    winner: Mapped[str | None] = mapped_column(String(120))
    explanation_json: Mapped[str | None] = mapped_column(Text)
    snapshot_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    fixture: Mapped["Fixture"] = relationship("Fixture", back_populates="predictions")
