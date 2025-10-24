
from fastapi import FastAPI
from api import eval_sets_api, eval_data_api, eval_results_api, config_api, jobs_api
from utils.log import get_logger
from fastapi.middleware.cors import CORSMiddleware
import os
import asyncio
from services.cleanup_service import schedule_cleanup


logger = get_logger("main")


def create_app() -> FastAPI:
    app = FastAPI(title="hi_api", version="0.1.0")
    logger.info("Registering routers...")

    # CORS: 开发时允许本地前端端口访问后端，避免浏览器因跨域而阻断请求。
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(eval_sets_api.router, prefix="/api/v1/evalsets", tags=["evalsets"])
    app.include_router(eval_data_api.router, prefix="/api/v1", tags=["evaldata"])
    app.include_router(eval_results_api.router)
    app.include_router(config_api.router)
    # jobs API (status polling for background tasks)
    app.include_router(jobs_api.router)

    @app.get("/api/v1/health", summary="轻量健康检查")
    def health():
        return {"status": "ok"}

    @app.on_event("startup")
    async def on_startup():
        logger.info("App startup event triggered.")
        # optional cleanup scheduler
        try:
            if os.getenv('CLEANUP_ENABLED', '0') in ('1', 'true', 'True'):
                interval = int(os.getenv('CLEANUP_INTERVAL_SECONDS', str(24 * 3600)))
                # run scheduler in background
                logger.info(f"Starting cleanup scheduler (interval_seconds={interval})")
                asyncio.create_task(asyncio.to_thread(schedule_cleanup, interval))
        except Exception as e:
            logger.exception(f"Failed to start cleanup scheduler: {e}")

    @app.on_event("shutdown")
    async def on_shutdown():
        logger.info("App shutdown event triggered.")

    return app



app = create_app()


if __name__ == "__main__":
    import uvicorn
    logger.info("Running app with uvicorn...")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
