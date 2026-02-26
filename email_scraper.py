"""Email scraper utility

This module reads a list of websites from a text file and attempts to
collect email addresses by crawling pages and shallowly following links
that are likely to contain contact information. It also demonstrates how to
bootstrap a Selenium browser with a custom profile.

Usage:
    python email_scraper.py --input "Schools results.txt" --output emails.txt

Dependencies (add to requirements.txt):
    selenium
    webdriver-manager
    requests
    beautifulsoup4
    colorama

Author: Pasindu Gunawardhana
Telegram: t.me/Pasindu_S_Gunawardhana
Email: silencelab.me@gmail.com
"""

import argparse
import logging
import os
import re
import sys
import time
from pathlib import Path
from typing import List, Set, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from colorama import Fore, Style, init as colorama_init
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# ---------------------------------------------------------------------------
# constants and defaults
# ---------------------------------------------------------------------------
DEFAULT_INPUT_FILE = "Schools results.txt"
DEFAULT_OUTPUT_FILE = "found_emails.txt"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
)
EMAIL_REGEX = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"

# keywords to look for when drilling into link targets
_DEEP_KEYWORDS = [
    "contact",
    "about",
    "support",
    "help",
    "staff",
    "team",
    "directory",
    "faculty",
    "admin",
    "about-us",
    "contact-us",
    "contactus",
]

# ---------------------------------------------------------------------------
# utility functions
# ---------------------------------------------------------------------------

def setup_logger(verbose: bool = False) -> None:
    """Configure the root logger."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(message)s",
        level=level,
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def init_browser(
    headless: bool = True,
    profile_dir: Optional[str] = None,
    user_data_dir: Optional[str] = None,
) -> webdriver.Chrome:
    """Create and return a configured Chrome webdriver instance."""
    options = Options()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(f"user-agent={USER_AGENT}")
    options.add_experimental_option("useAutomationExtension", False)
    options.add_experimental_option(
        "excludeSwitches", ["enable-logging", "enable-automation"]
    )

    if profile_dir:
        options.add_argument(f"--profile-directory={profile_dir}")
    if user_data_dir:
        options.add_argument(f"--user-data-dir={user_data_dir}")
    if headless:
        options.add_argument("--headless")

    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)


def extract_emails(text: str) -> Set[str]:
    """Return a set of email addresses found in ``text``.

    Filters out addresses that resemble package version strings such as
    ``bootstrap@5.3.3``.
    """
    emails = re.findall(EMAIL_REGEX, text)
    valid = {e for e in emails if not re.match(r".+@\d+\.\d+\.\d+", e)}
    return valid


def get_deep_links(soup: BeautifulSoup, base_url: str) -> List[str]:
    """Scan the soup for links whose href or link text contain keywords.

    The returned URLs are normalized to absolute form when possible.
    """
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"].lower()
        text = a.get_text().lower()
        if any(k in href or k in text for k in _DEEP_KEYWORDS):
            if href.startswith("http"):
                links.add(href)
            else:
                links.add(urljoin(base_url, href))
    return list(links)


def find_emails_deep(
    url: str, max_depth: int = 2, visited: Optional[Set[str]] = None
) -> Set[str]:
    """Recursively crawl ``url`` up to ``max_depth`` levels looking for emails."""
    if visited is None:
        visited = set()
    emails_found: Set[str] = set()
    try:
        resp = requests.get(url, timeout=10, headers={"User-Agent": USER_AGENT})
        emails_found.update(extract_emails(resp.text))
        if emails_found or max_depth <= 0:
            return emails_found
        soup = BeautifulSoup(resp.text, "html.parser")
        deep_links = get_deep_links(soup, url)
        for link in deep_links:
            if link not in visited:
                visited.add(link)
                emails_found.update(find_emails_deep(link, max_depth - 1, visited))
    except requests.RequestException:
        logging.debug("Failed to fetch %s", url)
    return emails_found


def process_input_file(input_path: Path, output_path: Path) -> None:
    """Read websites from ``input_path`` and write results to ``output_path``."""
    if not input_path.exists():
        logging.error("Input file does not exist: %s", input_path)
        return

    with input_path.open(encoding="utf-8") as fh, output_path.open(
        "w", encoding="utf-8"
    ) as out:
        for line in fh:
            if "->" not in line:
                continue
            website = line.split("->", 1)[1].strip()
            if not website.startswith(("http://", "https://")):
                website = "http://" + website
            logging.info("Searching emails on: %s", website)
            emails = find_emails_deep(website)
            if emails:
                logging.info("Found emails: %s", ", ".join(emails))
                out.write(f"{website} -> {', '.join(emails)}\n")
            else:
                logging.info("No emails found for %s", website)


def parse_args():
    parser = argparse.ArgumentParser(description="Simple email scraper.")
    parser.add_argument(
        "--input", "-i", default=DEFAULT_INPUT_FILE, help="Input file path"
    )
    parser.add_argument(
        "--output", "-o", default=DEFAULT_OUTPUT_FILE, help="Output file path"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser in headless mode (if launched)",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Skip launching Selenium browser",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable debug logging"
    )
    return parser.parse_args()


def main():
    colorama_init(autoreset=True)
    args = parse_args()
    setup_logger(args.verbose)

    if not args.no_browser:
        driver = init_browser(headless=args.headless)
        logging.info("Launched browser")
        try:
            driver.get("http://google.com")
            time.sleep(1)
        finally:
            driver.quit()

    input_path = Path(args.input)
    output_path = Path(args.output)
    process_input_file(input_path, output_path)


if __name__ == "__main__":
    main()
