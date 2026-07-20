import re
import json
import cloudscraper
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

app = FastAPI(
    title="MovieBox API Pro",
    description="Full Pure REST API for moviebox.ph — Cloudflare Bypass Enabled",
    version="2.1.6"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

API_BASE = "https://h5-api.aoneroom.com/wefeed-h5api-bff"

# إنشاء كائن الـ scraper
scraper = cloudscraper.create_scraper()

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    "Referer": "https://moviebox.ph/",
    "Origin": "https://moviebox.ph",
    "Accept": "application/json",
    "Content-Type": "application/json",
}

def _make_request(url: str, method: str = "GET", payload: dict = None) -> dict:
    """إجراء الطلبات باستخدام cloudscraper لتجاوز حماية Cloudflare"""
    try:
        if method == "POST":
            resp = scraper.post(url, json=payload, headers=DEFAULT_HEADERS)
        else:
            resp = scraper.get(url, headers=DEFAULT_HEADERS)

        if resp.status_code != 200:
            raise HTTPException(status_code=502, detail=f"Upstream API error: {resp.status_code}")

        return resp.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Request failed: {str(e)}")

# ملاحظة: تم تعديل المسار والمعاملات لتطابق الموقع الأصلي كما طلبت
@app.post("/searchResult")
async def search_result(keyword: str = Query(..., min_length=1), page: int = 1):
    url = f"{API_BASE}/subject/search"
    data = _make_request(url, method="POST", payload={"keyword": keyword, "page": page, "perPage": 20})
    return data

# باقي المسارات (home, detail, stream) يجب تعديلها لتستخدم دالة _make_request الجديدة بدون await
# مثال لمسار home:
@app.get("/home")
def get_home():
    url = f"{API_BASE}/home?host=moviebox.ph"
    return _make_request(url)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
