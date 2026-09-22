import urllib.request, json
TOKEN = "8797412860:AAEl2fAdwu06DHrCPED-_q1APrZiAhKNGWc"
CHAT  = "7847039406"

url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
data = json.dumps({"chat_id": CHAT, "text": "Tes bot ✅"}).encode()
req = urllib.request.Request(url, data=data, method="POST")
req.add_header("Content-Type", "application/json")
try:
    print(urllib.request.urlopen(req).read().decode())
except urllib.error.HTTPError as e:
    print("HTTP", e.code)
    print(e.read().decode())
