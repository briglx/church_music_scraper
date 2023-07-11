#!/usr/bin/python
"""Main script for scraper."""
import argparse
import asyncio
import json
import logging
import os
import re
import sys
import urllib.parse

from aiofiles import os as async_os
import aiohttp
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    format="%(asctime)s %(levelname)s:%(name)s: %(message)s",
    level=logging.DEBUG,
    datefmt="%H:%M:%S",
    stream=sys.stderr,
)
LOGGER = logging.getLogger(__name__)
logging.getLogger("chardet.charsetprober").disabled = True


def get_music_folder():
    """Return the full path."""
    path = MUSIC_PATH
    if os.path.isabs(path):
        return path

    current_dir = os.getcwd()
    return os.path.join(current_dir, path)


async def create_music_folder():
    """Create post folder."""
    folder_name = get_music_folder()

    LOGGER.info("Making folder: %s", folder_name)

    if not await async_os.path.exists(folder_name):
        await async_os.mkdir(folder_name)
    else:
        LOGGER.info("Folder already exists to make folder:  %s", folder_name)


async def create_folder(sub_folder_name):
    """Create sub folder for album."""
    folder_name = os.path.join(get_music_folder(), sub_folder_name)

    LOGGER.info("Making folder: %s", folder_name)

    if not await async_os.path.exists(folder_name):
        await async_os.mkdir(folder_name)
    else:
        LOGGER.info("Folder already exists:  %s", folder_name)


async def create_album_folder(album_title, collection_title=None):
    """Create sub folder for album."""
    if collection_title:
        folder_name = os.path.join(get_music_folder(), collection_title, album_title)
    else:
        folder_name = os.path.join(get_music_folder(), album_title)

    LOGGER.info("Making folder: %s", folder_name)

    if not await async_os.path.exists(folder_name):
        await async_os.mkdir(folder_name)
    else:
        LOGGER.info("Folder already exists:  %s", folder_name)


def clean_name(name):
    """Ensure title is a valid name."""
    name = name.replace("<em>", "")
    name = name.replace("—", "-")
    name = name.replace("–", "-")
    name = name.replace("‘", "'")
    name = name.replace("’", "'")
    # track_title = track_title.replace("?","")
    # track_title = track_title.replace("!","")
    name = re.sub(r"[^a-zA-Z0-9\s\.\-\']", "", name)
    name = name.replace("  ", " ")
    name = name.replace("  ", " ")
    return name


def get_full_file_name(album_title, track_title, track_no, collection_title=None):
    """Get full path for track."""
    filename = f"{track_no:02d} {track_title}.mp3"
    if collection_title:
        file_path = os.path.join(
            get_music_folder(), collection_title, album_title, filename
        )
    else:
        file_path = os.path.join(get_music_folder(), album_title, filename)

    return file_path


async def fetch_url(session, url):
    """Fetch url data."""
    try:
        return await session.get(url)
    except aiohttp.ClientConnectionError:
        print(f"Connection error occurred while fetching: {url}")


async def save_mp3(session, url, filename):
    """Save mp3 to local file system."""
    response = await fetch_url(session, url)
    if response is None:
        return

    mp3_data = await response.read()
    with open(filename, "wb") as file:
        file.write(mp3_data)
    print(f"MP3 file saved as: {filename}")


def join_url(base_url, link):
    """Join base url with relative link."""
    parsed_original = urllib.parse.urlparse(base_url)
    joined_link = urllib.parse.urljoin(
        parsed_original.scheme + "://" + parsed_original.netloc, link
    )
    return joined_link


def has_album_detail(div_element):
    """Check if element has album info."""
    if len(div_element.contents) != 2:
        return False

    child1 = div_element.contents[0]
    child2 = div_element.contents[1]

    # Check if both children are divs
    if child1.name != "div" or child2.name != "div":
        return False

    # Check if second is only text in div
    if child2.contents and not isinstance(child2.contents[0], str):
        return False

    return True


