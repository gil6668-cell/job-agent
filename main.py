import os
import json
import hashlib
import urllib.request
import urllib.parse
import urllib.error

STATE_FILE = "state.json"

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

SOURCES = {
    "🏦 בנק הפועלים – משרות": "https://www.bankhapoalim.co.il/he/jobs-site/lobby",
    "🛡️ הראל – קריירה": "https://www.harel-group.co.il/careers",
    "💻 הראל – Tech Jobs": "https://tech.harel-group.co.il/",
}


def tg_send(text: str):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": CHAT_ID, "text": text}).encode("utf-8")
    req = urllib.request.Request(url, data=data)
    with urllib.request.urlopen(req, timeout=20) as r:
        r.read()

def fetch_text(url: str) -> str:
    # מנסים להיראות כמו דפדפן אמיתי
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7",
        "Connection": "close",
    }
    req = urllib.request.Request(url, headers=headers)
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
    return hashlib.sha256(html.encode("utf-8", errors="ignore")).hexdigest()

def main():
    # לא מפילים את הריצה על בעיות של אתרים
    if not TOKEN or not CHAT_ID:
        # אם אין טוקן/צ'אט, אין טעם להמשיך
        raise Exception("Missing TOKEN or TELEGRAM_CHAT_ID")

    state = load_state()
    hashes = state.get("hashes", {})

    changed = []
    blocked = []
    other_errors = []

    for name, url in SOURCES.items():
        try:
            html = fetch_text(url)
            h = page_hash(html)

            old_h = hashes.get(url)
            if old_h is None:
                hashes[url] = h  # ריצה ראשונה רק שומר
            elif h != old_h:
                hashes[url] = h
                changed.append((name, url))

        except urllib.error.HTTPError as e:
            if e.code == 403:
                blocked.append((name, url))
            else:
                other_errors.append(f"{name} | HTTP {e.code}")
        except Exception as e:
            other_errors.append(f"{name} | {type(e).__name__}: {e}")

    state["hashes"] = hashes
    save_state(state)

    # שולחים הודעה מסכמת אחת
    lines = []
    if changed:
        lines.append("🆕 שינוי בדפי משרות:")
        for n, u in changed:
            lines.append(f"• {n}\n{u}")

    if blocked:
        lines.append("⛔ חסימה (403) – האתר לא מאפשר גישה אוטומטית מ-GitHub:")
        for n, u in blocked:
            lines.append(f"• {n}\n{u}")

    if other_errors:
        lines.append("⚠️ שגיאות נוספות:")
        for x in other_errors[:3]:
            lines.append(f"• {x}")

    if not lines:
        lines.append("ℹ️ אין שינוי בדפי המשרות (והכול נגיש).")

    tg_send("\n\n".join(lines))

if __name__ == "__main__":
    main()
