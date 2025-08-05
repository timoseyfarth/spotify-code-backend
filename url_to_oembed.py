import requests


def _get_request_url(spotify_url: str, debug: bool=False) -> str:
    base_url = "https://open.spotify.com/oembed?url="
    oembed_url = base_url + spotify_url
    result = oembed_url.replace(" ", "%20")
    if debug:
        print(f"Constructed oEmbed Request URL: {result}")

    return result

def _request_oembed(oembed_url: str, debug: bool=False) -> dict[str, ...]:
    response = requests.get(oembed_url)
    if response.status_code == 200:
        if debug:
            print(f"Successfully retrieved oEmbed data: {response.json()} from URL: {oembed_url}")
        return response.json()
    else:
        raise Exception(f"Failed to retrieve oEmbed data: {response.status_code} - {response.text}")


def get_oembed_data(spotify_url: str, debug: bool=False) -> dict[str, ...]:
    oembed_url = _get_request_url(spotify_url, debug)
    return _request_oembed(oembed_url, debug)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Retrieve oEmbed data for a Spotify URL.")
    parser.add_argument("spotify_url", type=str, help="The Spotify URL to retrieve oEmbed data for.")
    parser.add_argument("--debug", action="store_true", help="Enable debug output.")

    args = parser.parse_args()

    data = get_oembed_data(args.spotify_url, args.debug)
    print(data)