import json
import cloudscraper
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

app = FastAPI(
    title="MovieBox API Pro",
    description="Full Pure REST API for moviebox.ph with Smart Auth",
    version="2.1.8"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

API_BASE = "https://h5-api.aoneroom.com/wefeed-h5api-bff"
scraper = cloudscraper.create_scraper()

def _get_token() -> str:
    """جلب التوكن اللازم للعمليات"""
    try:
        resp = scraper.get(f"{API_BASE}/home?host=moviebox.ph")
        x_user = resp.headers.get("x-user")
        if x_user:
            return json.loads(x_user).get("token", "")
        return ""
    except:
        return ""

def _make_request(url: str, method: str = "POST", payload: dict = None) -> dict:
    """إجراء طلب مع معالجة ذكية للتوكن ومحاولة ثانية عند فشل الطلب"""
    token = _get_token()
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
        "Origin": "https://moviebox.ph",
        "Referer": "https://moviebox.ph/"
    }

    try:
        # المحاولة الأولى
        if method == "POST":
            resp = scraper.post(url, json=payload, headers=headers)
        else:
            resp = scraper.get(url, headers=headers)
        
        # إذا فشل الطلب (400)، نحاول مرة أخرى بتوكن جديد
        if resp.status_code == 400:
            new_token = _get_token()
            headers["Authorization"] = f"Bearer {new_token}"
            if method == "POST":
                resp = scraper.post(url, json=payload, headers=headers)
            else:
                resp = scraper.get(url, headers=headers)

        if resp.status_code != 200:
            raise HTTPException(status_code=502, detail=f"Upstream API error: {resp.status_code}")
        
        return resp.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Request failed: {str(e)}")

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return "<h1>MovieBox API is Running and Stable</h1>"

@app.get("/searchResult")
async def search_result(keyword: str = Query(..., min_length=1), page: int = 1):
    url = f"{API_BASE}/subject/search"
    data = _make_request(url, method="POST", payload={"keyword": keyword, "page": page, "perPage": 20})
    return data

@app.get("/home")
def get_home():
    url = f"{API_BASE}/home?host=moviebox.ph"
    return _make_request(url, method="GET")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
