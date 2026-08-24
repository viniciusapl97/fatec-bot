# api/main.py
#
# API do Jovis: expõe bot/services/ por HTTP pro site e pro app (autenticação
# via token de acesso pessoal, gerado no bot com /tokendeacesso — ver
# api/deps.py). Não depende de nada específico do Telegram.
#
# Rodar localmente: uvicorn api.main:app --reload

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import auth, me, subjects, activities, absences, grades
from bot.core.settings import FRONTEND_ORIGINS

app = FastAPI(
    title="Jovis API",
    version="0.1.0",
    description="API do Jovis — mesmos dados do bot de Telegram, para o site e o app.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(me.router)
app.include_router(subjects.router)
app.include_router(activities.router)
app.include_router(absences.router)
app.include_router(grades.router)


@app.get("/health", tags=["health"])
async def health() -> dict:
    """Endpoint simples pra checar se a API está no ar (sem autenticação)."""
    return {"status": "ok"}
