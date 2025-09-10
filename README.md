# Instagram Downloader

A simple tool to download Instagram posts and entire profiles. Supports both images and videos.

## Features

- Download single Instagram posts (photos and videos)
- Download entire Instagram profiles
- User-friendly graphical interface
- No API key required

## Installation

### Option 1: Download the Executable (Windows)

1. Go to the [Releases](https://github.com/maksattulegenov/instagram-dl/releases) page
2. Download the latest `instagram_downloader.exe`
3. Double-click to run

### Option 2: Run from Source

1. Clone the repository:
```bash
git clone https://github.com/maksattulegenov/instagram-dl.git
cd instagram-dl
```

2. Install the required packages:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python instagram_downloader_v4.py
```

## Usage

1. Launch the application
2. Enter your Instagram username and password
3. To download a single post:
   - Enter the post URL (e.g., https://www.instagram.com/p/ABC123)
   - Click "Download"
4. To download a profile:
   - Enter the profile username
   - Select "Profile Download"
   - Click "Download"

Downloaded files will be saved in the `downloads` folder.

## Building from Source

To create your own executable:

1. Install PyInstaller:
```bash
pip install pyinstaller
```

2. Create the executable:
```bash
pyinstaller --onefile --noconsole --name instagram_downloader instagram_downloader_v4.py
```

The executable will be created in the `dist` folder.

## Dependencies

- requests
- beautifulsoup4
- tqdm

## License

MIT License

## Disclaimer

This tool is for personal use only. Please respect Instagram's terms of service and copyright laws.
