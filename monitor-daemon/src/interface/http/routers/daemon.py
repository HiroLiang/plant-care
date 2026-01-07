from fastapi import APIRouter, Depends

router = APIRouter(
    prefix="/daemon",
    tags=["daemon"],
)


@router.get("/health")
async def health():
    return {"status": "ok"}
