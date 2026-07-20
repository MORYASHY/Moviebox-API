import json
import asyncio
import cloudscraper  # المكتبة الجديدة لتجاوز الحماية
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

# إنشاء مكرر السكرابر (Scraper)
scraper = cloudscraper.create_scraper()

def _make_request(url: str, method: str = "GET", payload: dict = None) -> dict:
    """إجراء طلب عبر cloudscraper لتجاوز الحماية"""
    try:
        # إضافة تأخير لتجنب الحظر
        # ملاحظة: cloudscraper يعمل بشكل متزامن (synchronous)
        if method == "POST":
            resp = scraper.post(url, json=payload)
        else:
            resp = scraper.get(url)
        
        if resp.status_code != 200:
            raise HTTPException(status_code=502, detail=f"Upstream API error: {resp.status_code}")
        
        return resp.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Request failed: {str(e)}")

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return "<h1>MovieBox API is Running with Cloudflare Bypass</h1>"

@app.get("/searchResult")
async def search_result(keyword: str = Query(..., min_length=1), page: int = 1):
    url = f"{API_BASE}/subject/search"
    # استدعاء دالة الطلب
    data = _make_request(url, method="POST", payload={"keyword": keyword, "page": page, "perPage": 20})
    return data

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
