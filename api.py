import logging
import uvicorn
from fastapi import FastAPI
from curl_cffi.requests import AsyncSession

# إعداد السجلات
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="MovieBox API - Native Android Emulation", version="4.2.0")

# الهيدرز التي نجحت في اختبارك اليدوي
ANDROID_HEADERS = {
    "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 14; TECNO LH8n Build/UP1A.231005.007)",
    "Connection": "Keep-Alive",
    "Accept-Encoding": "identity",
    "Referer": "http://moviebox.ph/"
}

# جلسة تحاكي المتصفح لضمان توافق TLS
session = AsyncSession(impersonate="chrome110")

API_BASE = "https://h5-api.aoneroom.com/wefeed-h5api-bff"

@app.get("/api/stream/{subject_id}")
async def get_stream_sources(subject_id: str, detail_path: str, se: int = 1, ep: int = 1):
    # 1. جلب الدومين (باستخدام هيدرز الأندرويد)
    try:
        dom_resp = await session.get(f"{API_BASE}/media-player/get-domain", headers=ANDROID_HEADERS)
        domain = dom_resp.json().get("data", "https://netfilm.world").rstrip("/")
    except Exception as e:
        return {"error": "Failed to get domain", "details": str(e)}
    
    # 2. بناء رابط الـ Play
    play_url = f"{domain}/wefeed-h5api-bff/subject/play?subjectId={subject_id}&se={se}&ep={ep}&detailPath={detail_path}&streamSignType=1"
    
    # 3. طلب الرابط بـ هيدرز الأندرويد
    resp = await session.get(play_url, headers=ANDROID_HEADERS)
    
    # 4. تسجيل الرد الكامل (لنرى إذا كانت الروابط أو الكوكيز موجودة)
    logger.info(f"DEBUG: Full API Response: {resp.text}")
    
    # 5. محاولة إرجاع البيانات
    try:
        return resp.json().get("data", {})
    except:
        return {"error": "Invalid Response", "raw": resp.text}

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000)
