import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.api import DataAPI
from fastapi.staticfiles import StaticFiles

class App:
    def __init__(self):
        self.app = FastAPI()
        self.setup_middleware()
        self.app.mount("/public", StaticFiles(directory="public"), name="public")
        self.app.include_router(DataAPI().router)

    def setup_middleware(self):
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=[],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def get_app(self):
        return self.app

if __name__ == "__main__":
    uvicorn.run(App().get_app(), host="localhost", port=9000)