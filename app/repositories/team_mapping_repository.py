from sqlalchemy.orm import Session

from app.models import Team, TeamNameMapping


class TeamMappingRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_aliases(self, canonical_name: str) -> list[str]:
        rows = (
            self.db.query(TeamNameMapping)
            .filter(TeamNameMapping.canonical_name == canonical_name)
            .all()
        )
        aliases = {canonical_name}
        for row in rows:
            aliases.add(row.alias)
        return sorted(aliases)

    def resolve_canonical(self, name: str) -> str:
        direct = (
            self.db.query(TeamNameMapping)
            .filter(TeamNameMapping.canonical_name == name)
            .first()
        )
        if direct:
            return direct.canonical_name

        alias_match = (
            self.db.query(TeamNameMapping)
            .filter(TeamNameMapping.alias.ilike(name))
            .first()
        )
        if alias_match:
            return alias_match.canonical_name
        return name

    def all_search_names(self, team_name: str) -> list[str]:
        canonical = self.resolve_canonical(team_name)
        return self.get_aliases(canonical)


class TeamRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def upsert_team(self, team_data: dict) -> Team:
        fd_id = team_data["id"]
        team = self.db.query(Team).filter(Team.football_data_id == fd_id).first()
        if not team:
            team = Team(football_data_id=fd_id)
            self.db.add(team)
        team.name = team_data.get("name", team.name)
        team.short_name = team_data.get("shortName")
        team.tla = team_data.get("tla")
        self.db.flush()
        return team
