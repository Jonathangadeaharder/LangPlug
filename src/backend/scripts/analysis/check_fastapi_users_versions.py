#!/usr/bin/env python3
"""Check fastapi-users version history for pwdlib dependency."""

import json
import urllib.request

url = "https://pypi.org/pypi/fastapi-users/json"
with urllib.request.urlopen(url, timeout=10) as response:
    data = json.loads(response.read())

    print("FastAPI-Users version history (last 10 releases):\n")
    releases = list(data["releases"].keys())[-10:]

    for version in releases:
        release_info = data["releases"][version]
        if release_info:
            # Get requires_dist from first release file
            requires_url = f"https://pypi.org/pypi/fastapi-users/{version}/json"
            try:
                with urllib.request.urlopen(requires_url, timeout=5) as ver_response:
                    ver_data = json.loads(ver_response.read())
                    requires = ver_data["info"].get("requires_dist", []) or []

                    # Check for pwdlib
                    pwdlib_deps = [r for r in requires if "pwdlib" in r.lower()]
                    passlib_deps = [r for r in requires if "passlib" in r.lower()]

                    print(f"Version {version}:")
                    if pwdlib_deps:
                        print(f"  - pwdlib: {pwdlib_deps[0]}")
                    if passlib_deps:
                        print(f"  - passlib: {passlib_deps[0]}")
                    if not pwdlib_deps and not passlib_deps:
                        print("  - No password library dependency!")
                    print()
            except Exception as e:
                print(f"  - Error checking: {e}\n")
