#!/usr/bin/env python3
"""
CricHD Live Event Scraper (Selenium-based)
Fetches all live event info from https://crichd.top/
Outputs in a standardized JSON format with dynamically generated team logos.

Requirements:
    pip install selenium beautifulsoup4 webdriver-manager pytz
"""

import json
import time
import re
import sys
from datetime import datetime, timedelta, timezone
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

try:
    from webdriver_manager.chrome import ChromeDriverManager
    USE_WDM = True
except ImportError:
    USE_WDM = False

try:
    import pytz
    BD_TZ = pytz.timezone("Asia/Dhaka")
except ImportError:
    BD_TZ = timezone(timedelta(hours=6))


# ======================================================================
# Team Logo Generator
# ======================================================================

# Known team name mappings for logo URL generation
# Maps common abbreviations / alternate names → slug for the logo CDN
TEAM_NAME_MAP = {
    # Countries - Cricket
    "india": "india",
    "ind": "india",
    "india a": "india",
    "india-a": "india",
    "australia": "australia",
    "aus": "australia",
    "australia a": "australia",
    "england": "england",
    "eng": "england",
    "pakistan": "pakistan",
    "pak": "pakistan",
    "south africa": "south-africa",
    "sa": "south-africa",
    "rsa": "south-africa",
    "proteas": "south-africa",
    "new zealand": "new-zealand",
    "nz": "new-zealand",
    "black caps": "new-zealand",
    "sri lanka": "sri-lanka",
    "sl": "sri-lanka",
    "sri lanka a": "sri-lanka",
    "west indies": "west-indies",
    "wi": "west-indies",
    "windies": "west-indies",
    "bangladesh": "bangladesh",
    "ban": "bangladesh",
    "afghanistan": "afghanistan",
    "afg": "afghanistan",
    "zimbabwe": "zimbabwe",
    "zim": "zimbabwe",
    "ireland": "ireland",
    "ire": "ireland",
    "scotland": "scotland",
    "sco": "scotland",
    "netherlands": "netherlands",
    "ned": "netherlands",
    "nepal": "nepal",
    "nep": "nepal",
    "oman": "oman",
    "uae": "uae",
    "united arab emirates": "uae",
    "usa": "usa",
    "united states": "usa",
    "canada": "canada",
    "can": "canada",
    "kenya": "kenya",
    "namibia": "namibia",
    "nam": "namibia",
    "papua new guinea": "papua-new-guinea",
    "png": "papua-new-guinea",
    "hong kong": "hong-kong",
    "hk": "hong-kong",
    "bermuda": "bermuda",
    "uganda": "uganda",
    "uga": "uganda",
    "jersey": "jersey",
    "malaysia": "malaysia",
    "singapore": "singapore",
    "thailand": "thailand",
    "myanmar": "myanmar",
    "samoa": "samoa",
    "vanuatu": "vanuatu",
    "tanzania": "tanzania",

    # IPL Teams
    "chennai super kings": "chennai-super-kings",
    "csk": "chennai-super-kings",
    "mumbai indians": "mumbai-indians",
    "mi": "mumbai-indians",
    "royal challengers bangalore": "royal-challengers-bangalore",
    "royal challengers bengaluru": "royal-challengers-bangalore",
    "rcb": "royal-challengers-bangalore",
    "kolkata knight riders": "kolkata-knight-riders",
    "kkr": "kolkata-knight-riders",
    "delhi capitals": "delhi-capitals",
    "dc": "delhi-capitals",
    "punjab kings": "punjab-kings",
    "pbks": "punjab-kings",
    "rajasthan royals": "rajasthan-royals",
    "rr": "rajasthan-royals",
    "sunrisers hyderabad": "sunrisers-hyderabad",
    "srh": "sunrisers-hyderabad",
    "gujarat titans": "gujarat-titans",
    "gt": "gujarat-titans",
    "lucknow super giants": "lucknow-super-giants",
    "lsg": "lucknow-super-giants",

    # PSL Teams
    "karachi kings": "karachi-kings",
    "lahore qalandars": "lahore-qalandars",
    "islamabad united": "islamabad-united",
    "peshawar zalmi": "peshawar-zalmi",
    "quetta gladiators": "quetta-gladiators",
    "multan sultans": "multan-sultans",

    # BBL Teams
    "sydney sixers": "sydney-sixers",
    "sydney thunder": "sydney-thunder",
    "melbourne stars": "melbourne-stars",
    "melbourne renegades": "melbourne-renegades",
    "brisbane heat": "brisbane-heat",
    "adelaide strikers": "adelaide-strikers",
    "hobart hurricanes": "hobart-hurricanes",
    "perth scorchers": "perth-scorchers",

    # T20 Blast / County Teams
    "birmingham bears": "birmingham-bears",
    "derbyshire falcons": "derbyshire-falcons",
    "durham": "durham",
    "essex eagles": "essex-eagles",
    "essex": "essex",
    "glamorgan": "glamorgan",
    "gloucestershire": "gloucestershire",
    "hampshire hawks": "hampshire-hawks",
    "hampshire": "hampshire",
    "kent spitfires": "kent-spitfires",
    "kent": "kent",
    "lancashire lightning": "lancashire-lightning",
    "lancashire": "lancashire",
    "leicestershire foxes": "leicestershire-foxes",
    "leicestershire": "leicestershire",
    "middlesex": "middlesex",
    "northamptonshire steelbacks": "northamptonshire-steelbacks",
    "northamptonshire": "northamptonshire",
    "northants": "northamptonshire",
    "nottinghamshire outlaws": "nottinghamshire-outlaws",
    "nottinghamshire": "nottinghamshire",
    "notts outlaws": "nottinghamshire-outlaws",
    "somerset": "somerset",
    "surrey": "surrey",
    "sussex sharks": "sussex-sharks",
    "sussex": "sussex",
    "warwickshire bears": "warwickshire-bears",
    "warwickshire": "warwickshire",
    "worcestershire rapids": "worcestershire-rapids",
    "worcestershire": "worcestershire",
    "yorkshire vikings": "yorkshire-vikings",
    "yorkshire": "yorkshire",

    # CPL Teams
    "trinbago knight riders": "trinbago-knight-riders",
    "tkr": "trinbago-knight-riders",
    "guyana amazon warriors": "guyana-amazon-warriors",
    "barbados royals": "barbados-royals",
    "st kitts and nevis patriots": "st-kitts-and-nevis-patriots",
    "jamaica tallawahs": "jamaica-tallawahs",
    "st lucia kings": "st-lucia-kings",

    # SA20 Teams
    "mi cape town": "mi-cape-town",
    "paarl royals": "paarl-royals",
    "pretoria capitals": "pretoria-capitals",
    "durban super giants": "durban-super-giants",
    "joburg super kings": "joburg-super-kings",
    "sunrisers eastern cape": "sunrisers-eastern-cape",

    # The Hundred
    "oval invincibles": "oval-invincibles",
    "trent rockets": "trent-rockets",
    "birmingham phoenix": "birmingham-phoenix",
    "london spirit": "london-spirit",
    "manchester originals": "manchester-originals",
    "northern superchargers": "northern-superchargers",
    "southern brave": "southern-brave",
    "welsh fire": "welsh-fire",
}

