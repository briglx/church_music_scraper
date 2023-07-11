#!/usr/bin/python
"""Tools to manage metadata on mp3."""
import argparse
import asyncio
import os
import re
import shutil

from mutagen import File


def show_all_keys(audio):
    """Show all tag names."""
    for key in audio.keys():
        print(f"{key}: {audio[key]}")


def get_name_part(filepath):
    """Get name from filepath."""
    pattern = r"\d{2}\s(.+)\.mp3"
    filename = filepath.split("/")[-1]  # Get the filename from the filepath
    match = re.match(pattern, filename)
    if match:
        text = match.group(1)
        return text

    return None


def parse_mp3_metadata(filepath):
    """Parse mp3 metadata."""
    metadata = {}

    audio = File(filepath)

    if audio is not None and audio.tags is not None:
        if "TPE1" in audio.tags:
            metadata["artist"] = audio.tags["TPE1"][0]
        if "TALB" in audio.tags:
            metadata["album"] = audio.tags["TALB"][0]
        if "TIT2" in audio.tags:
            metadata["title"] = audio.tags["TIT2"][0]
        if "TRCK" in audio.tags:
            metadata["track_no"] = audio.tags["TRCK"][0]
        if "TDRC" in audio.tags:
            metadata["track_date"] = audio.tags["TDRC"][0]
        # Add more tags as needed

    return metadata


def get_track_padding(filepath):
    """Get padding size for track."""
    three_wide = ["Hymns-Music Only", "Hymns-Words and Music", "Childrens Songbook"]

    for pattern in three_wide:
        if pattern in filepath:
            return 3

    return 2


def rename_file(filepath, new_filename):
    """Rename file to new filename."""
    # Generate the new filename based on the metadata
    new_filepath = os.path.join(os.path.dirname(filepath), new_filename)

    # Rename the file
    print(f"Rename {filepath} to {new_filepath}")
    # os.rename(filepath, new_filepath)


async def copy_file(source, destination):
    """Copy the file."""
    source_filepath = os.path.abspath(source)
    destination_filepath = os.path.abspath(destination)

    print(f"Copy {source_filepath} to {destination_filepath}")

    os.makedirs(os.path.dirname(destination_filepath), exist_ok=True)
    shutil.copy2(source_filepath, destination_filepath)


def set_directory(filepath, directory):
    """Rename file to new filename."""
    # Generate the new filename based on the metadata
    path, filename = os.path.split(filepath)
    new_filepath = os.path.join(directory, path, filename)

    # Rename the file
    print(f"Set directory for {filepath} {directory} to {new_filepath}")
    return new_filepath


def needs_new_name(filepath):
    """Check if file needs new name."""
    rename_album_paths = [
        "Childrens Songbook-Music Only",
        "Children's Songbook-Music Only",
        "Childrens Songbook-Words and Music",
        "Hymns-Music Only",
        "Hymns-Words and Music",
    ]

    for term in rename_album_paths:
        if term in filepath:
            return True
    return False


def parse_filepath(filepath):
    """Parse filepath into parts."""
    filename, _ = os.path.splitext(filepath)

    filename_parts = filename.split("/")
    album_path = "/".join(filename_parts[:-2]).strip()

    name_parts = filename_parts[-1].split(" ")
    track_name = " ".join(name_parts[1:]).strip()

    track_no = name_parts[0]

    return (album_path, track_name, track_no)


def remove_track_no_trailing_zero(filepath):
    """Remove track number trailing zero."""
    _, track_name, track_no = parse_filepath(filepath)

    # Remove trailing zero
    track_no = track_no[:-1]
    track_no = int(track_no)

    # Update filename with new track
    padding_len = get_track_padding(filepath)
    new_filename = f"{track_no:0{padding_len}d} {track_name}.mp3"

    # update filename only
    new_filepath = os.path.join(os.path.dirname(filepath), new_filename)
    return new_filepath


def use_tag_track_no(filepath):
    """Use track tag number."""
    album_path, track_name, track_no = parse_filepath(filepath)

    audio = File(filepath)
    track_no = audio.tags.get("TRCK", [track_no])[0]

    if "Let the Holy Spirit Guide" in filepath:
        track_no = "1430"

    if "If You Could Hie to Kolob" in filepath:
        track_no = "2840"

    if "Words and Music" in album_path:
        if "I Saw a Mighty Angel Fly" in filepath:
            track_no = "150"

    if "Music Only" in album_path:
        if "Prayer of Thanksgiving" in filepath:
            track_no = "930"

    if "Children's Songbook-Music Only" in album_path:
        track_no = track_no[:-1]
        track_no = int(track_no)
        if "Heritage" in filepath:
            track_no = track_no + 30
        if "Nature and Seasons" in filepath:
            track_no = track_no + 33
        if "Prelude Music" in filepath:
            track_no = track_no + 32
        track_no = f"{track_no:d}0"

    track_no = int(track_no)

    # update file with track no
    padding_len = get_track_padding(filepath)
    new_filename = f"{track_no:0{padding_len}d} {track_name}.mp3"

    # update filename only
    new_filepath = os.path.join(os.path.dirname(filepath), new_filename)
    return new_filepath


def get_new_name(filepath):
    """Get new name for filepath."""
    # album_path, track_name, track_no = parse_filepath(filepath)

    if "Hymns-Words and Music" in filepath:
        new_filepath = use_tag_track_no(filepath)
        new_filepath = remove_track_no_trailing_zero(new_filepath)
        return new_filepath

    if "Hymns-Music Only" in filepath:
        new_filepath = use_tag_track_no(filepath)
        new_filepath = remove_track_no_trailing_zero(new_filepath)
        return new_filepath

    if "Childrens Songbook-Music Only" in filepath:
        new_filepath = use_tag_track_no(filepath)
        new_filepath = remove_track_no_trailing_zero(new_filepath)
        return new_filepath

    if "Children's Songbook-Music Only" in filepath:
        new_filepath = use_tag_track_no(filepath)
        new_filepath = remove_track_no_trailing_zero(new_filepath)
        return new_filepath

    if "Childrens Songbook-Words and Music" in filepath:
        new_filepath = use_tag_track_no(filepath)
        new_filepath = remove_track_no_trailing_zero(new_filepath)
        return new_filepath

    return filepath


async def main():
    """Use metadata to update files."""
    track_list = []
    path = MUSIC_PATH
    path = "music_20230710_2/Children's Songbook-Music Only"
    for root, _, files in os.walk(path):
        for file in files:

            filepath = os.path.join(root, file)

            if needs_new_name(filepath):
                new_filepath = get_new_name(filepath)
                track_list.append((filepath, new_filepath))
            else:
                track_list.append((filepath, filepath))

    sorted_lst = sorted(track_list)
    tasks = []
    for item in sorted_lst:
        source, destination = item
        new_filename = set_directory(destination, "music_renamed")
        tasks.append(copy_file(source, new_filename))

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Church Music Scraper - Metadata.",
        add_help=True,
    )
    parser.add_argument(
        "--music_path",
        "-m",
        help="Path to music folder",
    )
    args = parser.parse_args()

    MUSIC_PATH = args.music_path or os.environ.get("MUSIC_PATH")

    if not MUSIC_PATH:
        raise ValueError(
            "Music path is required. Have you set the MUSIC_PATH env variable?"
        )

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
