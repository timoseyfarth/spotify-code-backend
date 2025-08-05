import cv2


def preprocess_image(img: cv2.Mat, debug: bool=False, debug_dir: str="debug_outputs") -> cv2.Mat:
    gray = _grayscale(img, debug=debug, debug_dir=debug_dir)
    th = _top_hat(gray, debug=debug, debug_dir=debug_dir)
    otsu = _otsu_threshold(th, debug=debug, debug_dir=debug_dir)
    closed = _closing(otsu, debug=debug, debug_dir=debug_dir)

    return closed

def _grayscale(img: cv2.Mat, debug: bool=False, debug_dir: str= "debug_outputs") -> cv2.Mat:
    gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    if debug:
        cv2.imwrite(f"{debug_dir}/2_gray.png", gray_img)
        print(f"Converted image to grayscale. Saved this intermediate step to {debug_dir}/2_gray.png")

    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

def _top_hat(img: cv2.Mat, kernel_size: tuple[int, int]=(15, 1),
             debug: bool=False, debug_dir: str="debug_outputs") -> cv2.Mat:
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, kernel_size)
    top_hat_img = cv2.morphologyEx(img, cv2.MORPH_TOPHAT, kernel)
    if debug:
        cv2.imwrite(f"{debug_dir}/3_top_hat.png", top_hat_img)
        print(f"Applied Top-Hat transformation with kernel size {kernel_size}. Saved this intermediate step to {debug_dir}/3_top_hat.png")

    return top_hat_img

def _otsu_threshold(img: cv2.Mat, debug: bool=False, debug_dir: str= "debug_outputs") -> cv2.Mat:
    threshold, otsu_img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    if debug:
        cv2.imwrite(f"{debug_dir}/4_otsu.png", otsu_img)
        print(f"Applied Otsu's thresholding with optimal threshold {threshold}. Saved this intermediate step to {debug_dir}/4_otsu.png")

    return otsu_img

def _closing(img: cv2.Mat, kernel_size: tuple[int, int]=(3, 7),
             debug: bool=False, debug_dir: str="debug_outputs") -> cv2.Mat:
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, kernel_size)
    closed_img = cv2.morphologyEx(img, cv2.MORPH_CLOSE, kernel)
    if debug:
        cv2.imwrite(f"{debug_dir}/5_closing.png", closed_img)
        print(f"Applied morphological closing with kernel size {kernel_size}. Saved this intermediate step to {debug_dir}/5_closing.png")

    return closed_img
