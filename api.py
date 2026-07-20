import os
import json
import cloudscraper
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

app = FastAPI(
    title="MovieBox API Pro",
    description="Full Pure REST API with ScraperAPI Integration",
    version="2.2.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# قراءة المفتاح من متغيرات البيئة في Railway[span_1](start_span)[span_1](end_span)
SCRAPER_API_KEY = os.getenv("SCRAPER_API_KEY")
API_BASE = "https://h5-api.aoneroom.com/wefeed-h5api-bff"
scraper = cloudscraper.create_scraper()

def _make_request(url: str, method: str = "POST", payload: dict = None) -> dict:
    """إجراء الطلب عبر ScraperAPI لتجاوز الحظر[span_2](start_span)[span_2](end_span)"""
    
    # دمج الرابط الأساسي مع مفتاح الـ API[span_3](start_span)[span_3](end_span)
    proxy_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={url}"
    
    headers = {
        "Content-Type": "application/json",
    }

    try:
        if method == "POST":
            # إرسال طلب POST مع البيانات[span_4](start_span)[span_4](end_span)
            resp = scraper.post(proxy_url, json=payload, headers=headers)
        else:
            # إرسال طلب GET[span_5](start_span)[span_5](end_span)
            resp = scraper.get(proxy_url, headers=headers)
        
        if resp.status_code != 200:
            raise HTTPException(status_code=502, detail=f"ScraperAPI failed with code: {resp.status_code}")
        
        return resp.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Request failed: {str(e)}")

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return "<h1>MovieBox API is Running with ScraperAPI</h1>"

@app.get("/searchResult")
async def search_result(keyword: str = Query(..., min_length=1), page: int = 1):
    url = f"{API_BASE}/subject/search"
    # استدعاء دالة الطلب[span_6](start_span)[span_6](end_span)
    return _make_request(url, method="POST", payload={"keyword": keyword, "page": page, "perPage": 20})

@app.get("/home")
def get_home():
    url = f"{API_BASE}/home?host=moviebox.ph"
    return _make_request(url, method="GET")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000)
