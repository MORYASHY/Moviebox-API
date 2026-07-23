import re
import json
import httpx
import logging
import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

# إعداد السجلات
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="MovieBox API Pro - Test Without Auth", version="3.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

API_BASE = "https://h5-api.aoneroom.com/wefeed-h5api-bff"

# عميل مشترك (Persistent Session) للاحتفاظ بالكوكيز والجلسة
client = httpx.AsyncClient(timeout=25, follow_redirects=True)

_bearer_token: str | None = None

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 14; TECNO LH8n Build/UP1A.231005.007; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/151.0.7922.47 Mobile Safari/537.36",
    "Referer": "http://moviebox.ph/",
    "X-Client-Info": '{"timezone":"Asia/Riyadh"}',
    "X-Request-Lang": "en",
    "Accept": "application/json",
    "Content-Type": "application/json",
}

async def _get_bearer_token() -> str:
    global _bearer_token
    if _bearer_token: return _bearer_token
    try:
        resp = await client.get(f"{API_BASE}/home?host=moviebox.ph", headers=DEFAULT_HEADERS)
        x_user = resp.headers.get("x-user")
        if x_user: _bearer_token = json.loads(x_user).get("token")
    except Exception as e:
        logger.error(f"Error fetching token: {e}")
    return _bearer_token or ""

@app.get("/search")
async def search(q: str = Query(..., min_length=1), page: int = 1):
    url = f"{API_BASE}/subject/search"
    payload = {"keyword": q, "page": page, "perPage": 20}
    token = await _get_bearer_token()
    headers = {**DEFAULT_HEADERS, "Authorization": f"Bearer {token}"}
    
    resp = await client.post(url, headers=headers, json=payload)
    data = resp.json()
    inner = data.get("data", {})
    items = [{
        "name": sub.get("title"),
        "slug": sub.get("detailPath"),
        "subject_id": sub.get("subjectId")
    } for sub in (inner.get("items") or inner.get("list") or [])]
    return {"query": q, "total": inner.get("pager", {}).get("totalCount", 0), "items": items}

@app.get("/api/stream/{subject_id}")
async def get_stream_sources(subject_id: str, detail_path: str, se: int = 1, ep: int = 1):
    # 1. جلب الدومين
    dom_resp = await client.get(f"{API_BASE}/media-player/get-domain", headers=DEFAULT_HEADERS)
    domain = dom_resp.json().get("data", "https://netfilm.world").rstrip("/")
    
    # 2. بناء الروابط
    player_referer = (
        f"{domain}/spa/videoPlayPage/movies/{detail_path}"
        f"?id={subject_id}&detailSe={se}&detailEp={ep}&lang=en&type=%2Fmovie%2Fdetail&page_from=search_detail"
    )
    play_url = f"{domain}/wefeed-h5api-bff/subject/play?subjectId={subject_id}&se={se}&ep={ep}&detailPath={detail_path}&streamSignType=1"
    
    # 3. خطوة الـ Warm-up: زيارة صفحة المشغل أولاً لتعيين الكوكيز
    await client.get(player_referer, headers=DEFAULT_HEADERS)
    
    # 4. بناء الهيدرز بدون التوكن (للتحقق من فرضية التعارض) + إضافة Origin
    headers = {
        **DEFAULT_HEADERS,
        "Referer": player_referer,
        "Origin": "https://netfilm.world",
        "Prefers-Color-Scheme": "dark",
        "X-Source": ""
    }
    
    # 5. الطلب
    resp = await client.get(play_url, headers=headers)
    
    logger.info(f"DEBUG: Status Code (No Auth): {resp.status_code}")
    
    if resp.status_code != 200:
        return {"error": "Blocked", "status_code": resp.status_code, "msg": "Request still denied"}
            
    return resp.json().get("data", {})

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000)
