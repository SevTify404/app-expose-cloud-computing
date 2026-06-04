import os

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from db import BDWrapper, get_todo_db
from utils import clear_cache_headers, get_cpu_usage, get_instance_index

app = FastAPI(title="Démo Exposé Cloud Foundry")

templates = Jinja2Templates(directory="static")


class TodoCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=250)


class TodoItem(BaseModel):
    id: str
    title: str
    description: str
    created_at: str


@app.get("/")
async def root(request: Request, repo: BDWrapper = Depends(get_todo_db)):
    # CF_INSTANCE_INDEX automatiquement sur les serveurs Cf ")
    instance_index = get_instance_index()
    cpu_usage = get_cpu_usage()
    
    todos_enabled = repo.ready
    response = templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "instance_index": instance_index,
            "cpu_usage": cpu_usage,
            "todos": repo.list_todos(),
            "todos_enabled": todos_enabled,
            "todo_status_message": repo.fallback_reason if not todos_enabled else "Base de données prête pour la démo.",
        },
    )

    # Clear des headers pour remove le cache du navigateur 
    clear_cache_headers(response)
    
    return response

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("static/images/cloud_foundry.png")


@app.get("/api/todos")
async def list_todos(repo: BDWrapper = Depends(get_todo_db)):
    if not repo.ready:
        raise HTTPException(status_code=503, detail="TODO indisponible tant que le service de base de données n’est pas bindé.")
    return {"todos": repo.list_todos()}


@app.post("/api/todos", status_code=201)
async def create_todo(payload: TodoCreate, repo: BDWrapper = Depends(get_todo_db)):
    if not repo.ready:
        raise HTTPException(status_code=503, detail="TODO indisponible tant que le service de base de données n’est pas bindé.")
    todo = repo.create_todo(payload.title, payload.description)
    if "error" in todo:
        raise HTTPException(status_code=503, detail="TODO indisponible pour le moment.")
    return todo


@app.delete("/api/todos/{todo_id}", status_code=204)
async def delete_todo(todo_id: str, repo: BDWrapper = Depends(get_todo_db)):
    if not repo.ready:
        raise HTTPException(status_code=503, detail="TODO indisponible tant que le service de base de données n’est pas bindé.")
    deleted = repo.delete_todo(todo_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Todo introuvable")

    return Response(status_code=204)

@app.get("/work")
async def work():
    total = 0

    for i in range(30_000_000):
        total += i

    return {
        "instance": get_instance_index(),
        "result": total
    }

app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))

    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
