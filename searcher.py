import yt_dlp
from PyQt6.QtCore import QThread, pyqtSignal


class SearchWorker(QThread):
    result_ready = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, query: str):
        super().__init__()
        self.query = query.strip()

    def run(self):
        try:
            results = self._fetch(self.query)
            self.result_ready.emit(results)
        except Exception as e:
            self.error.emit(str(e)[:200])

    def _fetch(self, query: str) -> list:
        is_url = query.startswith("http://") or query.startswith("https://")

        flat_opts = {
            "quiet": True,
            "no_warnings": True,
            "ignoreerrors": True,
            "extract_flat": True,
            "skip_download": True,
            "playlist_items": "1:50",
        }

        meta_opts = {
            "quiet": True,
            "no_warnings": True,
            "ignoreerrors": True,
            "skip_download": True,
            "noplaylist": True,
        }

        if is_url:
            with yt_dlp.YoutubeDL(flat_opts) as ydl:
                data = ydl.extract_info(query, download=False)

            if data is None:
                return []

            if data.get("_type") == "playlist" or "entries" in data:
                entries = list(data.get("entries") or [])
                results = []
                for e in entries:
                    if not e:
                        continue
                    results.append({
                        "id": e.get("id", ""),
                        "title": e.get("title") or e.get("id", "بدون عنوان"),
                        "duration": e.get("duration", 0),
                        "thumbnail": e.get("thumbnail") or self._pick_thumb(e),
                        "uploader": e.get("uploader") or e.get("channel", ""),
                        "webpage_url": e.get("url") or e.get("webpage_url", ""),
                        "url": e.get("url", ""),
                    })
                return results

            return [self._normalize(data)]

        else:
            search_url = f"ytsearch15:{query}"
            with yt_dlp.YoutubeDL(flat_opts) as ydl:
                data = ydl.extract_info(search_url, download=False)

            if not data or not data.get("entries"):
                return []

            results = []
            for e in data["entries"]:
                if not e:
                    continue
                results.append({
                    "id": e.get("id", ""),
                    "title": e.get("title") or e.get("id", "بدون عنوان"),
                    "duration": e.get("duration", 0),
                    "thumbnail": e.get("thumbnail") or self._pick_thumb(e),
                    "uploader": e.get("uploader") or e.get("channel", ""),
                    "webpage_url": f"https://www.youtube.com/watch?v={e.get('id', '')}",
                    "url": e.get("url", ""),
                })
            return results

    def _normalize(self, data: dict) -> dict:
        return {
            "id": data.get("id", ""),
            "title": data.get("title") or "بدون عنوان",
            "duration": data.get("duration", 0),
            "thumbnail": data.get("thumbnail") or self._pick_thumb(data),
            "uploader": data.get("uploader") or data.get("channel", ""),
            "webpage_url": data.get("webpage_url") or data.get("url", ""),
            "url": data.get("url", ""),
        }

    @staticmethod
    def _pick_thumb(entry: dict) -> str:
        thumbnails = entry.get("thumbnails") or []
        if thumbnails:
            for t in reversed(thumbnails):
                url = t.get("url", "")
                if url:
                    return url
        vid_id = entry.get("id", "")
        if vid_id:
            return f"https://i.ytimg.com/vi/{vid_id}/mqdefault.jpg"
        return ""
