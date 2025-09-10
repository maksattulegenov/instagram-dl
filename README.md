# Instagram-DL

instagram-dl - download photos and videos from Instagram

- [INSTALLATION](#installation)
- [DESCRIPTION](#description)
- [OPTIONS](#options)
- [CONFIGURATION](#configuration)
- [BUGS](#bugs)
- [COPYRIGHT](#copyright)

# INSTALLATION

There are several ways to install and run instagram-dl:

## Method 1: Download the Executable (Windows)

1. Go to https://github.com/maksattulegenov/instagram-dl/releases
2. Download the latest `instagram-dl.exe`
3. Place it anywhere on your computer
4. Double-click to run, or use from command line:
   ```
   instagram-dl.exe --help
   ```

## Method 2: Install using pip (All Platforms)

```bash
pip install instagram-dl
```

Then run using:
```bash
instagram-dl --help
```

## Method 3: Install from source (All Platforms)

```bash
git clone https://github.com/maksattulegenov/instagram-dl.git
cd instagram-dl
pip install -e .
```

## Method 4: Run without installing (All Platforms)

If you have Python 3.8 or later installed:

```bash
git clone https://github.com/maksattulegenov/instagram-dl.git
cd instagram-dl
pip install -r requirements.txt
python -m instagram_dl.cli --help
```

# DESCRIPTION

**instagram-dl** is a command-line program to download photos and videos from Instagram. It requires Python 3.8 or higher and is not platform specific. It should work on any platform that runs Python. The program can download single posts, carousel posts (multiple photos/videos), and entire profiles.

    instagram-dl [OPTIONS] URL [URL...]

## Installation

You can install instagram-dl using pip:

```bash
pip install instagram-dl
```

Or install from source:

```bash
git clone https://github.com/yourusername/instagram-dl.git
cd instagram-dl
pip install .
```

# OPTIONS

    -h, --help                           Print this help text and exit
    --version                            Print program version and exit
    -u, --username USERNAME              Instagram username for login
    -p, --password PASSWORD              Instagram password for login
    --gui                               Launch graphical user interface
    --profile                           Download entire profile instead of single post
    -o, --output TEMPLATE               Output filename template (see below)
    -v, --verbose                       Print various debugging information
    -q, --quiet                         Activate quiet mode
    --max-posts NUMBER                  Maximum number of posts to download from a profile
    -r, --rate-limit RATE               Maximum download rate in posts per hour
    -c, --continue                      Resume partially downloaded files
    -w, --no-overwrites                Do not overwrite existing files
    --download-archive FILE             Download only posts not listed in the archive file

## Download Options:
    --retries RETRIES                   Number of retries (default is 10)
    --sleep-interval SECONDS            Number of seconds to sleep between downloads
    --max-sleep-interval SECONDS        Maximum number of seconds to sleep
    
## Filesystem Options:
    -a, --batch-file FILE               File containing URLs to download
    --restrict-filenames                Restrict filenames to ASCII characters
    --no-mtime                         Do not use the Last-modified header to set file time

# CONFIGURATION

You can configure instagram-dl by placing any supported command line option to a configuration file. On Linux and macOS, the system wide configuration file is located at `/etc/instagram-dl.conf` and the user wide configuration file at `~/.config/instagram-dl/config`. On Windows, the user wide configuration file is located at `%APPDATA%\instagram-dl\config.txt`.

For example:
```
# Lines starting with # are comments

# Always use this Instagram account
-u "myusername"
-p "mypassword"

# Save files in a specific format
-o "~/Instagram/%(uploader)s/%(title)s-%(id)s.%(ext)s"

# Rate limiting
--rate-limit 60

# Resume partial downloads
-c
```

# BUGS

Bugs and suggestions should be reported at: <https://github.com/yourusername/instagram-dl/issues>

Please include the full output of instagram-dl when run with `-v`, i.e. add `-v` flag to your command line.

# COPYRIGHT

This project is licensed under the MIT License.

The MIT License (MIT)

Copyright (c) 2025 Your Name

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
