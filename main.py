from time import time
from fastapi import FastAPI, __version__
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

html = f"""
<!DOCTYPE html>
<html>
    <head>
        <title>FastAPI on Vercel</title>
        <link rel="icon" href="/static/favicon.ico" type="image/x-icon" />
    </head>
    <body>
        <div class="bg-gray-200 p-4 rounded-lg shadow-lg">
            <h1>Hello from FastAPI@{__version__}</h1>
            <ul>
                <li><a href="/docs">/docs</a></li>
                <li><a href="/redoc">/redoc</a></li>
            </ul>
            <p>Powered by <a href="https://vercel.com" target="_blank">Vercel</a></p>
        </div>
    </body>
</html>
"""



# Example data storage (simulated in-memory database)
fake_items_db = [
    {"item_id": "1", "name": "Item One"},
    {"item_id": "2", "name": "Item Two"},
]

# Define a Pydantic model for item creation
class Item(BaseModel):
    name: str
    description: str = None

# GET endpoint to retrieve all items
@app.get("/items/")
async def read_items():
    return fake_items_db

# GET endpoint to retrieve a specific item by ID
@app.get("/items/{item_id}")
async def read_item(item_id: str):
    for item in fake_items_db:
        if item["item_id"] == item_id:
            return item
    raise HTTPException(status_code=404, detail="Item not found")

# POST endpoint to create a new item
@app.post("/items/")
async def create_item(item: Item):
    new_item = {"item_id": str(len(fake_items_db) + 1), **item.dict()}
    fake_items_db.append(new_item)
    return new_item

# PUT endpoint to update an existing item by ID
@app.put("/items/{item_id}")
async def update_item(item_id: str, item: Item):
    for i, db_item in enumerate(fake_items_db):
        if db_item["item_id"] == item_id:
            fake_items_db[i] = {"item_id": item_id, **item.dict()}
            return {"message": "Item updated successfully"}
    raise HTTPException(status_code=404, detail="Item not found")

# DELETE endpoint to delete an item by ID
@app.delete("/items/{item_id}")
async def delete_item(item_id: str):
    for i, db_item in enumerate(fake_items_db):
        if db_item["item_id"] == item_id:
            del fake_items_db[i]
            return {"message": "Item deleted successfully"}
    raise HTTPException(status_code=404, detail="Item not found")

# Example of a query parameter endpoint
@app.get("/items_by_name/")
async def read_item_by_name(name: str = Query(..., min_length=3, max_length=50)):
    result = [item for item in fake_items_db if name.lower() in item["name"].lower()]
    return result


@app.get('/ping')
async def hello():
    return {'res': 'pong', 'version': __version__, "time": time()}


class IntroductionRequest(BaseModel):
    subtopic: str
    keywords: str
    summary: str

@app.post("/generate_introduction/")
async def generate_introduction(request: IntroductionRequest):
    introduction = f"{request.subtopic}에 대한 소개\n\n"
    introduction += f"키워드: {request.keywords}\n\n"
    introduction += f"{request.summary}"
    
    return {"introduction": introduction}



# @app.get("/")
# async def root():
#     return HTMLResponse(html)
 