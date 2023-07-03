#!/usr/bin/python
"""Tools to manage metadata on mp3."""
import os
import re

from mutagen import File
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, ID3NoHeaderError


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
    else:
        return None


def clean_track_no(filepath, track_no, padding_len):
    """Clean track number."""
    trailing_0 = [
        "Hymns-Music Only",
        "Hymns-Words and Music",
        "Peace in Christ 2018 Youth Album",
    ]
    leading_0 = ["Embark 2015 Youth Album-Instrumental"]
    for pattern in trailing_0:
        if pattern in filepath:
            track_no = track_no[:-1]

    for pattern in leading_0:
        if pattern in filepath:
            track_no = track_no[1:]

    if "/" in track_no:
        track_no = track_no.split("/")[0]

    track_no = int(track_no)
    # track_no = f"{track_no:0{padding_len}d}"
    return track_no


def use_tag_track_info(filepath):
    """Use information from tag."""
    bad_track_tags = [
        "Christmas at Temple Square",
        "Especially for Youth Songs",
        "Youth Songs/09 Your Light",
    ]

    for term in bad_track_tags:
        if term in filepath:
            return False

    return True


def use_tag_album_info(filepath):
    """Use information from tag."""
    good_album_paths = ["Especially for Youth Songs"]
    bad_songs = ["The Greatest Gift", "Songs/23 All Times All Things All Places"]

    for term in bad_songs:
        if term in filepath:
            return False

    for term in good_album_paths:
        if term in filepath:
            return True

    return False


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


