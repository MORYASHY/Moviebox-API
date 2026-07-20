from fastapi import FastAPI, Query
from moviebox_api import MovieBox # استيراد المكتبة

app = FastAPI()
# تهيئة المكتبة
client = MovieBox()

@app.get("/searchResult")
async def search(keyword: str = Query(..., min_length=1), page: int = 1):
    try:
        # استخدام دالة البحث الجاهزة من المكتبة
        results = client.search(keyword, page=page)
        return results
    except Exception as e:
        return {"error": str(e)}

@app.get("/")
async def root():
    return {"status": "MovieBox API using library is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
