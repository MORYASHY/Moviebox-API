import re
import json
import httpx
import logging
import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

# إعداد السجلات (Logging)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="MovieBox API Pro",
    description="Full Pure REST API for moviebox.ph — Debugging Enabled",
    version="2.5.0"
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

API_BASE = "https://h5-api.aoneroom.com/wefeed-h5api-bff"
_bearer_token: str | None = None

# الهيدرز الأساسية المحدثة
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 14; TECNO LH8n Build/UP1A.231005.007; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/151.0.7922.47 Mobile Safari/537.36",
    "Referer": "http://moviebox.ph/",
    "X-Client-Info": '{"timezone":"Asia/Riyadh"}',
    "X-Request-Lang": "en",
    "Accept": "application/json",
    "Content-Type": "application/json",
}

PLAYER_HEADERS = {
    **DEFAULT_HEADERS,
    "sec-fetch-site": "same-origin",
    "Prefers-Color-Scheme": "dark",
    "X-Source": ""
}

async def _get_bearer_token() -> str:
    global _bearer_token
    if _bearer_token:
        return _bearer_token
    
    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.get(f"{API_BASE}/home?host=moviebox.ph", headers=DEFAULT_HEADERS)
            x_user = resp.headers.get("x-user")
            if x_user:
                _bearer_token = json.loads(x_user).get("token")
            else:
                cookie = resp.headers.get("set-cookie", "")
                m = re.search(r"token=([^;]+)", cookie)
                if m:
                    _bearer_token = m.group(1)
        except Exception as e:
            logger.error(f"Error fetching token: {e}")
    return _bearer_token or ""

async def _make_request(url: str, method: str = "GET", payload: dict = None) -> dict:
    token = await _get_bearer_token()
    headers = {**DEFAULT_HEADERS, "Authorization": f"Bearer {token}" if token else ""}
    
    async with httpx.AsyncClient(timeout=25) as client:
        try:
            if method == "POST":
                resp = await client.post(url, headers=headers, json=payload)
            else:
                resp = await client.get(url, headers=headers)
            
            if resp.status_code != 200:
                logger.error(f"Upstream Error {resp.status_code}: {resp.text}")
                raise HTTPException(status_code=502, detail="Upstream API error")
            
            return resp.json()
        except Exception as e:
            logger.error(f"Request failed: {e}")
            raise HTTPException(status_code=502, detail=str(e))

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return HTMLResponse(content="<h1>MovieBox API Pro - Debugging Mode</h1>")

@app.get("/search")
async def search(q: str = Query(..., min_length=1), page: int = 1):
    url = f"{API_BASE}/subject/search"
    payload = {"keyword": q, "page": page, "perPage": 20}
    data = await _make_request(url, method="POST", payload=payload)
    
    inner = data.get("data", {})
    items = [{
        "name": sub.get("title"),
        "slug": sub.get("detailPath"),
        "subject_id": sub.get("subjectId")
    } for sub in (inner.get("items") or inner.get("list") or [])]
    
    return {"query": q, "total": inner.get("pager", {}).get("totalCount", 0), "items": items}

@app.get("/api/stream/{subject_id}")
async def get_stream_sources(subject_id: str, detail_path: str, se: int = 1, ep: int = 1):
    dom_data = await _make_request(f"{API_BASE}/media-player/get-domain")
    domain = dom_data.get("data", "https://netfilm.world").rstrip("/")
    
    # 1. جلب التوكن الحالي لضمان إرساله مع طلب البث[span_1](start_span)[span_1](end_span)
    token = await _get_bearer_token()
    
    # 2. بناء Referer مطابق تماماً للطلب الناجح[span_2](start_span)[span_2](end_span)
    player_referer = (
        f"{domain}/spa/videoPlayPage/movies/{detail_path}"
        f"?id={subject_id}&detailSe={se}&detailEp={ep}&lang=en&type=%2Fmovie%2Fdetail&page_from=home_Trending+Drama"
    )
    
    # 3. بناء رابط الطلب مع المعامل الضروري streamSignType[span_3](start_span)[span_3](end_span)
    play_url = f"{domain}/wefeed-h5api-bff/subject/play?subjectId={subject_id}&se={se}&ep={ep}&detailPath={detail_path}&streamSignType=1"
    
    # 4. دمج التوكن مع الهيدرز للتحقق من المصادقة[span_4](start_span)[span_4](end_span)
    headers = {
        **PLAYER_HEADERS, 
        "Referer": player_referer,
        "Authorization": f"Bearer {token}"
    }
    
    async with httpx.AsyncClient(timeout=25) as client:
        resp = await client.get(play_url, headers=headers)
        
        # تسجيل الحالة والرد[span_5](start_span)[span_5](end_span)
        logger.info(f"DEBUG: URL Called: {play_url}")
        logger.info(f"DEBUG: Status Code: {resp.status_code}")
        
        if resp.status_code != 200:
            return {"error": "Blocked", "status_code": resp.status_code, "msg": "Request denied by server"}
            
        return resp.json().get("data", {})

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
