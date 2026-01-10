from fastapi import APIRouter, Depends

router = APIRouter(
    prefix="/daemon",
    tags=["daemon"],
)


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/test")
async def test():
    ...