def get_collection_id(soup):
    """Return the collection id for the page."""
    anchor_tags = soup.find_all("a")
    for anchor_tag in anchor_tags:
        href = anchor_tag.get("href")
        if href:
            parsed_url = urllib.parse.urlparse(href)
            query_params = urllib.parse.parse_qs(parsed_url.query)
            if "collectionId" in query_params:
                collection_id = query_params["collectionId"][0]
                return collection_id

    return None


def get_album_links(soup):
    """Get album links from site."""
    album_links = []

    div_album_collection = soup.find("div", attrs={"data-testid": "CollectionGridView"})
    for a_tag in div_album_collection.find_all("a"):
        for a_div in a_tag.find_all("div"):
            if has_album_detail(a_div):
                # Get the first two child divs
                child_divs = a_div.find_all("div", recursive=False)
                album_track_count = child_divs[0].text.strip()
                album_title = child_divs[1].text.strip()

                album_links.append((album_title, album_track_count, a_tag["href"]))

    return album_links


async def scrape_album_json(session, soup, collection_title=None):
    """Scrape the album site's json data."""
    if soup.find("script", attrs={"type": "application/json"}):

        json_data = json.loads(
            soup.find("script", attrs={"type": "application/json"}).string
        )

        if "err" in json_data:
            raise LookupError("This item is not available for download.")

        album_title = clean_name(json_data["props"]["pageProps"]["title"].strip())
        await create_album_folder(album_title, collection_title)

        tasks = []
        for idx, item in enumerate(json_data["props"]["pageProps"].get("items", [])):
            track_title = clean_name(item["title"].strip())
            audio_src = item["downloads"][0].get("url")
            full_file_name = get_full_file_name(
                album_title, track_title, idx + 1, collection_title
            )

            tasks.append(save_mp3(session, audio_src, full_file_name))

        await asyncio.gather(*tasks)
    else:
        raise LookupError("Json data not found on the page.")


async def scrape_album_html(session, url, soup, collection_title=None):
    """Get Album details from site."""
    album_title = await create_album_folder_from_page(soup, collection_title)

    div_track_collection = soup.find("div", attrs={"data-testid": "CollectionListView"})
    a_tags = div_track_collection.find_all("a", recursive=False)

    tasks = []
    for idx, item in enumerate(a_tags):
        track_url = join_url(url, item["href"])
        tasks.append(
            scrape_child_page(
                session, track_url, album_title, idx + 1, collection_title
            )
        )

    await asyncio.gather(*tasks)


def get_collection_url(base_url, soup):
    """Get collection full url."""
    collection_id = get_collection_id(soup)
    collection_url = COLLECTION_PATH_PATTERN.replace("collection_id", collection_id)
    full_url = join_url(base_url, collection_url)
    return full_url


async def create_album_folder_from_page(soup, collection_title):
    """Create album folder from page."""
    header = soup.find("header")
    h1_title = header.find("h1", recursive=False)
    album_title = clean_name(h1_title.text.strip())
    await create_album_folder(album_title, collection_title)
    return album_title


async def scrape_album_api(session, url, soup, collection_title):
    """Fetch tracks by the api."""
    album_title = await create_album_folder_from_page(soup, collection_title)

    # Get items by api call
    collection_url = get_collection_url(url, soup)
    response = await fetch_url(session, collection_url)
    if response.status == 200:
        json_data = await response.json()

        if "err" in json_data:
            raise LookupError("This item is not available for download.")

        if "items" in json_data:
            tasks = []
            for idx, item in enumerate(json_data["items"]):

                track_title = clean_name(item["title"].strip())
                audio_src = item["downloads"][0].get("url")
                full_file_name = get_full_file_name(
                    album_title, track_title, idx + 1, collection_title
                )

                tasks.append(save_mp3(session, audio_src, full_file_name))

            await asyncio.gather(*tasks)
        else:
            raise LookupError("No items in the data data not found on the page.")
    else:
        raise LookupError("Bad response.")


