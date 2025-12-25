import os
import json
import hashlib
import urllib.request
import urllib.parse

STATE_FILE = "state.json"

TOKEN = os.getenv("TOKEN")  # <-- שם הסוד: TOKEN
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")  # <-- שם הסוד: TELEGRAM_CHAT_ID

# מקורות התחלה (בנקים + ביטוח) — אפשר להוסיף עוד אחר כך
SOURCES = {
    "🏦 בנק לאומי – קריירה": "https://careers.leumi.co.il/",
    "🛡️ הראל – קריירה": "https://www.harel-group.co.il/about/career/Pages/default.aspx",
}


def tg_send(text: str):
    """שולח הודעה בטלגרם"""
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": CHAT_ID, "text": text}).encode("utf-8")
    req = urllib.request.Request(url, data=data)
    with urllib.request.urlopen(req, timeout=20) as r:
        r.read()


def fetch_text(url: str) -> str:
    """מוריד את הדף"""
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="ignore")


def load_state() -> dict:
    """קורא את state.json"""
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"hashes": {}}


def save_state(state: dict):
    """שומר state.json"""
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def page_hash(html: str) -> str:
    """יוצר טביעת אצבע לדף כדי לדעת אם השתנה"""
    return hashlib.sha256(html.encode("utf-8", errors="ignore")).hexdigest()


def main():
    if not TOKEN or not CHAT_ID:
        raise Exception("Missing TOKEN or TELEGRAM_CHAT_ID")

    state = load_state()
    hashes = state.get("hashes", {})

    changed = []
    errors = []

    for name, url in SOURCES.items():
        try:
            html = fetch_text(url)
            h = page_hash(html)

            old_h = hashes.get(url)
            if old_h is None:
                # פעם ראשונה – רק שומרים, לא מציפים
                hashes[url] = h
            else:
                if h != old_h:
                    hashes[url] = h
                    changed.append((name, url))

        except Exception as e:
            errors.append(f"{name} | {url}\n{type(e).__name__}: {e}")

    state["hashes"] = hashes
    save_state(state)

    # הודעה בטלגרם
    if changed:
        lines = ["🆕 נמצאו שינויים בדפי קריירה:"]
        for n, u in changed:
            lines.append(f"• {n}\n{u}")
        tg_send("\n\n".join(lines))
    elif errors:
        tg_send("⚠️ היו שגיאות בבדיקה:\n\n" + "\n\n".join(errors[:3]))
    else:
        tg_send("ℹ️ אין שינוי בדפי הקריירה (בנקים + ביטוח).")


if __name__ == "__main__":
    main()
