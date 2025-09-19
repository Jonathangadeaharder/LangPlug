#!/usr/bin/env python3
"""Simple health check test to verify server is running"""
from pathlib import Path
from urllib import request as urlreq

REPORT_PATH = Path(__file__).parent.parent / "logs" / "simple_health_test_report.txt"

def main():
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with REPORT_PATH.open("w", encoding="utf-8") as f:
        f.write("=== Simple Health Test ===\n")
        f.flush()

        try:
            req = urlreq.Request("http://localhost:8000/health")
            with urlreq.urlopen(req, timeout=5) as resp:
                code = resp.getcode()
                text = resp.read().decode("utf-8")
                f.write(f"Health check: {code}\n")
                f.write(f"Response: {text}\n")
                f.flush()

                if code == 200:
                    f.write("SUCCESS: Server is responding\n")
                else:
                    f.write(f"UNEXPECTED: Got {code} instead of 200\n")
        except Exception as e:
            f.write(f"FAILED: {e}\n")
            f.write("Server appears to be down\n")

        f.flush()

if __name__ == "__main__":
    main()
