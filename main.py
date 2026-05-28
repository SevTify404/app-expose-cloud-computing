import os
import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates
from utils import get_instance_index, get_cpu_usage

app = FastAPI(title="Démo Exposé Cloud Foundry")


templates = Jinja2Templates(directory="static")


@app.get("/")
async def root(request: Request):
    # CF_INSTANCE_INDEX automatiquement sur les serveurs Cf ")
    instance_index = get_instance_index()
    cpu_usage = get_cpu_usage()
    
    response = templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"instance_index": instance_index, "cpu_usage" : cpu_usage}
    )

    # Clear des headers
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    
    return response

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("static/images/cloud_foundry.png")


app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))

    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
