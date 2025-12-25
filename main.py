import os, json, time
import urllib.request, urllib.parse

STATE_FILE = "state.json"

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def tg_send(text: str):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": CHAT_ID, "text": text}).encode()
    req = urllib.request.Request(url, data=data)
    with urllib.request.urlopen(req, timeout=20) as r:
        r.read()

def load_state():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"seen": []}

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False)

def fetch_text(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="ignore")

# ---- מקור ראשון (קל): RSS של משרות ב-GitHub/Greenhouse/Lever וכו' ----
# כדי שלא ננחש אתר שיחסום אותנו, נתחיל בזה שתשים כאן RSS אחד.
RSS_URL = os.getenv("JOBS_RSS_URL", "").strip()

def parse_rss_items(xml: str, limit=10):
    # parser פשוט מאוד ל-RSS: מוצא <item> עם <title> ו-<link>
    items = []
    parts = xml.split("<item>")
    for p in parts[1:]:
        title = ""
        link = ""
        if "<title>" in p and "</title>" in p:
            title = p.split("<title>", 1)[1].split("</title>", 1)[0].strip()
        if "<link>" in p and "</link>" in p:
            link = p.split("<link>", 1)[1].split("</link>", 1)[0].strip()
        if title and link:
            items.append((title, link))
        if len(items) >= limit:
            break
    return items

def main():
    if not TOKEN or not CHAT_ID:
        raise Exception("Missing TELEGRAM_TOKEN or TELEGRAM_CHAT_ID")

    if not RSS_URL:
        tg_send("✅ הטלגרם עובד. עכשיו צריך להגדיר מקור משרות (RSS). שלח לי לינק RSS ראשון ונחבר אותו.")
        return

    xml = fetch_text(RSS_URL)
    items = parse_rss_items(xml, limit=15)

    state = load_state()
    seen = set(state.get("seen", []))

    new_items = []
    for title, link in items:
        key = link
        if key not in seen:
            new_items.append((title, link))

    if not new_items:
        tg_send("ℹ️ אין משרות חדשות מאז הפעם הקודמת.")
        return

    # שולחים עד 5 כדי לא להציף
    new_items = new_items[:5]
    msg_lines = ["🆕 משרות חדשות:"]
    for t, l in new_items:
        msg_lines.append(f"• {t}\n{l}")

    tg_send("\n\n".join(msg_lines))

    # שמירה
    for _, link in new_items:
        seen.add(link)
    state["seen"] = list(seen)[-500:]  # מגבילים גודל
    save_state(state)

main()
