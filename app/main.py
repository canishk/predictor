import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config import get_settings
from app.database.seed_mappings import seed_team_mappings
from app.database.session import SessionLocal, init_db
from app.services.refresh_service import RefreshService

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


async def scheduled_refresh() -> None:
    db = SessionLocal()
    try:
        result = await RefreshService(db).run()
        logger.info("Scheduled refresh completed: %s", result)
    except Exception:
        logger.exception("Scheduled refresh failed")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    db = SessionLocal()
    try:
        seed_team_mappings(db)
    finally:
        db.close()

    settings = get_settings()
    if not settings.disable_scheduler:
        scheduler.add_job(
            scheduled_refresh,
            "interval",
            minutes=settings.refresh_interval_minutes,
            id="refresh_job",
            replace_existing=True,
        )
        scheduler.start()

        try:
            await scheduled_refresh()
        except Exception:
            logger.exception("Initial refresh failed")
    else:
        logger.info("Scheduler disabled")

    yield
    if scheduler.running:
        scheduler.shutdown(wait=False)


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="World Cup Predictor", version="1.0.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run("app.main:app", host="127.0.0.1", port=settings.api_port, reload=True)