# Logo CDN base URLs to try (in order of preference)
LOGO_CDN_BASES = [
    "https://img.cricketworld.com/teams/{slug}.png",
    "https://cdn.img4every1.org/team/{slug}/logo.webp",
    "https://ssl.gstatic.com/onebox/media/sports/logos/{slug}_96x96.png",
]

# Default fallback logo
DEFAULT_LOGO = "https://cdn.img4every1.org/team/default/logo.webp"
CRICKET_LOGO = "https://cdn.img4every1.org/team/cricket/logo.webp"


def slugify(name: str) -> str:
    """Convert a team name to a URL-friendly slug."""
    slug = name.lower().strip()
    slug = re.sub(r"[''`]", "", slug)
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    slug = slug.strip("-")
    return slug


def get_team_logo(team_name: str) -> str:
    """
    Generate a team logo URL from the team name.
    Uses known mappings first, then falls back to slugified CDN URL.
    """
    if not team_name:
        return DEFAULT_LOGO

    clean = team_name.strip().lower()

    # Check known mappings
    if clean in TEAM_NAME_MAP:
        slug = TEAM_NAME_MAP[clean]
    else:
        slug = slugify(team_name)

    # Use the CDN pattern
    return f"https://cdn.img4every1.org/team/{slug}/logo.webp"


