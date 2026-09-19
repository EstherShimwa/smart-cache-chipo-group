# timing.py
#
# Level 1 — Feel the Pain
# Run this BEFORE implementing any cache to record your baseline response times.
# Run it AGAIN after each level to see the improvement.
#
# Usage:
#   python timing.py
#
# Make sure the Django dev server is running first:
#   python manage.py runserver

import urllib.request
import time
import json

BASE_URL = "http://127.0.0.1:8000"

ENDPOINTS = [
    ("All Posts (list)", f"{BASE_URL}/api/posts/"),
    ("Single Post (id=1)", f"{BASE_URL}/api/posts/1/"),
]


def measure(label: str, url: str, runs: int = 3) -> None:
    times = []
    for _ in range(runs):
        start = time.perf_counter()
        try:
            with urllib.request.urlopen(url) as response:
                response.read()
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)
        except Exception as e:
            print(f"  ❌ {label}: {e}")
            return

    avg = sum(times) / len(times)
    fastest = min(times)
    print(f"  {label}")
    print(f"    First request : {times[0]:.1f}ms")
    print(f"    Average       : {avg:.1f}ms")
    print(f"    Fastest (cache hit?) : {fastest:.1f}ms")
    print()


def main():
    print("=" * 55)
    print("  CACHE TIMING SCRIPT")
    print("  Run BEFORE and AFTER implementing each level")
    print("=" * 55)
    print()

    for label, url in ENDPOINTS:
        measure(label, url)

    print("=" * 55)
    print("  💡 Tip: On a cache HIT the fastest time should be")
    print("     significantly lower than the first request.")
    print("=" * 55)


if __name__ == "__main__":
    main()
