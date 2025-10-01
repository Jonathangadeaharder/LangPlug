#!/usr/bin/env python3
"""
Live API probe without GUI (stdlib only):
- Checks /health
- Logs in as admin/admin
- Starts /process/chunk for Superstore episode (0-600s)
- Polls /process/progress until completed or timeout
- Fetches subtitles via /videos/subtitles
- Writes a detailed report to Backend/logs/live_api_probe_report.txt
"""

import contextlib
import datetime as dt
import json
import time
from pathlib import Path
from urllib import request as urlreq
from urllib.parse import quote

BASE = "http://localhost:8000"
REPORT_PATH = Path(__file__).parent.parent / "logs" / "live_api_probe_report.txt"
LOG_PATH = Path(__file__).parent.parent / "logs" / f"langplug-backend-{dt.datetime.now().strftime('%Y-%m-%d')}.log"

# Adjust this to the actual Superstore episode filename you have
VIDEO_REL = r"Superstore\Episode 1 Staffel 1 von Superstore S to - Serien Online gratis a.mp4"
CHUNK_START = 0
CHUNK_END = 600


def write_line(f, line: str):
    with contextlib.suppress(Exception):
        pass
    f.write(line + "\n")
    f.flush()  # Ensure immediate write to disk


def http_get(path: str, headers: dict | None = None, timeout: int = 10):
    req = urlreq.Request(BASE + path, method="GET")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    with urlreq.urlopen(req, timeout=timeout) as resp:
        return resp.getcode(), resp.read().decode("utf-8", errors="replace")


def http_post_json(path: str, payload: dict, headers: dict | None = None, timeout: int = 15):
    data = json.dumps(payload).encode("utf-8")
    req = urlreq.Request(BASE + path, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    with urlreq.urlopen(req, timeout=timeout) as resp:
        text = resp.read().decode("utf-8", errors="replace")
        return resp.getcode(), text


def main():
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with REPORT_PATH.open("w", encoding="utf-8") as f:
        write_line(f, "Live API Probe - LangPlug Backend")
        write_line(f, f"Timestamp: {dt.datetime.now().isoformat()}")
        write_line(f, "")

        # Health
        try:
            code, text = http_get("/health", timeout=5)
            write_line(f, f"/health status: {code}")
            write_line(f, f"/health body: {text}")
        except Exception as e:
            write_line(f, f"/health request failed: {e}")
            return

        # Login admin/admin
        headers = {}
        try:
            code, text = http_post_json("/auth/login", {"username": "admin", "password": "admin"})
            write_line(f, f"/auth/login status: {code}")
            if code < 200 or code >= 300:
                write_line(f, f"Login failed body: {text}")
                return
            data = json.loads(text)
            token = data.get("token")
            headers = {"Authorization": f"Bearer {token}"}
        except Exception as e:
            write_line(f, f"Login error: {e}")
            return

        # Start chunk task
        try:
            payload = {"video_path": VIDEO_REL, "start_time": CHUNK_START, "end_time": CHUNK_END}
            code, text = http_post_json("/process/chunk", payload, headers=headers)
            write_line(f, f"/process/chunk status: {code}")
            if code < 200 or code >= 300:
                write_line(f, f"Chunk start error body: {text}")
                return
            task_id = json.loads(text).get("task_id")
            write_line(f, f"Task ID: {task_id}")
        except Exception as e:
            write_line(f, f"Chunk start exception: {e}")
            return

        # Poll progress
        status = None
        for i in range(60):  # ~60 * 1s = 60s
            time.sleep(1)
            try:
                code, text = http_get(f"/process/progress/{task_id}", headers=headers)
                write_line(f, f"Progress poll {i + 1}: {code}")
                data = json.loads(text)
                status = data.get("status")
                write_line(f, f"status={status}, progress={data.get('progress')}, step={data.get('current_step')}")
                if data.get("subtitle_path"):
                    write_line(f, f"subtitle_path: {data.get('subtitle_path')}")
                if data.get("translation_path"):
                    write_line(f, f"translation_path: {data.get('translation_path')}")
                if status == "completed":
                    break
            except Exception as e:
                write_line(f, f"Progress request failed: {e}")
        if status != "completed":
            write_line(f, "Task did not complete within timeout.")
            return

        # Build chunk subtitle relative path and fetch via API
        chunk_rel = VIDEO_REL.replace(".mp4", f"_chunk_{CHUNK_START}_{CHUNK_END}.srt").replace("\\", "/")
        sub_url = f"/videos/subtitles/{quote(chunk_rel, safe='')}"
        try:
            code, text = http_get(sub_url, headers=headers)
            write_line(f, f"GET subtitles status: {code}")
            write_line(f, f"Subtitle length (chars): {len(text)}")
            write_line(f, "First 200 chars:")
            write_line(f, text[:200].replace("\n", "\\n"))
        except Exception as e:
            write_line(f, f"Subtitle fetch error: {e}")

        # Double-check file on disk
        videos_root = Path(__file__).parent.parent.parent / "videos"
        disk_path = videos_root / chunk_rel
        write_line(f, f"Disk path: {disk_path}")
        if disk_path.exists():
            size = disk_path.stat().st_size
            write_line(f, f"Disk file exists, size={size} bytes")
            if size:
                try:
                    snippet = disk_path.read_text(encoding="utf-8", errors="replace")[:200]
                    escaped_snippet = snippet.replace("\n", "\\n")
                    write_line(f, f"Disk first 200 chars: {escaped_snippet}")
                except Exception as e:
                    write_line(f, f"Disk read error: {e}")
        else:
            write_line(f, "Disk file does not exist")

        # Tail CHUNK DEBUG lines from backend log (if present)
        write_line(f, "")
        write_line(f, f"Inspecting backend log: {LOG_PATH}")
        if LOG_PATH.exists():
            try:
                lines = LOG_PATH.read_text(encoding="utf-8", errors="replace").splitlines()
                ch = [ln for ln in lines if "[CHUNK DEBUG]" in ln or "[CHUNK PROCESSING" in ln]
                write_line(f, f"Found {len(ch)} CHUNK-related log lines")
                for ln in ch[-50:]:
                    write_line(f, ln)
            except Exception as e:
                write_line(f, f"Log read error: {e}")
        else:
            write_line(f, "Backend log file not found")


if __name__ == "__main__":
    main()
