from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import pandas as pd
import json


# =========================
# CONFIGURATION
# =========================
HEADLESS = False
WAIT_TIME = 5000


# =========================
# HELPER FUNCTIONS
# =========================
def normalize_area_input(area_input):
    """
    Convert user input into Speedhome URL format.

    Example:
    Mont Kiara -> mont-kiara
    Petaling Jaya -> petaling-jaya
    """

    return area_input.strip().lower().replace(" ", "-")


def build_area_url(area_slug):
    """
    Build Speedhome URL from area slug.
    """

    return f"https://speedhome.com/rent/{area_slug}"


# =========================
# SCRAPING FUNCTIONS
# =========================
def get_page_data(url):
    """
    Open a page and extract __NEXT_DATA__ JSON.
    """

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=HEADLESS
        )

        page = browser.new_page()

        print(f"\nOpening: {url}")

        page.goto(
            url,
            wait_until="domcontentloaded"
        )

        page.wait_for_timeout(WAIT_TIME)

        html = page.content()

        browser.close()

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    next_data = soup.find(
        "script",
        id="__NEXT_DATA__"
    )

    if not next_data:
        raise Exception("__NEXT_DATA__ not found")

    return json.loads(next_data.string)


def extract_properties(property_content):
    """
    Convert raw Speedhome JSON into our standardized format.
    """

    properties = []

    for item in property_content:

        property_data = {
            "id": item.get("id"),
            "name": item.get("name"),

            "bedroom": item.get("bedroom"),
            "bathroom": item.get("bathroom"),
            "carpark": item.get("carpark"),

            "monthly_price": item.get("price"),
            "yearly_price": item.get("price", 0) * 12,

            "sqft": item.get("sqft"),

            "furnish_type": item.get("furnishType"),
            "property_type": item.get("type"),

            "city": item.get("city"),
            "state": item.get("state"),

            "pet_friendly": item.get("petFriendly"),

            "listing_url": (
                f"https://speedhome.com/reels/{item.get('slug')}"
                if item.get("slug")
                else None
            )
        }

        properties.append(property_data)

    return properties


def scrape_area(area_input):
    """
    Scrape all pages for a given area.
    """

    area_slug = normalize_area_input(
        area_input
    )

    first_page_url = build_area_url(
        area_slug
    )

    print("\nGetting first page...")

    data = get_page_data(
        first_page_url
    )

    property_list = data["props"]["pageProps"]["propertyList"]

    total_pages = property_list["totalPages"]

    print(f"Found {total_pages} pages")

    all_properties = []

    for page_number in range(total_pages):

        print(
            f"\nScraping page {page_number + 1}/{total_pages}"
        )

        if page_number == 0:

            current_data = data

        else:

            page_url = (
                f"{first_page_url}?page={page_number + 1}"
            )

            current_data = get_page_data(
                page_url
            )

        current_property_list = current_data[
            "props"
        ]["pageProps"]["propertyList"]

        properties = extract_properties(
            current_property_list["content"]
        )

        print(
            f"Found {len(properties)} properties"
        )

        all_properties.extend(
            properties
        )

    print(
        f"\nTotal properties collected: {len(all_properties)}"
    )

    return all_properties, area_slug


# =========================
# EXPORT FUNCTIONS
# =========================
def save_to_csv(properties, area_slug):
    """
    Save scraped data into /data folder.
    """

    df = pd.DataFrame(
        properties
    )

    filename = (
        f"data/{area_slug.replace('-', '_')}.csv"
    )

    df.to_csv(
        filename,
        index=False
    )

    print(
        f"\nCSV saved to: {filename}"
    )


# =========================
# MAIN
# =========================
if __name__ == "__main__":

    area = input(
        "Enter area: "
    )

    properties, area_slug = scrape_area(
        area
    )

    save_to_csv(
        properties,
        area_slug
    )