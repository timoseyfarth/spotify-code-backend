import requests
from url_conversion import url_to_uri

def _get_request_url(spotify_uri: str, debug: bool=False) -> str:
    img_format = "jpeg"
    bg_color = "000000"
    code_color = "white"
    size = "640"
    base_url = "https://scannables.scdn.co/uri/plain"
    code_url = f"{base_url}/{img_format}/{bg_color}/{code_color}/{size}/{spotify_uri}"
    result = code_url.replace(" ", "%20")
    if debug:
        print(f"Constructed Spotify Code Request URL: {result}")
    return result

def _request_code_image(code_image_url: str, debug: bool=False) -> bytes:
    response = requests.get(code_image_url)
    if response.status_code == 200:
        if debug:
            print(f"Successfully retrieved Spotify Code Image from URL: {code_image_url}")
        return response.content
    else:
        raise Exception(f"Failed to retrieve image: {response.status_code} - {response}")

def _save_spotify_code_image(response_content: bytes, image_path: str, debug: bool=False) -> None:
    with open(image_path, 'wb') as f:
        f.write(response_content)
    if debug:
        print(f"Image saved to {image_path}")


def save_spotify_code_data(spotify_url: str, image_path: str, debug: bool=False) -> None:
    uri = url_to_uri(spotify_url)
    request_url = _get_request_url(uri, debug=debug)
    code_image = _request_code_image(request_url, debug=debug)
    _save_spotify_code_image(code_image, image_path, debug=debug)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Download Spotify Code Image")
    parser.add_argument("spotify_url", help="Spotify URL to download the code image from")
    parser.add_argument("--image_path", default="code_img.png", help="Path to save the downloaded image")
    parser.add_argument("--debug", default="False", action="store_true",
                        help="Enable debug output")

    args = parser.parse_args()

    save_spotify_code_data(args.spotify_url, args.image_path, args.debug)
