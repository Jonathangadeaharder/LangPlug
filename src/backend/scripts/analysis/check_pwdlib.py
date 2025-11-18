import json
import urllib.request

url = "https://pypi.org/pypi/pwdlib/json"
with urllib.request.urlopen(url, timeout=5) as response:  # noqa: S310
    data = json.loads(response.read())
    print("Latest pwdlib:", data["info"]["version"])  # noqa: T201
    deps = data["info"]["requires_dist"] or []
    argon_deps = [d for d in deps if "argon2" in d.lower()]
    print("Argon2 dependencies:", argon_deps)  # noqa: T201
