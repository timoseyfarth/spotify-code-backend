# Spotify Code Generator - Backend

[![License](https://img.shields.io/github/license/timoseyfarth/smoothiepy)](https://github.com/timoseyfarth/spotify-code-backend/blob/main/LICENSE)
[![](https://img.shields.io/badge/GitHub-Frontend-blue)](https://github.com/timoseyfarth/spotify-code-frontend)
[![](https://img.shields.io/badge/GitHub-Main%20Repo-white)](https://github.com/timoseyfarth/spotify-code-project)

Turn your favorite Spotify tracks, albums, or playlists into a unique, scannable 3D model! This project combines a web app with a parametric 3D modeling on MakerWorld to create personalized Spotify Tags.

[MakerWorld 3D Model Link](https://makerworld.com/en/models/1660269-customizable-spotify-keychain-tag) • [Live Code Generator Website](https://spotify-code.seyfarth.dev/)

---

This repository contains the backend server for the 3D Printable Spotify Code Generator. It's a Python application that takes a Spotify URL, fetches the code, processes the image, and returns the Base-8 encoded strings.

---

## 📦 Python Modules

The functionality is split into separate python modules. Each module can be run on its own. But beware: Some modules depend on the result of other modules as input. But you can always run them one after the other and paste the corresponding input as parameters. For usage instructions of any python module run:
```bash
python <name>.py -h
```

For example, if you want to test the fetching from the Spotify URL to the Spotify Code Image you can use the  `url_to_code_image.py`

```bash
python url_to_code_image.py --help
```

This will return usage instructions:
```Console
usage: url_to_code_image.py [--image_path IMAGE_PATH] [--debug] spotify_url

Download Spotify Code Image

positional arguments:
  spotify_url               Spotify URL to download the code image from

options:
  --image_path IMAGE_PATH   Path to save the downloaded image
  --debug                   Enable debug output
```

An example on how to run this python module:
```bash
python url_to_code_image.py https://open.spotify.com/track/4PTG3Z6ehGkBFwjybzWkR8
```

### Each module explained

* `album_image_to_colors.py`
    Analyzes a locally saved album cover to generate a matching color palette (HEX, RGB, and names) and suggests a contrasting color for the Spotify code.

* `code_image_to_bars.py`
    Processes a Spotify code image file, using image recognition to detect the vertical bars and measure their height levels for data encoding.

* `oembed_to_album_image.py`
    Parses the JSON response from Spotify's oEmbed API to extract the direct URL for the album or track's cover image. Furthermore creates two PDF files with the album image centered on the page.

* `oembed_to_title.py`
    Parses the JSON response from Spotify's oEmbed API to extract the title of the song, album, or playlist.

* `url_conversion.py`
    A utility that converts a standard Spotify share URL (e.g., `https://open.spotify.com/...`) into a Spotify URI format (e.g., `spotify:track:...`) for use in other API calls.

* `url_to_code_image.py`
    Takes a Spotify URL and fetches the corresponding scannable Spotify code image, saving it as a local file.

* `url_to_oembed.py`
    Queries Spotify's oEmbed API with a given URL to retrieve metadata about the content.

---

## ✨ Features

* To aid in troubleshooting and ensure application stability, the backend maintains a local log of incoming requests. A lightweight SQLite database is used to record the timestamp and the requested Spotify URL.

---

## 🚀 Getting Started

(Note: These instructions are optimized for Windows and not tested on other OS's)

1. Clone the repo to your local machine
```bash
git clone git@github.com:timoseyfarth/spotify-code-backend.git
cd spotify-code-backend
```

2. Create a virtual environment
```bash
python -m venv .venv
.venv\Scripts\activate
```

3. Install the requirements from the `requirements.txt`
```bash
pip install -r requirements.txt
```

4. Set up environment variables

Create a `.env` file in the root directory. See `.env.example` for a default local setup. If this configuration fits for you rename the file to `.env`.

5. Run the Uvicorn application locally
```bash
uvicorn core:app --reload
```

6. Make requests via Swagger (you can reach the available endpoints if you append `/docs` to the local Uvicorn URL). Or make the run the frontend and make requests directly via the website locally. (More information in the [frontend repo](https://github.com/timoseyfarth/spotify-code-frontend))

## 👨‍💻 A Note from the Creator

This project was a fantastic learning experience. It was my first time trying to setup a API from scratch. Therefore it may not be perfect. It was a personal challenge to handle external services like the Spotify API, and dive into the logic of image processing and data encoding. I'm proud of how it turned out and hope you enjoy using it!