def needs_new_name(filepath):
    """Check if file needs new name."""
    rename_album_paths = [
        "Childrens Songbook-Music Only",
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
    filename, file_extension = os.path.splitext(filepath)

    filename_parts = filename.split("/")
    album_path = "/".join(filename_parts[:-2]).strip()

    album_name = filename_parts[-2]

    name_parts = filename_parts[-1].split(" ")

    track_name = " ".join(name_parts[1:]).strip()
    # track_name = get_name_part(filepath)

    track_no = name_parts[0]

    return (album_path, track_name, track_no)


def remove_track_no_trailing_zero(filepath):
    """Remove track number trailing zero."""
    album_path, track_name, track_no = parse_filepath(filepath)

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

    track_no = int(track_no)

    # update file with track no
    padding_len = get_track_padding(filepath)
    new_filename = f"{track_no:0{padding_len}d} {track_name}.mp3"

    # update filename only
    new_filepath = os.path.join(os.path.dirname(filepath), new_filename)
    return new_filepath


def get_new_name(filepath):
    """Get new name for filepath."""
    trailing_zero_tracks = ["Childrens Songbook-Music Only"]

    album_path, track_name, track_no = parse_filepath(filepath)

    if "Childrens Songbook-Music Only" in filepath:
        new_filepath = use_tag_track_no(filepath)
        new_filepath = remove_track_no_trailing_zero(new_filepath)
        return new_filepath

    if "Childrens Songbook-Words and Music" in filepath:
        new_filepath = use_tag_track_no(filepath)
        new_filepath = remove_track_no_trailing_zero(new_filepath)
        return new_filepath

    return filepath

    # # # Add a few default tags
    # filepath_parts = filepath.split('/')
    # album_path = '/'.join(filepath_parts[:-2]).strip()

    # album_name = filepath_parts[-2]

    # filename = filepath_parts[-1]
    # filename_parts = filename.split(' ')

    # track_name = ' '.join(filename_parts[1:]).strip()
    # track_name = get_name_part(filepath)

    # track_no = filename_parts[0]

    # audio = File(filepath, easy=True)
    audio = File(filepath)

    # track_no = clean_track_no(filepath, track_no, padding_len)

    if audio.tags is None:
        # print(f"No tags found for {filepath}")

        # Set the tags
        # audio.add_tags()

        # # Add a few default tags
        filepath_parts = filepath.split("/")

        # album_name = filepath_parts[-2]

        filename = filepath_parts[-1]
        # filename_parts = filename.split(' ')

        # track_name = ' '.join(filename_parts[1:]).strip()
        # track_name = get_name_part(filepath)

        # track_no = filename_parts[0]
        # track_no = int(track_no)

        # # No tags found
        # # audio.add_tags()
        # Set the tags
        # audio.add(TIT2(encoding=3, text=track_name))
        # audio.add(TRCK(encoding=3, text=track_no))
        # audio.add(TPE1(encoding=3, text="John Doe"))
        # audio.add(TALB(encoding=3, text=album_name))
        # audio["title"] = track_name
        # audio["album"] = album_name
        # audio["tracknumber"] = track_no

        # new_filename = f"{track_no:0{padding_len}d} {track_name}.mp3"
        new_filename = filename

    else:

        # Extract desired metadata fields (e.g., artist and title)
        # artist = audio.get("artist", ["Unknown Artist"])[0]
        # title = audio.get("title", [track_name])[0]
        # track_no = audio.get("tracknumber", [track_no])[0]
        # track_no = clean_track_no(filepath, track_no, padding_len)

        artist = audio.tags.get("TPE1", ["Unknown Artist"])[0]
        title = audio.tags.get("TIT2", [track_name])[0]

        if use_tag_album_info(filepath):
            album_name = audio.tags.get("TALB", [album_name])[0]
        if use_tag_track_info(filepath):
            track_no = audio.tags.get("TRCK", [track_no])[0]

        padding_len = get_track_padding(filepath)
        track_no = clean_track_no(filepath, track_no, padding_len)

        # if '/' in track_no:
        #     track_no = track_no.split('/')[0]
        # track_no = int(track_no)

        track_name = title.split("—")[0].strip()
        # filename_name_part = get_name_part(filepath)

        # assert title_name_part == filename_name_part

        # Generate the new filename based on the metadata
        new_filename = f"{track_no:0{padding_len}d} {track_name}.mp3"

    track_no = int(track_no)
    assert f"{track_no:0{padding_len}d}" != "000"

    new_filepath = os.path.join(os.path.dirname(album_path), album_name, new_filename)
    # new_filepath = os.path.join(os.path.dirname(filepath), new_filename)

    return new_filepath

    # Create the new filepath by replacing the filename
    # new_filepath = os.path.join(os.path.dirname(filepath), new_filename)

    # Rename the file
    # os.rename(filepath, new_filepath)

    return new_filepath


def main():
    """Test metadata tools on files."""
    filepaths = [
        "music/Hymns-Words and Music/Restoration Pages 1-61/01 The Morning Breaks.mp3",
        "music/Hymns-Words and Music/Restoration Pages 1-61/24 Now Well Sing with One Accord.mp3",
    ]

    folder_path = "music/Hymns-Words and Music"
    folder_path = "music"
    folder_path = "music/Hymns-Music Only/Childrens Songs Pages 299-308/"
    folder_path = "music/Hymns-Words and Music"
    folder_path = "music/Hymns-Music Only"
    folder_path = "music/Hymns-Music Only/Childrens Songs Pages 299-308/"
    folder_path = "music/Book of Mormon Videos Soundtrack from First Nephi"
    folder_path = "music/Christmas at Temple Square"
    folder_path = "music/Youth Music/Especially for Youth Songs"  # sometimes ['08 2', '09 02', duplicate 01]
    folder_path = "music"
    # Ask of God 2017 Youth Album has messed up
    #     music/Youth Music/Ask of God 2017 Youth Album/10 Ask of God (2017 Mutual Theme).mp3
    # music/Youth Music/Ask of God 2017 Youth Album/100 Priceless.mp3
    # music/Youth Music/Ask of God 2017 Youth Album/110 Healing Water.mp3
    # music/Youth Music/Ask of God 2017 Youth Album/12 Ask of God (Female Version).mp3
    # music/Youth Music/Ask of God 2017 Youth Album/20 One by One.mp3
    # music/Youth Music/Ask of God 2017 Youth Album/30 What Family Means to Me.mp3
    # music/Youth Music/Ask of God 2017 Youth Album/40 Thy Will Be Done.mp3
    # music/Youth Music/Ask of God 2017 Youth Album/60 Choose to Stay.mp3
    # music/Youth Music/Ask of God 2017 Youth Album/70 I Hear His Voice.mp3
    # music/Youth Music/Ask of God 2017 Youth Album/80 Blessings.mp3
    # music/Youth Music/Ask of God 2017 Youth Album/90 Better Life.mp3

    # # has messed up
    # music/Youth Music/Ask of God 2017 Youth Album-Instrumental/101 Priceless - Minus Track.mp3
    # music/Youth Music/Ask of God 2017 Youth Album-Instrumental/11 Ask of God (2017 Mutual Theme) - Minus Track.mp3
    # music/Youth Music/Ask of God 2017 Youth Album-Instrumental/111 Healing Water - Minus Track.mp3
    # music/Youth Music/Ask of God 2017 Youth Album-Instrumental/13 Ask of God (Female Version) - Minus Track.mp3
    # music/Youth Music/Ask of God 2017 Youth Album-Instrumental/21 One by One - Minus Track.mp3
    # music/Youth Music/Ask of God 2017 Youth Album-Instrumental/31 What Family Means to Me - Minus Track.mp3
    # music/Youth Music/Ask of God 2017 Youth Album-Instrumental/41 Thy Will Be Done - Minus Track.mp3
    # music/Youth Music/Ask of God 2017 Youth Album-Instrumental/61 Choose to Stay - Minus to Stay.mp3
    # music/Youth Music/Ask of God 2017 Youth Album-Instrumental/71 I Hear His Voice - Minus Track.mp3
    # music/Youth Music/Ask of God 2017 Youth Album-Instrumental/81 Blessings - Minus Track.mp3
    # music/Youth Music/Ask of God 2017 Youth Album-Instrumental/91 Better Life - Minus Track.mp3

    track_list = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:

            filepath = os.path.join(root, file)

            if needs_new_name(filepath):

                new_filepath = get_new_name(filepath)
                # rename_file(filepath, new_filepath)
                track_list.append((filepath, new_filepath))

            else:
                track_list.append((filepath, ""))

    sorted_lst = sorted(track_list)
    for sl in sorted_lst:
        # rename_file(sl)
        # print(parse_mp3_metadata(filepath))
        print(sl)


if __name__ == "__main__":
    main()
