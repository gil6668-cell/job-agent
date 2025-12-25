import os
import urllib.parse
import urllib.request

token = os.getenv("TELEGRAM_TOKEN")
chat_id = os.getenv("TELEGRAM_CHAT_ID")

if not token or not chat_id:
    raise Exception("Missing TELEGRAM_TOKEN or TELEGRAM_CHAT_ID")

text = "🤖 היי! זו הודעת בדיקה מהסוכן שלך."

data = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode()
url = f"https://api.telegram.org/bot{token}/sendMessage"

req = urllib.request.Request(url, data=data)
with urllib.request.urlopen(req, timeout=10) as resp:
    resp.read()
