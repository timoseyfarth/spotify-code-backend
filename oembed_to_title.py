
def get_title(oembed_data: dict[str, ...], debug: bool=False) -> str:
    if 'title' in oembed_data:
        if debug:
            print(f"Title found in oEmbed data: {oembed_data['title']}")
        return oembed_data['title']
    else:
        raise KeyError("Title not found in oEmbed data")


if __name__ == "__main__":
    import argparse
    from url_to_oembed import get_oembed_data

    parser = argparse.ArgumentParser(description="Retrieve title from Spotify URL")
    parser.add_argument("spotify_url", help="Spotify URL to get the title from")
    parser.add_argument("--debug", action="store_true", help="Enable debug output.")

    args = parser.parse_args()

    data = get_oembed_data(args.spotify_url, debug=args.debug)

    title = get_title(data, args.debug)
    print(f"Title: {title}")
