#!/usr/bin/python
"""Tools to manage metadata on mp3."""
from mutagen import File


def parse_mp3_metadata(filename):
    """Parse mp3 metadata."""
    metadata = {}

    try:
        audio = File(filename)
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

    except Exception as e:
        print(f"Error occurred while parsing metadata: {str(e)}")

    return metadata


def main():
    """Test metadata tools on files."""
    metadata = parse_mp3_metadata(
        "music/Go and Do: 2020 Youth Album/02 I Will Go and Do.mp3"
    )
    print(metadata)
    metadata = parse_mp3_metadata(
        "music/Go and Do: 2020 Youth Album/13 I Will Go and Do.mp3"
    )
    print(metadata)


if __name__ == "__main__":
    main()
