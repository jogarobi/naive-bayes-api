from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def read_root():
    return {"message": "Hello World!"}


@app.get("/message/{id}")
async def read_item(id):
    return {"message": f"Your message ID is {id}"}
