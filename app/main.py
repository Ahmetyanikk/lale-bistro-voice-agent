from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.database import Base, SessionLocal, engine
from app.routers.tools import router as tools_router
from app.seed import seed_if_empty


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_if_empty(db)
    finally:
        db.close()
    yield


app = FastAPI(title="Lale Bistro Voice Assistant Backend", lifespan=lifespan)
app.include_router(tools_router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.exception_handler(RequestValidationError)
def validation_error_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"error": "invalid_request"})


@app.exception_handler(Exception)
def unhandled_error_handler(request: Request, exc: Exception):
    # never leak stack traces or DB details to the caller
    return JSONResponse(status_code=500, content={"error": "internal_error"})
