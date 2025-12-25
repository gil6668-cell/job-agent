import os
import json
import hashlib
import urllib.request
import urllib.parse

STATE_FILE = "state.json"

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# מקורות: בנק לאומי + מנורה מבטחים
SOURCES = {
    "🏦 בנק לאומי – משרות": "https://www.leumi.co.il/leumi_main/searchjobs",
    "🛡️ מנורה מבטחים – משרות": "https://www.menoramivt.co.il/job-posting/open-position",
}


def tg_send(text: str):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = urllib.parse.urlencode(
        {"chat_id": CHAT_ID, "text": text}
    ).encode("utf-8")
    req = urllib.request.Request(url, data=data)
    with urllib.request.urlopen(req, timeout=20) as r:
        r.read()


def fetch_text(url: str) -> str:
    req = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0"}
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="ignore")


def load_state():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"hashes": {}}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def page_hash(html: str) -> str:
    return hashlib.sha256(
        html.encode("utf-8", errors="ignore")
    ).hexdigest()


def main():
    if not TOKEN or not CHAT_ID:
        raise Exception("Missing TOKEN or TELEGRAM_CHAT_ID")

    state = load_state()
    hashes = state.get("hashes", {})

    changed = []

    for name, url in SOURCES.items():
        html = fetch_text(url)
        h = page_hash(html)

        old_h = hashes.get(url)
        if old_h is None:
            # ריצה ראשונה – רק שומרים מצב
            hashes[url] = h
        elif h != old_h:
            hashes[url] = h
            changed.append((name, url))

    state["hashes"] = hashes
    save_state(state)

    if changed:
        lines = ["🆕 שינוי בדפי משרות:"]
        for n, u in changed:
            lines.append(f"• {n}\n{u}")
        tg_send("\n\n".join(lines))
    else:
        tg_send("ℹ️ אין שינוי בדפי המשרות (לאומי + מנורה).")


if __name__ == "__main__":
    main()
