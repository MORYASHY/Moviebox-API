import logging
import uvicorn
from fastapi import FastAPI, Query
from curl_cffi.requests import AsyncSession

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="MovieBox API - Final Stable Match", version="5.2.0")

# --- الإعدادات ---
# (إذا توقف الكود عن العمل بعد فترة، قم بتحديث التوكن أدناه من متصفحك)
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1aWQiOjMxOTE5NDc4MzI2MDY0ODMwOTYsImF0cCI6MywiZXh0IjoiMTc4MzM4MTYwNCIsImV4cCI6MTc5MTE1NzYwNCwiaWF0IjoxNzgzMzgxMzA0fQ.gtrv_Cuu9MoPj9oqGOq7J5sMULLeV2HDwVjZ9t6jcEY"

COOKIES = {
    "token": TOKEN,
    "mb_token": f'"{TOKEN}"',
    "mb_guest_token": f'"{TOKEN}"'
}

HEADERS = {
    "accept": "application/json",
    "accept-language": "ar;q=0.8",
    "authorization": f"Bearer {TOKEN}",
    "x-client-info": '{"timezone":"Asia/Riyadh"}',
    "x-vip-restrict": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36",
    "sec-ch-ua": '"Not;A=Brand";v="8", "Chromium";v="150", "Brave";v="150"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin"
}

# جلسة تحاكي متصفح Chrome 110
session = AsyncSession(impersonate="chrome110")
API_BASE = "https://netfilm.world/wefeed-h5api-bff"

@app.get("/search")
async def search(q: str = Query(..., min_length=1), page: int = 1):
    url = f"{API_BASE}/subject/search"
    payload = {"keyword": q, "page": page, "perPage": 20}
    
    resp = await session.post(url, headers=HEADERS, cookies=COOKIES, json=payload)
    data = resp.json()
    
    inner = data.get("data", {})
    items = [{
        "name": sub.get("title"),
        "slug": sub.get("detailPath"),
        "subject_id": sub.get("subjectId")
    } for sub in (inner.get("items") or inner.get("list") or [])]
    
    return {"query": q, "total": inner.get("pager", {}).get("totalCount", 0), "items": items}

@app.get("/api/stream/{subject_id}")
async def get_stream_sources(subject_id: str, detail_path: str):
    # 1. بناء الرابط (params كما في الـ cURL الخاص بك)
    base_url = f"{API_BASE}/subject/play"
    params = {
        "subjectId": subject_id,
        "se": "0",
        "ep": "0",
        "detailPath": detail_path,
        "streamSignType": "1"
    }
    
    # 2. بناء الـ Referer (مطابق تماماً لـ cURL: فارغ للـ se و ep)
    referer = f"https://netfilm.world/spa/videoPlayPage/movies/{detail_path}?id={subject_id}&detailSe=&detailEp=&lang=en&type=%2Fmovie%2Fdetail"
    
    # 3. دمج الهيدرز
    current_headers = {**HEADERS, "referer": referer}
    
    # 4. إرسال الطلب
    resp = await session.get(base_url, headers=current_headers, cookies=COOKIES, params=params)
    
    logger.info(f"DEBUG: Status Code: {resp.status_code}")
    
    if resp.status_code == 200:
        return resp.json().get("data", {})
    else:
        logger.error(f"Failed with code {resp.status_code}: {resp.text}")
        return {"error": f"Failed with code {resp.status_code}", "raw": resp.text}

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000)
