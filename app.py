import requests, re, os, json
from flask import Flask, Response, request
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

RAPIDAPI_URL = "https://yt-api.p.rapidapi.com/dl"
RAPIDAPI_HEADERS = {
    "accept": "application/json",
    "origin": "https://www.ytsavepro.com",
    "referer": "https://www.ytsavepro.com/",
    "sec-ch-ua": '"Microsoft Edge";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
    "sec-ch-ua-mobile": "?1",
    "sec-ch-ua-platform": '"Android"',
    "user-agent": "Mozilla/5.0 (Linux; Android 8.0.0; SM-G955U) AppleWebKit/537.36 Chrome/137.0.0.0 Mobile Safari/537.36 Edg/137.0.0.0",
    "x-rapidapi-host": "yt-api.p.rapidapi.com",
    "x-rapidapi-key": os.environ.get("X")
}

def extract_video_id(url):
    patterns = [
        r"(?:youtu\.be/)([^&\n?#]+)",
        r"(?:v=)([^&\n?#]+)"
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

@app.route('/')
def home():
    return Response(json.dumps({
        "developer_info": "Dev: S4NCHITT.t.me",
        "message": "Use /api?url=https://youtube.com/watch?v=...",
        "example": "/api?url=https://youtu.be/BWczaSneA0Q"
    }, indent=2), mimetype='application/json')

@app.route('/api')
def get_info():
    res = {"developer_info": "Dev: S4NCHITT.t.me"}
    full_url = request.args.get("url")
    video_id = extract_video_id(full_url) if full_url else None
    if not video_id:
        res.update({"status": "error", "message": "Missing or invalid YouTube URL."})
        return Response(json.dumps(res, indent=2), mimetype='application/json', status=400)

    try:
        r = requests.get(RAPIDAPI_URL, headers=RAPIDAPI_HEADERS, params={"id": video_id})
        r.raise_for_status()
        data = r.json()

        res.update({
            "message": "Video information found.",
            "status": "success",
            "video_info": {
                "id": data.get("id"),
                "title": data.get("title"),
                "channelTitle": data.get("channelTitle"),
                "lengthSeconds": data.get("lengthSeconds"),
                "viewCount": data.get("viewCount"),
                "largestThumbnailUrl": max(data.get("thumbnail", []), key=lambda x: x.get("width", 0), default={}).get("url")
            }
        })

        vids, auds = [], []

        def add(fmt_list, fmt, typ):
            urls = {f['url'] for f in fmt_list}
            if fmt.get("url") and fmt["url"] not in urls:
                fmt_list.append({
                    "type": typ,
                    "qualityLabel": fmt.get("qualityLabel", "N/A"),
                    "audioQuality": fmt.get("audioQuality", "N/A"),
                    "mimeType": fmt.get("mimeType", "N/A"),
                    "url": fmt["url"],
                    "contentLength": fmt.get("contentLength")
                })

        for fmt in data.get("formats", []):
            mt = fmt.get("mimeType", "")
            if mt.startswith("video/"): add(vids, fmt, "combined")
            elif mt.startswith("audio/"): add(auds, fmt, "audio-only")

        for fmt in data.get("adaptiveFormats", []):
            mt = fmt.get("mimeType", "")
            if mt.startswith("video/") and "qualityLabel" in fmt: add(vids, fmt, "video-only")
            elif mt.startswith("audio/") and "audioQuality" in fmt: add(auds, fmt, "audio-only")

        vids.sort(
            key=lambda f: int(re.search(r"\d+", f.get("qualityLabel", "0")).group()) if f.get("qualityLabel") else 0,
            reverse=True
        )
        auds.sort(key=lambda f: f.get("audioQuality", ""), reverse=True)

        res["formats"] = {"video_streams": vids, "audio_streams": auds}
        return Response(json.dumps(res, indent=2), mimetype='application/json')

    except Exception as e:
        res.update({"status": "error", "message": str(e)})
        return Response(json.dumps(res, indent=2), mimetype='application/json', status=500)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7860)