def parse_teams_from_match_name(match_name: str) -> tuple[str, str]:
    """
    Extract Team 1 and Team 2 from a match name like:
      - "India vs Afghanistan"
      - "1st ODI India vs Afghanistan"
      - "2nd Test England vs New Zealand"
      - "Australia vs Bangladesh"
      - "West Indies vs Sri Lanka"
      - "T20 Blast 2026" (tournament, no vs)
      - "Women's T20 World Cup 2026" (tournament)
    """
    if not match_name:
        return ("", "")

    name = match_name.strip()

    # Try to find "vs" separator
    vs_patterns = [
        r"\bvs\.?\b",
        r"\bv\.?\b",
        r"\bversus\b",
    ]

    for pattern in vs_patterns:
        match = re.search(pattern, name, re.IGNORECASE)
        if match:
            left = name[: match.start()].strip()
            right = name[match.end() :].strip()

            # Remove prefixes like "1st ODI", "2nd Test", "3rd T20I" etc.
            prefix_pattern = r"^(?:\d+(?:st|nd|rd|th)\s+)?(?:ODI|Test|T20I?|Match|Game|Final|Semi[- ]?Final|Qualifier|Eliminator)\s+"
            left = re.sub(prefix_pattern, "", left, flags=re.IGNORECASE).strip()
            right = re.sub(prefix_pattern, "", right, flags=re.IGNORECASE).strip()

            # Clean up
            left = left.strip(" -–—")
            right = right.strip(" -–—")

            if left and right:
                return (left, right)

    # No "vs" found — this might be a tournament name
    return (name, "")


def parse_match_datetime(date_str: str, time_str: str) -> tuple[str, str]:
    """
    Parse date and time strings into ISO 8601 UTC format.
    Returns (start_time, end_time) where end_time is start + 3 hours for cricket.

    Expected formats:
      date_str: "13-06-2026", "Today", "Tomorrow"
      time_str: "14:00", "09:30"

    The times on crichd.top appear to be in the selected timezone (default GMT+00).
    We treat them as UTC.
    """
    start_dt = None

    if not date_str and not time_str:
        return ("", "")

    # Handle "Today" / "Tomorrow"
    now_utc = datetime.now(timezone.utc)
    clean_date = date_str.strip().lower() if date_str else ""

    if clean_date == "today":
        base_date = now_utc.date()
    elif clean_date == "tomorrow":
        base_date = (now_utc + timedelta(days=1)).date()
    else:
        # Try parsing dd-mm-yyyy
        for fmt in ["%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d", "%d-%m-%y"]:
            try:
                base_date = datetime.strptime(clean_date, fmt).date()
                break
            except (ValueError, TypeError):
                continue
        else:
            # Couldn't parse date
            base_date = now_utc.date()

    # Parse time
    clean_time = time_str.strip() if time_str else "00:00"
    for tfmt in ["%H:%M", "%I:%M %p", "%H:%M:%S"]:
        try:
            t = datetime.strptime(clean_time, tfmt).time()
            break
        except (ValueError, TypeError):
            continue
    else:
        t = datetime.strptime("00:00", "%H:%M").time()

    start_dt = datetime.combine(base_date, t, tzinfo=timezone.utc)

    # Cricket matches typically last ~3-4 hours (T20: ~3h, ODI: ~8h, Test: ~7h/day)
    # Default to 3.5 hours
    end_dt = start_dt + timedelta(hours=3, minutes=30)

    start_iso = start_dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    end_iso = end_dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")

    return (start_iso, end_iso)


