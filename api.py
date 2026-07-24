import logging
import uvicorn
from fastapi import FastAPI
from curl_cffi.requests import AsyncSession

# إعداد السجلات
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="MovieBox API - Final Fix", version="4.3.0")

# الهيدرز التي أثبتت نجاحها
ANDROID_HEADERS = {
    "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 14; TECNO LH8n Build/UP1A.231005.007)",
    "Connection": "Keep-Alive",
    "Accept-Encoding": "identity",
    "Referer": "http://moviebox.ph/"
}

# جلسة تحاكي متصفح Chrome لضمان TLS Handshake صحيح
session = AsyncSession(impersonate="chrome110")

API_BASE = "https://h5-api.aoneroom.com/wefeed-h5api-bff"

@app.get("/api/stream/{subject_id}")
async def get_stream_sources(subject_id: str, detail_path: str, se: str = "1", ep: str = "1"):
    # 1. جلب الدومين
    try:
        dom_resp = await session.get(f"{API_BASE}/media-player/get-domain", headers=ANDROID_HEADERS)
        domain = dom_resp.json().get("data", "https://netfilm.world").rstrip("/")
    except Exception as e:
        return {"error": "Domain fetch failed", "details": str(e)}
    
    # 2. بناء الروابط بدقة
    # ملاحظة: تم دمج المعاملات داخل الرابط لضمان التوافق مع السيرفر
    play_url = f"{domain}/wefeed-h5api-bff/subject/play"
    params = {
        "subjectId": subject_id,
        "se": se,
        "ep": ep,
        "detailPath": detail_path,
        "streamSignType": "1"
    }
    
    # 3. خطوة الـ Warm-up (زيارة صفحة المشغل)
    player_referer = f"{domain}/spa/videoPlayPage/movies/{detail_path}?id={subject_id}&page_from=search_detail"
    await session.get(player_referer, headers=ANDROID_HEADERS)
    
    # 4. الطلب الفعلي
    headers = {**ANDROID_HEADERS, "Referer": player_referer, "Origin": "https://netfilm.world"}
    resp = await session.get(play_url, headers=headers, params=params)
    
    logger.info(f"DEBUG: Final URL: {resp.url}")
    logger.info(f"DEBUG: API Response: {resp.text}")
    
    # 5. إرجاع النتيجة
    try:
        return resp.json().get("data", {})
    except:
        return {"error": "Invalid JSON response from server", "raw": resp.text}

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000)
