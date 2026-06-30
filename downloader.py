import os
import queue
import threading
import re
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Dict
from PyQt6.QtCore import QThread, pyqtSignal
import yt_dlp


def _parse_speed(speed_bytes):
    if speed_bytes is None:
        return ""
    if speed_bytes >= 1024 * 1024:
        return f"{speed_bytes / (1024 * 1024):.1f} MB/s"
    elif speed_bytes >= 1024:
        return f"{speed_bytes / 1024:.1f} KB/s"
    return f"{int(speed_bytes)} B/s"


class DownloadManager(QThread):
    progress_signal = pyqtSignal(str, float)
    done_signal = pyqtSignal(str)
    speed_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()
        self._queue = queue.Queue()
        self._stop_event = threading.Event()
        self._max_workers = 3
        self._executor: ThreadPoolExecutor = None
        self._active_futures: Dict[str, Future] = {}
        self._lock = threading.Lock()

    def set_max_workers(self, n: int):
        self._max_workers = max(1, min(8, n))

    def add_download(self, info: dict, output_path: str):
        self._queue.put((info, output_path))

    def stop(self):
        self._stop_event.set()
        self._queue.put(None)
        if self._executor:
            self._executor.shutdown(wait=False, cancel_futures=True)

    def run(self):
        self._executor = ThreadPoolExecutor(max_workers=self._max_workers)
        while not self._stop_event.is_set():
            try:
                item = self._queue.get(timeout=1)
            except queue.Empty:
                if self._max_workers != self._executor._max_workers:
                    self._executor.shutdown(wait=False)
                    self._executor = ThreadPoolExecutor(max_workers=self._max_workers)
                continue

            if item is None:
                break

            info, output_path = item
            video_id = info.get("id", "unknown")

            if self._max_workers != self._executor._max_workers:
                self._executor.shutdown(wait=False)
                self._executor = ThreadPoolExecutor(max_workers=self._max_workers)

            future = self._executor.submit(self._download_one, info, output_path)
            with self._lock:
                self._active_futures[video_id] = future

        self._executor.shutdown(wait=True)

    def _download_one(self, info: dict, output_path: str):
        video_id = info.get("id", "unknown")
        url = info.get("webpage_url") or info.get("url") or info.get("original_url", "")

        if not url:
            self.error_signal.emit(video_id, "لا يوجد رابط للتحميل")
            return

        os.makedirs(output_path, exist_ok=True)

        def progress_hook(d):
            if d["status"] == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
                downloaded = d.get("downloaded_bytes", 0)
                speed = d.get("speed")
                if total and total > 0:
                    pct = (downloaded / total) * 100
                    self.progress_signal.emit(video_id, pct)
                if speed:
                    self.speed_signal.emit(_parse_speed(speed))
            elif d["status"] == "finished":
                self.progress_signal.emit(video_id, 100.0)

        ydl_opts = {
            "outtmpl": os.path.join(output_path, "%(title)s.%(ext)s"),
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best",
            "merge_output_format": "mp4",
            "concurrent_fragment_downloads": 8,
            "progress_hooks": [progress_hook],
            "ignoreerrors": True,
            "continuedl": True,
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "retries": 5,
            "fragment_retries": 10,
        }

        aria2c_path = self._find_aria2c()
        if aria2c_path:
            ydl_opts["external_downloader"] = aria2c_path
            ydl_opts["external_downloader_args"] = {
                "aria2c": ["-x16", "-s16", "-k1M", "--file-allocation=none",
                           "--optimize-concurrent-downloads=true",
                           "--auto-file-renaming=false"]
            }

        ffmpeg_path = self._find_ffmpeg()
        if ffmpeg_path:
            ydl_opts["ffmpeg_location"] = ffmpeg_path

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            self.done_signal.emit(video_id)
        except yt_dlp.utils.DownloadError as e:
            msg = str(e)
            msg = re.sub(r"\x1b\[[0-9;]*m", "", msg)
            self.error_signal.emit(video_id, msg[:120])
        except Exception as e:
            self.error_signal.emit(video_id, str(e)[:120])

    @staticmethod
    def _find_aria2c():
        candidates = [
            "aria2c",
            r"C:\ProgramData\chocolatey\bin\aria2c.exe",
            r"C:\Program Files\aria2\aria2c.exe",
            os.path.join(os.path.expanduser("~"), "aria2", "aria2c.exe"),
        ]
        import shutil
        for c in candidates:
            if shutil.which(c):
                return c
        return None

    @staticmethod
    def _find_ffmpeg():
        import shutil
        candidates = [
            "ffmpeg",
            r"C:\ProgramData\chocolatey\bin\ffmpeg.exe",
            r"C:\ffmpeg\bin\ffmpeg.exe",
            os.path.join(os.path.expanduser("~"), "ffmpeg", "bin", "ffmpeg.exe"),
        ]
        for c in candidates:
            if shutil.which(c):
                return c
        return None
