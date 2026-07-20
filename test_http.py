import urllib.request
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

try:
    print("Testing GET /")
    html = urllib.request.urlopen("http://127.0.0.1:8888/").read().decode('utf-8')
    if "AJAX POLLING" in html:
        print("[SUCCESS] HTML contains AJAX POLLING string")
    else:
        print("[FAIL] HTML is old version")
        
    print("\nTesting GET /api/poll")
    poll = urllib.request.urlopen("http://127.0.0.1:8888/api/poll").read().decode('utf-8')
    print("Poll output length:", len(poll))
    print("Poll output start:", poll[:200])
except Exception as e:
    print("Error:", e)
