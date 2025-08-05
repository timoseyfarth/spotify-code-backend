import numpy as np
from sklearn.cluster import KMeans
import webcolors
import cv2
from data_transfer_objects import AlbumImageColorDTO, ColorDTO


def _get_mean_color(image_path: str, debug: bool=False) -> tuple[int, int, int]:
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Could not read image from {image_path}")

    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    mean = np.mean(image_rgb, axis=(0, 1))
    result_tuple = tuple(int(c) for c in mean)
    if debug:
        print(f"Mean color for {image_path}: {result_tuple}")
    return result_tuple

def _get_prominent_colors(image_path: str, n_colors: int=5, min_saturation: float=0.2,
                          min_brightness: float=0.2, debug: bool=False) -> list[tuple[int, int, int]]:
    img = cv2.imread(image_path)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    pixels = img_rgb.reshape(-1, 3)
    kmeans = KMeans(n_clusters=n_colors).fit(pixels)
    centers = np.round(kmeans.cluster_centers_).astype(int)

    prominent_colors = []
    for rgb in centers:
        hsv = cv2.cvtColor(np.uint8([[rgb]]), cv2.COLOR_RGB2HSV)[0][0]
        s, v = hsv[1]/255.0, hsv[2]/255.0
        if s > min_saturation and v > min_brightness:
            prominent_colors.append(tuple(rgb))

    if debug:
        print(f"Found {len(prominent_colors)} prominent colors with min saturation: {min_saturation} "
              f"and min brightness: {min_brightness}: {prominent_colors}")

    return prominent_colors

def _get_accent_color(image_path: str, debug: bool=False) -> tuple[int, int, int]:
    prom_colors = _get_prominent_colors(image_path, debug=debug)

    if len(prom_colors) == 0:
        if debug:
            print(f"No prominent colors found in {image_path}. Falling back to mean color.")
        return _get_mean_color(image_path, debug=debug)
    else:
        result_tuple = tuple(int(c) for c in prom_colors[0])
        if debug:
            print(f"Using first prominent color: {result_tuple} from {image_path}")
        return result_tuple

def _get_code_color(rgb_color: tuple[int, int, int], debug: bool=False) -> tuple[int, int, int]:
    r, g, b = rgb_color
    r /= 255
    g /= 255
    b /= 255

    total_lum = 0.2126 * _luminance(r) + 0.7152 * _luminance(g) + 0.0722 * _luminance(b)
    contrast_black = (total_lum + 0.05) / 0.05
    contrast_white = 1.05 / (total_lum + 0.05)
    result_color = (0, 0, 0) if contrast_black > contrast_white else (255, 255, 255)

    if debug:
        print(f"Calculated code color for accent color: {rgb_color}: {result_color}. Contrast black: {contrast_black}, "
              f"Contrast white: {contrast_white}")

    return result_color

def _luminance(c: float) -> float:
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

def _rgb_to_hex(color: tuple[int, int, int]) -> str:
    return "#{:02x}{:02x}{:02x}".format(*color)

def _closest_color_name(rgb_tuple: tuple[int, int, int]) -> str:
    min_colors = {}
    for name in webcolors.names("css3"):
        r_c, g_c, b_c = webcolors.name_to_rgb(name)
        rd = (r_c - rgb_tuple[0]) ** 2
        gd = (g_c - rgb_tuple[1]) ** 2
        bd = (b_c - rgb_tuple[2]) ** 2
        min_colors[(rd + gd + bd)] = name
    return min_colors[min(min_colors.keys())]

def _get_color_name(rgb_tuple: tuple[int, int, int], debug: bool=False) -> str:
    try:
        result_name = webcolors.rgb_to_name(rgb_tuple)

        if debug:
            print(f"Exact color name for {rgb_tuple}: {result}")

        return result_name
    except ValueError:
        result_name = _closest_color_name(rgb_tuple)

        if debug:
            print(f"No exact color name for {rgb_tuple}. Using closest name: {result_name}")

        return result_name


def get_colors_from_image(image_path: str, debug: bool=False) -> AlbumImageColorDTO:
    if debug:
        print(f"Processing image: {image_path}")
        print("Calculating accent color...")
    accent_color = _get_accent_color(image_path)
    accent_hex = _rgb_to_hex(accent_color)
    accent_name = _get_color_name(accent_color)

    if debug:
        print(f"Accent color: {accent_color}, Hex: {accent_hex}, Name: {accent_name}")
        print("Calculating code color...")
    code_color = _get_code_color(accent_color)
    code_hex = _rgb_to_hex(code_color)
    code_name = _get_color_name(code_color)

    if debug:
        print(f"Code color: {code_color}, Hex: {code_hex}, Name: {code_name}")

    accent_dto = ColorDTO(
        rgb=accent_color,
        hex=accent_hex,
        name=accent_name
    )
    code_dto = ColorDTO(
        rgb=code_color,
        hex=code_hex,
        name=code_name
    )
    dto = AlbumImageColorDTO(
        accent_color=accent_dto,
        code_color=code_dto
    )
    return dto

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Get accent color and code color from an album image")
    parser.add_argument("image_path", help="Path to the input image")
    parser.add_argument("--debug", default="False", action="store_true",
                        help="Enable debug output")
    args = parser.parse_args()

    result = get_colors_from_image(args.image_path)

    print(result)
