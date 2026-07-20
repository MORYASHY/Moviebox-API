import json
import time
import cloudscraper
from fake_useragent import UserAgent
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

app = FastAPI(
    title="MovieBox API Pro",
    description="Full Pure REST API for moviebox.ph with Advanced Bypass",
    version="2.1.9"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

API_BASE = "https://h5-api.aoneroom.com/wefeed-h5api-bff"
scraper = cloudscraper.create_scraper()
ua = UserAgent()

def _get_headers():
    """توليد ترويسات عشوائية لكل طلب"""
    return {
        "User-Agent": ua.random,
        "Content-Type": "application/json",
        "Origin": "https://moviebox.ph",
        "Referer": "https://moviebox.ph/"
    }

def _make_request(url: str, method: str = "POST", payload: dict = None) -> dict:
    """إجراء الطلب مع تأخير، كوكيز، وتغيير دوري للـ User-Agent"""
    # 1. التأخير لتجنب الحظر
    time.sleep(1.5) 
    
    # 2. الحصول على كوكيز جديدة
    home_resp = scraper.get(f"{API_BASE}/home?host=moviebox.ph", headers=_get_headers())
    cookies = home_resp.cookies
    
    # 3. الحصول على توكن
    x_user = home_resp.headers.get("x-user")
    token = json.loads(x_user).get("token", "") if x_user else ""
    
    headers = _get_headers()
    headers["Authorization"] = f"Bearer {token}"

    try:
        if method == "POST":
            resp = scraper.post(url, json=payload, headers=headers, cookies=cookies)
        else:
            resp = scraper.get(url, headers=headers, cookies=cookies)
        
        if resp.status_code != 200:
            raise HTTPException(status_code=502, detail=f"Upstream API error: {resp.status_code}")
        
        return resp.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Request failed: {str(e)}")

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return "<h1>MovieBox API is Active with Advanced Anti-Ban</h1>"

@app.get("/searchResult")
async def search_result(keyword: str = Query(..., min_length=1), page: int = 1):
    url = f"{API_BASE}/subject/search"
    return _make_request(url, method="POST", payload={"keyword": keyword, "page": page, "perPage": 20})

@app.get("/home")
def get_home():
    url = f"{API_BASE}/home?host=moviebox.ph"
    return _make_request(url, method="GET")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
