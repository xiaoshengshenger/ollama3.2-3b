from fastapi import APIRouter

test = APIRouter()

@test.get("/ping")
def test2():
    return {"message": "test2"}