# Email Scraper

This repository contains a Python script for scraping email addresses from
websites. It reads a list of sites (usually from a Google search result),
then crawls the pages and any linked contact/about pages looking for email
addresses.

## Features

- Recursive crawling of relevant pages
- Selenium integration to launch a browser session if needed
- Command-line interface with options for input/output files
- Colorful console output using `colorama`

## Usage

```bash
python email_scraper.py --input "Schools results.txt" --output emails.txt
```

Add `--no-browser` if you don't need the browser launch, and `-v` for verbose
logging.

## Requirements

See `requirements.txt`.

## Author

Pasindu Gunawardhana
- Telegram: [t.me/Pasindu_S_Gunawardhana](https://t.me/Pasindu_S_Gunawardhana)
- Email: silencelab.me@gmail.com
