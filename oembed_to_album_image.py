import requests
from fpdf import FPDF


def _get_thumbnail_url(oembed_data: dict[str, ...], debug: bool=False) -> str:
    if 'thumbnail_url' in oembed_data:
        if debug:
            print(f"Thumbnail URL found in oEmbed data: {oembed_data['thumbnail_url']}")
        return oembed_data['thumbnail_url']
    else:
        raise KeyError("Thumbnail URL not found in oEmbed data")

def _request_album_image(thumbnail_url: str, debug: bool=False) -> bytes:
    response = requests.get(thumbnail_url)
    if response.status_code == 200:
        if debug:
            print(f"Successfully retrieved album image from URL: {thumbnail_url}")
        return response.content
    else:
        raise Exception(f"Failed to retrieve album image: {response.status_code} - {response.text}")

def _save_album_image(image_content: bytes, image_path: str, debug: bool=False) -> None:
    with open(image_path, 'wb') as f:
        f.write(image_content)

    if debug:
        print(f"Thumbnail image saved to {image_path}")

def _write_pdf_with_image_minimal(image_path: str, output_path: str, size_mm: int=20, debug: bool=False):
    pdf = FPDF(unit='mm', format=(size_mm, size_mm))
    pdf.add_page()
    pdf.image(image_path, x=0, y=0, w=size_mm, h=size_mm)
    pdf.output(output_path)

    if debug:
        print(f"PDF with size {size_mm}x{size_mm}mm created at {output_path}")

def _write_pdf_with_image_a4(image_path: str, output_path: str, size_mm: int=20, debug: bool=False):
    pdf = FPDF(unit='mm', format='A4')
    pdf.add_page()

    page_width = 210
    x = (page_width - size_mm) / 2
    y = 20

    pdf.image(image_path, x=x, y=y, w=size_mm, h=size_mm)
    pdf.output(output_path)

    if debug:
        print(f"A4 PDF created with image at {output_path} with size {size_mm}x{size_mm}mm centered on the page")


def save_album_data(oembed_data: dict[str, ...], image_path: str, pdf_a4_path: str=None,
                    pdf_minimal_path: str=None, debug: bool=False) -> None:
    thumbnail_url = _get_thumbnail_url(oembed_data, debug=debug)
    thumbnail = _request_album_image(thumbnail_url, debug=debug)

    _save_album_image(thumbnail, image_path, debug=debug)
    if pdf_a4_path:
        _write_pdf_with_image_a4(image_path, pdf_a4_path, debug=debug)
    if pdf_minimal_path:
        _write_pdf_with_image_minimal(image_path, pdf_minimal_path, debug=debug)

if __name__ == "__main__":
    import argparse
    from url_to_oembed import get_oembed_data

    parser = argparse.ArgumentParser(description="Download Spotify Thumbnail Image")
    parser.add_argument("spotify_url", help="Spotify URL to download the thumbnail image from")
    parser.add_argument("--image_path", default="thumbnail_img.png", help="Path to save the downloaded image")
    parser.add_argument("--debug", default="False", action="store_true",
                        help="Enable debug output")
    parser.add_argument("--output-pdf-a4", default="None", help="Output PDF file path A4 Size (default: None, no PDF output)")
    parser.add_argument("--output-pdf-minimal", default="None", help="Output PDF file path 32x32mm Size (default: None, no PDF output)")

    args = parser.parse_args()

    data = get_oembed_data(args.spotify_url, debug=args.debug)

    save_album_data(data, args.image_path, args.output_pdf_a4, args.output_pdf_minimal, args.debug)
