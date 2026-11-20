from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from db.auth import get_current_user
from routers import documents
from routers import documents, query, chats


app = FastAPI(title="AskAnyPDF API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://askanypdf.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router)
app.include_router(query.router)  
app.include_router(chats.router)

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/me")
def me(user_id: str = Depends(get_current_user)):
    return {"user_id": user_id}