async def scrape_child_page(session, url, album_title, track_no, collection_title=None):
    """Parse and save track."""
    html = await fetch_url(session, url)
    if html is None:
        return

    soup = BeautifulSoup(await html.text(), "html.parser")

    # Look for track_title
    track_title = None
    div_elements = soup.find_all("div")
    for div in div_elements:
        # Check if the div contains an h1, button, and section
        if div.find("h1") and div.find("button") and div.find("section"):
            track_title = clean_name(div.find("h1").text.strip())

    # get audio link
    audio_src = None
    audio_tag = soup.find("audio")
    if audio_tag and audio_tag.has_attr("src"):
        audio_src = audio_tag["src"]

    tasks = []
    if track_title and audio_src:
        full_file_name = get_full_file_name(
            album_title, track_title, track_no, collection_title
        )
        tasks.append(save_mp3(session, audio_src, full_file_name))

    await asyncio.gather(*tasks)


def has_json_data(soup):
    """Check if page has json data."""
    # Search for the text 'mp3' or 'pageProps' in script tags
    script_tags = soup.find_all("script")
    for script_tag in script_tags:
        script_text = script_tag.get_text()
        if "mp3" in script_text or "pageProps" in script_text:
            return True

    return False


async def scrape_album_site(session, url, collection_title=None):
    """Scrape the album site following urls."""
    html = await fetch_url(session, url)
    if html is None:
        return

    soup = BeautifulSoup(await html.text(), "html.parser")

    try:
        if get_collection_id(soup):
            # Try to call json directly
            await scrape_album_api(session, url, soup, collection_title)

        elif has_json_data(soup):
            # Try to call json directly
            await scrape_album_json(session, soup, collection_title)

        else:
            await scrape_album_html(session, url, soup, collection_title)
    except LookupError:
        LOGGER.error("Failed to parse Album %s", url)


async def scrape_collection_site(session, url):
    """Scrape the music site following urls."""
    tasks = []

    html = await fetch_url(session, url)
    if html is None:
        return

    soup = BeautifulSoup(await html.text(), "html.parser")

    h1_title = soup.find("h1")
    collection_title = clean_name(h1_title.text.strip())
    await create_folder(collection_title)

    album_links = get_album_links(soup)

    for album_link in album_links:
        album_title, album_track_count, link = album_link

        LOGGER.info("Parsing Album: %s %s at %s", album_title, album_track_count, link)
        joined_link = join_url(url, link)
        tasks.append(scrape_album_site(session, joined_link, collection_title))

    await asyncio.gather(*tasks)


async def main():
    """Fetch main data."""
    await create_music_folder()

    async with aiohttp.ClientSession() as session:
        if IS_ALBUM:
            await scrape_album_site(session, SITE_URL)
        else:
            await scrape_collection_site(session, SITE_URL)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Church Music Scraper.",
        add_help=True,
    )
    parser.add_argument(
        "--site_url",
        "-s",
        help="Site URL to scrape",
    )
    parser.add_argument(
        "--music_path",
        "-m",
        help="Path to music folder",
    )
    parser.add_argument(
        "-a",
        action="store_true",
        help="Url path is an album.",
    )
    args = parser.parse_args()

    SITE_URL = args.site_url or os.environ.get("SITE_URL")
    MUSIC_PATH = args.music_path or os.environ.get("MUSIC_PATH")
    COLLECTION_PATH_PATTERN = os.environ.get("COLLECTION_PATH_PATTERN")
    IS_ALBUM = args.a

    if not SITE_URL:
        raise ValueError(
            "Site URL is required. Have you set the SITE_URL env variable?"
        )
    if not MUSIC_PATH:
        raise ValueError(
            "Music path is required. Have you set the MUSIC_PATH env variable?"
        )

    if not COLLECTION_PATH_PATTERN:
        raise ValueError(
            "Pattern is required. Have you set the COLLECTION_PATH_PATTERN env variable?"
        )

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
