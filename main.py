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


async def create_album_folder(album_title):
    """Create sub folder for album."""
    folder_name = os.path.join(get_music_folder(), album_title)

    LOGGER.info("Making folder: %s", folder_name)

    if not await async_os.path.exists(folder_name):
        await async_os.mkdir(folder_name)
    else:
        LOGGER.info("Folder already exists:  %s", folder_name)


def get_full_file_name(album_title, track_title, track_no):
    """Get full path for track."""
    filename = f"{track_no:02d} {track_title}.mp3"
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


async def get_album_links(session, url):
    """Get album links from site."""
    album_links = []

    html = await fetch_url(session, url)
    if html is None:
        return
    soup = BeautifulSoup(await html.text(), "html.parser")

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


async def scrape_album_site(session, url):
    """Scrape the album site following urls."""
    track_idx = 0
    html = await fetch_url(session, url)
    if html is None:
        return

    # html = await fetch_url(url)
    soup = BeautifulSoup(await html.text(), "html.parser")

    # Get Album Title
    header = soup.find("header")
    h1_title = header.find("h1", recursive=False)
    album_title = h1_title.text.strip()

    links = []
    div_track_collection = soup.find("div", attrs={"data-testid": "CollectionListView"})
    a_tags = div_track_collection.find_all("a", recursive=False)
    for a_tag in a_tags:
        links.append(a_tag["href"])

    await create_album_folder(album_title)

    tasks = []
    for link in links:
        joined_link = join_url(url, link)
        tasks.append(
            process_child_page(session, joined_link, album_title, track_idx + 1)
        )
        track_idx = track_idx + 1

    await asyncio.gather(*tasks)


async def get_album_from_json(session, url):
    """Get Album details from site."""
    album_title = None
    tracks = []
    html = await fetch_url(session, url)
    if html is None:
        return
    soup = BeautifulSoup(await html.text(), "html.parser")

    if soup.find("script", attrs={"type": "application/json"}):

        json_data = json.loads(
            soup.find("script", attrs={"type": "application/json"}).string
        )

        album_title = json_data["props"]["pageProps"]["title"].strip()

        for item in json_data["props"]["pageProps"].get("items", []):
            track_title = item["title"].strip()
            audio_src = item["downloads"][0].get("url")

            tracks.append((track_title, audio_src))

        return (album_title, tracks)


async def scrape_album_json(session, url):
    """Scrape the album site's json data."""
    album_info = get_album_from_json(session, url)
    if album_info is None:
        return

    album_title, tracks = album_info
    await create_album_folder(album_title)

    tasks = []
    for idx, item in enumerate(tracks):
        track_title, audio_src = item
        full_file_name = get_full_file_name(album_title, track_title, idx + 1)
        tasks.append(save_mp3(session, audio_src, full_file_name))

        await asyncio.gather(*tasks)


async def process_child_page(session, url, album_title, track_no):
    """Parse and save track."""
    track_title = None
    audio_src = None

    html = await fetch_url(session, url)
    if html:
        soup = BeautifulSoup(await html.text(), "html.parser")
        div_elements = soup.find_all("div")

        # Iterate through the div elements
        for div in div_elements:
            # Check if the div contains an h1, button, and section
            if div.find("h1") and div.find("button") and div.find("section"):
                track_title = div.find("h1").text.strip()

        # get audio link
        audio_tag = soup.find("audio")
        if audio_tag and audio_tag.has_attr("src"):
            audio_src = audio_tag["src"]

        tasks = []
        if track_title and audio_src:
            track_title = re.sub(r"[^a-zA-Z0-9\s\.]", "", track_title)
            full_file_name = get_full_file_name(album_title, track_title, track_no)
            tasks.append(save_mp3(session, audio_src, full_file_name))

        await asyncio.gather(*tasks)

    else:
        print(f"No track for {url}")


async def scrape_youth_music_site(session, url):
    """Scrape the music site following urls."""
    tasks = []

    album_links = await get_album_links(session, url)

    for album_link in album_links:
        album_title, album_track_count, link = album_link

        LOGGER.info("Parsing Album: %s %s at %s", album_title, album_track_count, link)
        joined_link = join_url(url, link)
        tasks.append(scrape_album_json(session, joined_link))

    await asyncio.gather(*tasks)


async def main():
    """Fetch main data."""
    await create_music_folder()

    async with aiohttp.ClientSession() as session:
        await scrape_youth_music_site(session, SITE_URL)


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
    args = parser.parse_args()

    SITE_URL = args.site_url or os.environ.get("SITE_URL")
    MUSIC_PATH = args.music_path or os.environ.get("MUSIC_PATH")

    if not SITE_URL:
        raise ValueError(
            "Site URL is required. Have you set the SITE_URL env variable?"
        )
    if not MUSIC_PATH:
        raise ValueError(
            "Music path is required. Have you set the MUSIC_PATH env variable?"
        )
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
