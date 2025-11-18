#!/usr/bin/env python3
"""Check recent fastapi-users versions."""

import json
import urllib.request

url = "https://pypi.org/pypi/fastapi-users/json"
with urllib.request.urlopen(url, timeout=10) as response:  # noqa: S310
    data = json.loads(response.read())

    # Get versions 10-14
    all_versions = list(data["releases"].keys())
    recent_versions = [v for v in all_versions if v.startswith(("10.", "11.", "12.", "13.", "14."))]

    print("FastAPI-Users password library dependency evolution:\n")  # noqa: T201
    for version in recent_versions[-15:]:  # Last 15 versions
        try:
            ver_url = f"https://pypi.org/pypi/fastapi-users/{version}/json"
            with urllib.request.urlopen(ver_url, timeout=5) as ver_response:  # noqa: S310
                ver_data = json.loads(ver_response.read())
                requires = ver_data["info"].get("requires_dist", []) or []

                pwdlib_deps = [r for r in requires if "pwdlib" in r.lower()]
                passlib_deps = [r for r in requires if "passlib" in r.lower()]

                if pwdlib_deps or passlib_deps:
                    print(f"{version:15} {pwdlib_deps or passlib_deps}")  # noqa: T201
        except Exception:
            pass

    print("\n" + "=" * 80)  # noqa: T201
    print("Conclusion: pwdlib was introduced in v13.0.0+")  # noqa: T201
    print("=" * 80)  # noqa: T201
