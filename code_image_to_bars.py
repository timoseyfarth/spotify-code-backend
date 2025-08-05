from math import floor

import cv2
import os

from filter_image import preprocess_image
from data_transfer_objects import SpotifyCodeBarsDTO

SPOTIFY_CODE_BARS = 23
SPOTIFY_CODE_LEVELS = 7.0


def _get_bar_levels(image_path: str, debug: bool=False, debug_dir: str= "debug_outputs") -> list[int]:
    img = _load_image(image_path, debug=debug)
    return __get_bar_levels_internal(img, includes_album_cover=False, debug=debug, debug_dir=debug_dir)

def __get_bar_levels_internal(image: cv2.Mat, includes_album_cover: bool=False,
                              debug: bool=False, debug_dir: str= "debug_outputs") -> list[int]:
    roi_fract_bottom = 0.2 if includes_album_cover else 1
    roi_fract_right = 0.79

    roi = _roi_image(image, roi_fract_bottom, roi_fract_right, debug=debug, debug_dir=debug_dir)
    filtered = preprocess_image(roi, debug=debug, debug_dir=debug_dir)
    raw_bars, full_bar_info = _identify_bars(filtered, debug=debug, debug_dir=debug_dir)

    if len(raw_bars) != SPOTIFY_CODE_BARS and not includes_album_cover:
        if debug:
            print(f"Expected {SPOTIFY_CODE_BARS} bars, but found {len(raw_bars)}. Retrying without album cover.")
        return __get_bar_levels_internal(image, includes_album_cover=True, debug=debug, debug_dir=debug_dir)

    quantized_bars = _quantize_bars(filtered, raw_bars, full_bar_info, debug=debug, debug_dir=debug_dir)
    cleaned_bars = _clean_quantized_bars(quantized_bars, debug=debug)
    return cleaned_bars

def _load_image(image_path: str, debug: bool=False) -> cv2.Mat:
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Image not found: {image_path}")
    if debug:
        print(f"Loaded image: {image_path} with shape {img.shape}")
    return img

def _roi_image(img: cv2.Mat, roi_fraction_bottom: float, roi_fraction_right: float,
               debug: bool=False, debug_dir: str="debug_outputs") -> cv2.Mat:
    print(img.shape)
    height, width, _ = img.shape

    x0 = int(width * (1 - roi_fraction_right))
    y0 = int(height * (1 - roi_fraction_bottom))

    roi_img = img[y0:, x0:]

    if debug:
        cv2.imwrite(f"{debug_dir}/1_roi.png", roi_img)
        print(f"Extracted ROI with shape {roi_img.shape}. Saved this intermediate step to {debug_dir}/1_roi.png")

    return roi_img

def _identify_bars(img: cv2.Mat, min_height_frac: float=0.05, max_width_frac: float=0.1,
                   debug: bool=False, debug_dir: str="debug_outputs") -> (list[int], list[tuple[int, int, int, int]]):
    contours, _ = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    height, width = img.shape
    min_height = height * min_height_frac
    max_width = width * max_width_frac

    bar_full_info = []

    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if h >= min_height and w <= max_width:
            bar_full_info.append((x, y, w, h))

    bar_full_info.sort(key=lambda bar: bar[0])
    bar_heights = [h for _, _, _, h in bar_full_info]

    if debug:
        __debug_mark_identified_bars(img, bar_full_info, debug_dir)

    return bar_heights, bar_full_info

def __debug_mark_identified_bars(img: cv2.Mat, bar_full_info: list[tuple[int, int, int, int]], debug_dir: str) -> None:
    visualization = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    color = (0, 0, 255)

    for x, y, w, h in bar_full_info:
        center_top = (x + w // 2, y)
        center_bottom = (x + w // 2, y + h)
        cv2.circle(visualization, center_top, 3, color, -1)
        cv2.circle(visualization, center_bottom, 3, color, -1)
        cv2.rectangle(visualization, center_top, center_bottom, color, 1)
    cv2.imwrite(f"{debug_dir}/6_bars_identified.png", visualization)
    print(f"Identified {len(bar_full_info)} bars drawn on image (Expected {SPOTIFY_CODE_BARS}). Saved to {debug_dir}/6_bars_identified.png")

def _quantize_bars(img: cv2.Mat, bar_heights: list[int], full_bar_info: list[tuple[int, int, int, int]],
                   debug: bool=False, debug_dir: str= "debug_outputs") -> list:
    short_guard = bar_heights[0]
    long_guard = bar_heights[len(bar_heights) // 2]

    if min(bar_heights) < short_guard or max(bar_heights) > long_guard:
        raise ValueError("Bar heights are not within expected guard limits.")

    bar_span = long_guard - short_guard
    step = bar_span / SPOTIFY_CODE_LEVELS if bar_span > 0 else 1

    quantized_bars = [int(round((h - short_guard) / step)) if bar_span > 0 else 0 for h in bar_heights]

    if debug:
        __debug_number_quantize_bars(img, quantized_bars, full_bar_info, debug_dir)

    return quantized_bars

def __debug_number_quantize_bars(img: cv2.Mat, quantized_bars: list[int], full_bar_info: list[tuple[int, int, int, int]], debug_dir: str) -> None:
    visualization = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    color = (0, 0, 255)

    for (height, (x, y, w, h)) in zip(quantized_bars, full_bar_info):
        position = (x, y - 10)
        cv2.putText(visualization, str(height), position, cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

    cv2.imwrite(f"{debug_dir}/7_quantized_bars.png", visualization)
    print(f"Quantized bars visualized and saved to {debug_dir}/7_quantized_bars.png")

def _clean_quantized_bars(quantized_bars: list[int], debug: bool=False) -> list[int]:
    if len(quantized_bars) != SPOTIFY_CODE_BARS:
        raise ValueError(f"Expected {SPOTIFY_CODE_BARS} quantized bars, but got {len(quantized_bars)}.")

    if quantized_bars[0] != quantized_bars[-1]:
        raise ValueError("First and last quantized bars do not match.")

    data_bars = quantized_bars[1:-1]
    data_bars = data_bars[:10] + data_bars[11:21]

    if debug:
        print(f"Removed guards.Cleaned quantized bars to: {len(data_bars)} elements.")

    return data_bars

def _encode_octal(values):
    octal = 0
    for digit in values:
        octal = octal * 8 + digit
    return octal


def get_encoded_bars_from_image(image_path: str, debug: bool=False, debug_dir: str="debug_outputs") -> SpotifyCodeBarsDTO:
    data_bars = _get_bar_levels(image_path=image_path, debug=debug, debug_dir=debug_dir)
    octal = _encode_octal(data_bars)
    code_part1 = floor(octal / (8 ** 10))
    code_part2 = octal % (8 ** 10)

    dto = SpotifyCodeBarsDTO(
        data_bars=data_bars,
        octal_part1=code_part1,
        octal_part2=code_part2
    )
    return dto

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Detect heights of Spotify Code Bars from an image and encode them as octal"
    )
    parser.add_argument("image_path", help="Path to input image")
    parser.add_argument("--debug", default="False", action="store_true",
                        help="Enable debug output")
    parser.add_argument("--debug-dir", default="debug_outputs",
                        help="Directory for debug outputs")

    args = parser.parse_args()

    if args.debug:
        os.makedirs(args.debug_dir, exist_ok=True)

    result = get_encoded_bars_from_image(args.image_path, debug=args.debug, debug_dir=args.debug_dir)

    print(result)
