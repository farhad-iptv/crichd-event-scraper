import requests
import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL = "https://app.crichd.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}


def get_channels(event_url):
    channels = []

    try:
        r = requests.get(event_url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")

        rows = soup.select("table tbody tr")

        for row in rows:
            cols = row.find_all("td")

            if len(cols) < 6:
                continue

            channel_name = cols[1].get_text(strip=True)
            language = cols[4].get_text(strip=True)

            watch_link = ""
            link_tag = cols[5].find("a")

            if link_tag:
                watch_link = link_tag.get("href", "")

            channels.append({
                "Channel name": channel_name,
                "Language": language,
                "Embed link": watch_link,
                "Stream link": ""
            })

    except Exception as e:
        print(f"Channel Error: {event_url} -> {e}")

    return channels


def parse_event(event_data):
    try:
        category = event_data["category"]
        card = event_data["card"]

        a_tag = card.find("a")
        if not a_tag:
            return None

        event_url = urljoin(BASE_URL, a_tag.get("href", ""))

        countdown = card.select_one(".data-countdown")

        start_time = ""
        end_time = ""
        status = "UNKNOWN"

        if countdown:
            start_time = countdown.get("data-start", "")
            end_time = countdown.get("data-end", "")

            status_text = countdown.get_text(strip=True)

            if "Live" in status_text:
                status = "LIVE"
            elif "Starts" in status_text:
                status = "UPCOMING"

        teams = card.select("div.flex.gap-2.items-center")

        team1_name = ""
        team1_logo = ""

        team2_name = ""
        team2_logo = ""

        if len(teams) >= 1:
            team1_name = teams[0].get_text(strip=True)

            img = teams[0].find("img")
            if img:
                team1_logo = img.get("src", "")

        if len(teams) >= 2:
            team2_name = teams[1].get_text(strip=True)

            img = teams[1].find("img")
            if img:
                team2_logo = img.get("src", "")

        match_name = (
            f"{team1_name} vs {team2_name}"
            if team1_name and team2_name
            else team1_name
        )

        channels = get_channels(event_url)

        return {
            "Category": category,
            "Tour/Group name": category,
            "match name": match_name,
            "Team 1 Name": team1_name,
            "Team 1 Logo": team1_logo,
            "Team 2 Name": team2_name,
            "Team 2 Logo": team2_logo,
            "Start time": start_time,
            "End time": end_time,
            "Status": status,
            "Event URL": event_url,
            "Channels": channels
        }

    except Exception as e:
        print("Event Parse Error:", e)
        return None


def get_events():
    print("Fetching homepage...")

    r = requests.get(BASE_URL, headers=HEADERS, timeout=20)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")

    event_blocks = []

    for league_header in soup.select("div.flex.items-center.gap-3.mb-3"):

        try:
            category_div = league_header.select_one(
                "div.text-gray-700"
            )

            if not category_div:
                continue

            category = category_div.get_text(strip=True)

            parent = league_header.parent

            cards = parent.select("div.mt-3")

            for card in cards:
                event_blocks.append({
                    "category": category,
                    "card": card
                })

        except:
            pass

    return event_blocks


def main():

    events = get_events()

    print(f"Found {len(events)} events")

    matches = []

    with ThreadPoolExecutor(max_workers=10) as executor:

        futures = [
            executor.submit(parse_event, event)
            for event in events
        ]

        for future in as_completed(futures):
            result = future.result()

            if result:
                matches.append(result)

    output = {
        "total_matches": len(matches),
        "matches": matches
    }

    with open(
        "matches.json",
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            output,
            f,
            indent=4,
            ensure_ascii=False
        )

    print(
        f"Saved {len(matches)} matches to matches.json"
    )


if __name__ == "__main__":
    main()
