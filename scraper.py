import requests
import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import pytz

BASE_URL = "https://app.crichd.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


# ======================
# REAL BD TIME (LIVE)
# ======================
def get_bd_time():
    bd = pytz.timezone("Asia/Dhaka")
    return datetime.now(bd).strftime("%Y-%m-%d %I:%M:%S %p (BD Time)")


# ======================
# CHANNEL FETCH
# ======================
def get_channels(event_url):
    try:
        r = requests.get(event_url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")

        channels = []

        for row in soup.select("table tbody tr"):
            cols = row.find_all("td")
            if len(cols) < 6:
                continue

            link = cols[5].find("a")

            channels.append({
                "Channel name": cols[1].get_text(strip=True),
                "Language": cols[4].get_text(strip=True),
                "Embed link": link["href"] if link else "",
                "Stream link": ""
            })

        return channels

    except:
        return []


# ======================
# EVENT PARSE
# ======================
def parse_event(card, category):

    try:
        a = card.find("a")
        if not a:
            return None

        event_url = urljoin(BASE_URL, a["href"])

        countdown = card.select_one(".data-countdown")

        start = countdown.get("data-start", "") if countdown else ""
        end = countdown.get("data-end", "") if countdown else ""
        status_text = countdown.get_text(strip=True) if countdown else ""

        status = "LIVE" if "Live" in status_text else "UPCOMING"

        teams = card.select("div.flex.gap-2.items-center")

        t1 = teams[0] if len(teams) > 0 else None
        t2 = teams[1] if len(teams) > 1 else None

        team1 = t1.get_text(strip=True) if t1 else ""
        team2 = t2.get_text(strip=True) if t2 else ""

        logo1 = t1.find("img")["src"] if t1 and t1.find("img") else ""
        logo2 = t2.find("img")["src"] if t2 and t2.find("img") else ""

        channels = get_channels(event_url)

        return {
            "Category": category,
            "Tour/Group name": category,
            "match name": f"{team1} vs {team2}" if team2 else team1,
            "Team 1 Name": team1,
            "Team 1 Logo": logo1,
            "Team 2 Name": team2,
            "Team 2 Logo": logo2,
            "Start time": start,
            "End time": end,
            "Status": status,
            "referer": "https://bhalocast.pro/",
            "User agent": HEADERS["User-Agent"],
            "Channels": channels
        }

    except:
        return None


# ======================
# SCRAPE HOME PAGE
# ======================
def get_events():
    r = requests.get(BASE_URL, headers=HEADERS)
    soup = BeautifulSoup(r.text, "html.parser")

    data = []

    for league in soup.select("div.flex.items-center.gap-3.mb-3"):

        cat = league.select_one("div.text-gray-700")
        if not cat:
            continue

        category = cat.get_text(strip=True)

        parent = league.parent

        for card in parent.select("div.mt-3"):
            data.append((card, category))

    return data


# ======================
# MAIN
# ======================
def main():

    events = get_events()

    matches = []

    with ThreadPoolExecutor(max_workers=10) as ex:
        results = ex.map(lambda x: parse_event(x[0], x[1]), events)

        for r in results:
            if r:
                matches.append(r)

    total_links = sum(len(m["Channels"]) for m in matches)

    # 👉 REAL OUTPUT (NO COPY STATIC)
    output = {
        "playlist_name": "CricHD-event-scrapper",
        "owner": "Farhad Hossain",
        "telegram": "https://t.me/farhad2736",
        "last_updated": get_bd_time(),
        "total_links": total_links,
        "matches": matches
    }

    with open("matches.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=4, ensure_ascii=False)

    print("Live Update Done")
    print("Matches:", len(matches))
    print("Links:", total_links)


if __name__ == "__main__":
    main()