def determine_status(event: dict) -> str:
    """Determine event status: LIVE, UPCOMING, or FINISHED."""
    raw_status = event.get("status", "").upper()

    if "LIVE" in raw_status:
        return "LIVE"

    # Check based on time
    start_str = event.get("_start_iso", "")
    if start_str:
        try:
            start_dt = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            end_dt = start_dt + timedelta(hours=3, minutes=30)

            if now < start_dt:
                return "UPCOMING"
            elif start_dt <= now <= end_dt:
                return "LIVE"
            else:
                return "FINISHED"
        except (ValueError, TypeError):
            pass

    if "SCHEDULED" in raw_status or "SCHEDULE" in raw_status:
        return "UPCOMING"

    return "UPCOMING"


# ======================================================================
# Scraper Class
# ======================================================================

class CricHDScraper:
    BASE_URL = "https://crichd.top/"
    REFERER = "https://crichd.top/"
    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    def __init__(self, delay=3.0, headless=True, page_load_wait=15, owner="Farhad Hossain"):
        self.delay = delay
        self.headless = headless
        self.page_load_wait = page_load_wait
        self.owner = owner
        self.events = []
        self.driver = None

    # ------------------------------------------------------------------
    # Browser setup
    # ------------------------------------------------------------------
    def _init_driver(self):
        print("[INIT] Setting up Chrome WebDriver...")
        chrome_options = Options()

        if self.headless:
            chrome_options.add_argument("--headless=new")

        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument(f"user-agent={self.USER_AGENT}")
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_experimental_option(
            "excludeSwitches", ["enable-automation", "enable-logging"]
        )
        chrome_options.add_experimental_option("useAutomationExtension", False)

        try:
            if USE_WDM:
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                self.driver = webdriver.Chrome(options=chrome_options)
        except Exception as e:
            print(f"[ERROR] Failed to initialize Chrome: {e}")
            print("[TIP] Make sure Google Chrome is installed.")
            print("[TIP] pip install webdriver-manager")
            sys.exit(1)

        self.driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"},
        )
        print("[INIT] Chrome WebDriver ready.\n")

    def _close_driver(self):
        if self.driver:
            self.driver.quit()
            self.driver = None
            print("[CLOSE] Browser closed.")

    def _get_page_source(self, url: str, wait_selector: str = None) -> str | None:
        try:
            print(f"  [GET] {url}")
            self.driver.get(url)

            if wait_selector:
                try:
                    WebDriverWait(self.driver, self.page_load_wait).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, wait_selector))
                    )
                except TimeoutException:
                    print(f"  [WARN] Timeout waiting for '{wait_selector}', proceeding...")

            time.sleep(self.delay)
            return self.driver.page_source

        except Exception as exc:
            print(f"  [ERROR] Failed to load {url}: {exc}")
            return None

    # ------------------------------------------------------------------
    # Main page parsing
    # ------------------------------------------------------------------
    def fetch_main_page(self) -> list[dict]:
        source = self._get_page_source(self.BASE_URL, wait_selector="div.CSSTableGenerator")

        if not source:
            print("  [RETRY] Retrying with longer wait...")
            time.sleep(5)
            source = self._get_page_source(self.BASE_URL, wait_selector="table")

        if not source:
            print("[ERROR] Could not load main page.")
            return []

        soup = BeautifulSoup(source, "html.parser")

        with open("debug_main_page.html", "w", encoding="utf-8") as f:
            f.write(soup.prettify())

        events: list[dict] = []

        tables = soup.select("div.CSSTableGenerator table")
        if not tables:
            tables = soup.select("div.box table")
        if not tables:
            tables = soup.find_all("table")

        print(f"  [INFO] Found {len(tables)} table(s) on the page.")

        for table in tables:
            rows = table.find_all("tr")
            if not rows:
                continue

            header_text = rows[0].get_text(strip=True).lower()
            if any(kw in header_text for kw in ["league", "title", "match time", "link"]):
                print(f"  [INFO] Schedule table: {len(rows) - 1} event row(s).")
                for row in rows[1:]:
                    event = self._parse_schedule_row(row)
                    if event:
                        events.append(event)

        print(f"\n[INFO] Extracted {len(events)} event(s) from the main page.\n")
        return events

    def _parse_schedule_row(self, row) -> dict | None:
        cols = row.find_all("td")
        if len(cols) < 4:
            return None

        event: dict = {}

        # Column 0: Logo
        img = cols[0].find("img")
        if img:
            event["logo_url"] = urljoin(self.BASE_URL, img.get("src", ""))
            event["logo_alt"] = img.get("alt", "")
        else:
            event["logo_url"] = ""
            event["logo_alt"] = ""

        # Column 1: League
        league_link = cols[1].find("a")
        if league_link:
            event["league_name"] = league_link.get_text(strip=True)
            event["league_url"] = league_link.get("href", "")
        else:
            event["league_name"] = cols[1].get_text(strip=True)
            event["league_url"] = ""

        # Column 2: Title
        title_link = cols[2].find("a")
        if title_link:
            event["event_name"] = title_link.get_text(strip=True)
            event["event_url"] = title_link.get("href", "")
        else:
            event["event_name"] = cols[2].get_text(strip=True)
            event["event_url"] = ""

        # Column 3: Match time
        time_cell = cols[3]

        countdown_div = time_cell.find(attrs={"data-countdown": True})
        if countdown_div:
            event["countdown_target"] = countdown_div["data-countdown"]
        else:
            event["countdown_target"] = ""

        post_day = time_cell.find("small", class_="post-day")
        if post_day:
            dt_span = post_day.find("span", class_="dt")
            time_str = dt_span.get_text(strip=True) if dt_span else ""
            date_text = post_day.get_text(strip=True)
            if time_str:
                date_text = date_text.replace(time_str, "").strip()
            date_text = date_text.replace("\xa0", "").strip()
            event["match_date"] = date_text
            event["match_time"] = time_str
        else:
            event["match_date"] = ""
            event["match_time"] = ""

        # Column 4: Watch link
        if len(cols) > 4:
            watch_link = cols[4].find("a")
            event["watch_url"] = watch_link.get("href", "") if watch_link else event.get("event_url", "")
        else:
            event["watch_url"] = event.get("event_url", "")

        # Column 5: Status
        if len(cols) > 5:
            status_cell = cols[5]
            cell_classes = " ".join(status_cell.get("class", []))
            status_div = status_cell.find("div")

            if "liveg" in cell_classes:
                event["status"] = "LIVE"
            elif status_div:
                div_classes = " ".join(status_div.get("class", []))
                if "liveg" in div_classes:
                    event["status"] = "LIVE"
                elif "scheduleg" in div_classes:
                    event["status"] = "SCHEDULED"
                else:
                    event["status"] = status_cell.get_text(strip=True) or "UNKNOWN"
            else:
                event["status"] = status_cell.get_text(strip=True) or "UNKNOWN"
        else:
            event["status"] = "UNKNOWN"

        return event

    # ------------------------------------------------------------------
    # Event detail page parsing
    # ------------------------------------------------------------------
    def fetch_event_details(self, event_url: str) -> dict:
        details: dict = {"channels": [], "game_info": {}}

        if not event_url:
            return details

        full_url = event_url if event_url.startswith("http") else urljoin(self.BASE_URL, event_url)

        time.sleep(self.delay)
        source = self._get_page_source(full_url, wait_selector="div.CSSTableGenerator")

        if not source:
            return details

        soup = BeautifulSoup(source, "html.parser")

        css_tables = soup.select("div.CSSTableGenerator table")
        if not css_tables:
            css_tables = soup.select("div.box table")
        if not css_tables:
            css_tables = soup.find_all("table")

        for table in css_tables:
            rows = table.find_all("tr")
            if not rows:
                continue

            header_texts = [td.get_text(strip=True).lower() for td in rows[0].find_all("td")]
            header_combined = " ".join(header_texts)

            if "channel name" in header_combined or (
                "link" in header_combined and "language" in header_combined
            ):
                for row in rows[1:]:
                    cols = row.find_all("td")
                    if len(cols) < 3:
                        continue
                    channel = {
                        "channel_name": cols[0].get_text(strip=True),
                        "language": cols[1].get_text(strip=True),
                    }
                    link_tag = cols[2].find("a")
                    if link_tag:
                        channel["stream_url"] = link_tag.get("href", "")
                    else:
                        channel["stream_url"] = ""
                    details["channels"].append(channel)

            elif any(
                kw in header_combined
                for kw in ["game name", "sports name", "start date", "tour", "league"]
            ):
                for row in rows:
                    cols = row.find_all("td")
                    if len(cols) >= 2:
                        key = cols[0].get_text(strip=True).rstrip(":").strip()
                        value = cols[1].get_text(strip=True)
                        val_link = cols[1].find("a")
                        entry = {"value": value}
                        if val_link:
                            entry["url"] = val_link.get("href", "")
                        if key:
                            details["game_info"][key] = entry
            else:
                for row in rows:
                    cols = row.find_all("td")
                    if len(cols) == 2:
                        key = cols[0].get_text(strip=True).rstrip(":").strip()
                        value = cols[1].get_text(strip=True)
                        if key and value:
                            val_link = cols[1].find("a")
                            entry = {"value": value}
                            if val_link:
                                entry["url"] = val_link.get("href", "")
                            details["game_info"][key] = entry

        return details

    # ------------------------------------------------------------------
    # Build final output format
    # ------------------------------------------------------------------
    def _build_output(self) -> dict:
        """Convert raw scraped events into the desired JSON format."""
        now_bd = datetime.now(BD_TZ) if isinstance(BD_TZ, timezone) else datetime.now(BD_TZ)
        last_updated = now_bd.strftime("%Y-%m-%d %I:%M:%S %p") + " (BD Time)"

        matches = []
        total_links = 0

        for ev in self.events:
            event_name = ev.get("event_name", "")
            league_name = ev.get("league_name", "")
            details = ev.get("details", {})
            game_info = details.get("game_info", {})
            channels_raw = details.get("channels", [])

            # Determine category (sport)
            category = game_info.get("Sports Name", {}).get("value", "Cricket")
            if not category:
                category = "Cricket"

            # Tour / Group name
            tour = game_info.get("Tour/League", {}).get("value", "")
            if not tour:
                tour = league_name

            # Parse teams from match name
            team1_name, team2_name = parse_teams_from_match_name(event_name)

            # Generate logos
            team1_logo = get_team_logo(team1_name) if team1_name else DEFAULT_LOGO
            team2_logo = get_team_logo(team2_name) if team2_name else DEFAULT_LOGO

            # Parse date/time
            start_iso, end_iso = parse_match_datetime(
                ev.get("match_date", ""),
                ev.get("match_time", "")
            )

            # Store for status check
            ev["_start_iso"] = start_iso

            # Determine status
            status = determine_status(ev)

            # Build channels list
            formatted_channels = []
            for ch in channels_raw:
                channel_entry = {
                    "channel_name": ch.get("channel_name", ""),
                    "channel_language": ch.get("language", ""),
                    "stream_url": ch.get("stream_url", ""),
                    "referer": self.REFERER,
                    "user_agent": self.USER_AGENT,
                }
                formatted_channels.append(channel_entry)
                total_links += 1

            match_entry = {
                "Category": category,
                "Tour/Group name": tour,
                "match name": event_name,
                "Team 1 Name": team1_name,
                "Team 1 Logo": team1_logo,
                "Team 2 Name": team2_name if team2_name else "TBD",
                "Team 2 Logo": team2_logo if team2_name else DEFAULT_LOGO,
                "Start time": start_iso,
                "End time": end_iso,
                "Status": status,
                "referer": self.REFERER,
                "User agent": self.USER_AGENT,
                "Channels": formatted_channels,
            }

            matches.append(match_entry)

        output = {
            "playlist_name": "CricHD Live Sports Events",
            "owner": self.owner,
            "last_updated": last_updated,
            "total_links": total_links,
            "matches": matches,
        }

        return output

    # ------------------------------------------------------------------
    # Orchestrator
    # ------------------------------------------------------------------
    def scrape_all(self, fetch_details: bool = True) -> dict:
        self._init_driver()

        try:
            events = self.fetch_main_page()

            if fetch_details and events:
                total = len(events)
                for idx, event in enumerate(events, 1):
                    url = event.get("event_url") or event.get("watch_url", "")
                    print(
                        f"\n[{idx}/{total}] Fetching details: "
                        f"{event.get('event_name', 'N/A')}"
                    )
                    event["details"] = self.fetch_event_details(url)
            elif not events:
                print("[WARN] No events found. Check debug_main_page.html")

            self.events = events
            return self._build_output()

        finally:
            self._close_driver()

    # ------------------------------------------------------------------
    # Output
    # ------------------------------------------------------------------
    def save_json(self, output: dict, filepath: str = "crichd_events.json"):
        with open(filepath, "w", encoding="utf-8") as fh:
            json.dump(output, fh, indent=4, ensure_ascii=False)
        print(f"\n[SAVED] {filepath}")
        print(f"  → {len(output.get('matches', []))} matches")
        print(f"  → {output.get('total_links', 0)} total channel links")

    def print_summary(self, output: dict):
        matches = output.get("matches", [])

        print("\n" + "=" * 100)
        print(f"{'CRICHD LIVE SPORTS EVENTS':^100}")
        print("=" * 100)
        print(f"  Playlist : {output.get('playlist_name')}")
        print(f"  Owner    : {output.get('owner')}")
        print(f"  Updated  : {output.get('last_updated')}")
        print(f"  Total    : {len(matches)} matches, {output.get('total_links')} channel links")
        print("=" * 100)

        if not matches:
            print("\n  No events found!\n")
            return

        for i, m in enumerate(matches, 1):
            print(f"\n{'─' * 100}")
            print(f"  MATCH #{i}")
            print(f"{'─' * 100}")
            print(f"  {'Category':<22}: {m.get('Category')}")
            print(f"  {'Tour/Group':<22}: {m.get('Tour/Group name')}")
            print(f"  {'Match Name':<22}: {m.get('match name')}")
            print(f"  {'Team 1':<22}: {m.get('Team 1 Name')}")
            print(f"  {'Team 1 Logo':<22}: {m.get('Team 1 Logo')}")
            print(f"  {'Team 2':<22}: {m.get('Team 2 Name')}")
            print(f"  {'Team 2 Logo':<22}: {m.get('Team 2 Logo')}")
            print(f"  {'Start Time':<22}: {m.get('Start time')}")
            print(f"  {'End Time':<22}: {m.get('End time')}")
            print(f"  {'Status':<22}: {m.get('Status')}")

            channels = m.get("Channels", [])
            if channels:
                print(f"\n  {'Channels':<22}: ({len(channels)} available)")
                print(f"    {'#':<4} {'Name':<25} {'Language':<12} {'URL'}")
                print(f"    {'─'*4} {'─'*25} {'─'*12} {'─'*50}")
                for j, ch in enumerate(channels, 1):
                    print(
                        f"    {j:<4} "
                        f"{ch.get('channel_name', ''):<25} "
                        f"{ch.get('channel_language', ''):<12} "
                        f"{ch.get('stream_url', '')}"
                    )
            else:
                print(f"\n  {'Channels':<22}: None available")

        print(f"\n{'=' * 100}\n")


# ======================================================================
# Main
# ======================================================================

def main():
    print("=" * 65)
    print("  CricHD Live Event Scraper")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 65)

    scraper = CricHDScraper(
        delay=3.0,
        headless=True,
        page_load_wait=15,
        owner="Farhad Hossain",
    )

    output = scraper.scrape_all(fetch_details=True)

    scraper.print_summary(output)

    scraper.save_json(output, "crichd_events.json")

    print("[DONE] Scraping complete.")


if __name__ == "__main__":
    main()
