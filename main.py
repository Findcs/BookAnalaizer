import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from configs.Database import create_db_and_tables
from routers.FeedbackRouter import FeedbackRouter
from routers.RequestsRouter import RequestsRouter
from routers.SectionRouter import SectionRouter
from routers.UserRouter import UserRouter
from routers.DocumentRouter import DocumentRouter
from routers.BibliographicReferenceRouter import BibliographicRouter
app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(UserRouter)
app.include_router(RequestsRouter)
app.include_router(FeedbackRouter)
app.include_router(BibliographicRouter)
app.include_router(DocumentRouter)
app.include_router(SectionRouter)
@app.on_event("startup")
async def on_startup():
    await create_db_and_tables()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
