from fastapi import APIRouter

router = APIRouter(prefix="/daemon", tags=["daemon"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
