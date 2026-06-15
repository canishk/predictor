from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.match import MatchDetailResponse, MatchSummary, RefreshResponse
from app.services.match_query_service import MatchQueryService
from app.services.refresh_service import RefreshService

router = APIRouter(prefix="/api")


@router.get("/matches", response_model=list[MatchSummary])
def list_matches(db: Session = Depends(get_db)) -> list[MatchSummary]:
    return MatchQueryService(db).list_matches()


@router.get("/matches/{match_id}", response_model=MatchDetailResponse)
async def get_match(match_id: int, db: Session = Depends(get_db)) -> MatchDetailResponse:
    detail = await MatchQueryService(db).get_match_detail(match_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Match not found")
    return detail


@router.post("/admin/refresh", response_model=RefreshResponse)
async def refresh_data(db: Session = Depends(get_db)) -> RefreshResponse:
    result = await RefreshService(db).run()
    return RefreshResponse(**result)


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
