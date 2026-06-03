import os
import uuid
from datetime import datetime

import uvicorn
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from utils import (
    get_instance_index,
    clear_cache_headers,
    get_cpu_usage        
)

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


TODO_DB: list[TodoItem] = []


@app.get("/")
async def root(request: Request):
    # CF_INSTANCE_INDEX automatiquement sur les serveurs Cf ")
    instance_index = get_instance_index()
    cpu_usage = get_cpu_usage()
    
    response = templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "instance_index": instance_index,
            "cpu_usage": cpu_usage,
            "todos": TODO_DB,
        },
    )

    # Clear des headers pour remove le cache du navigateur 
    clear_cache_headers(response)
    
    return response

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("static/images/cloud_foundry.png")


@app.get("/api/todos")
async def list_todos():
    return {"todos": TODO_DB}


@app.post("/api/todos", status_code=201)
async def create_todo(payload: TodoCreate):
    todo = TodoItem(
        id=str(uuid.uuid4())[:8],
        title=payload.title.strip(),
        description=payload.description.strip(),
        created_at=datetime.now().replace(microsecond=0).isoformat(timespec="seconds"),
    )
    TODO_DB.append(todo)
    return todo


@app.delete("/api/todos/{todo_id}", status_code=204)
async def delete_todo(todo_id: str):
    for index, todo in enumerate(TODO_DB):
        if todo.id == todo_id:
            del TODO_DB[index]
            return Response(status_code=204)

    raise HTTPException(status_code=404, detail="Todo introuvable")


app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))

    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
