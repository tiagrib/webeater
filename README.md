<img src="img/logo.png" alt="Logo" style="max-height: 100px;">

# WebEater (weat)

WebEater is a web content extraction tool designed to fetch and process web pages.\
It is made for developers and researchers who need to extract structured data from web pages efficiently.\
The tool goes straight to the point, focusing on extracting text and structured data from web pages,
while providing some additional configurations and hits for better effectiveness.

Its main purpose is to serve as a go-to-component that works out of the box for most general use cases.

As it's currently at an early stage, it may not cover all edge cases or complex scenarios.\
We welcome contributions and feedback to help improve its capabilities.

## Main Features
- Fetches web pages and extracts text content into Markdown format.
- Return clean, plain text or a JSON object optionally containing lists of images and links found on the page.
- Handles JavaScript-heavy pages using Selenium and BeautifulSoup
- Can be used both as a library and a command-line tool (CLI).

## Quick Start (CLI)
To use WebEater from the command line, first install it using `pip`:

```
pip install webeater
```

Then, you can run it with a URL using the `weat` CLI tool

```
weat https://example.com
```

This will fetch the content of the page and print the extracted text to the console.

### CLI Options
You can customize the behavior of WebEater using various command-line options:

- url (positional): URL to fetch content from. If omitted, WebEater starts an interactive prompt.
- -c, --config FILE (default: weat.json): Config file to use.
- --hints FILE [FILE ...]: Additional hint files to load (space-separated paths).
- --debug: Enable debug logging.
- --silent: Silent mode — suppress debug/info messages; only print results or errors to allow calling from scripts or subprocesses.
- --json: Return content as JSON instead of plain text.
- --content-only: Return only the main extracted content (skip extracting links and images).

Examples:

```
# Basic usage
webeater https://example.com

# JSON output and content-only
webeater --json --content-only https://example.com

# Using a custom config and multiple hint files
webeater -c weat.json --hints hints/news.json hints/sports.json https://example.com
```

Interactive mode (when no URL is provided):

- Enter a URL when prompted to fetch content.
- Prefix shortcuts per request:
    - j!<url> → return JSON
    - c!<url> → content only
    - jc!<url> or cj!<url> → JSON + content only
- q → quit the interactive session

Notes:

- URLs must start with http:// or https://.
- In silent mode, only the result or an error line (prefixed with "Error:") is printed.


## Quick Start (Python)
To use WebEater, first install it using `pip`:

```
pip install webeater
```

You can then import the `Webeater` class and
create an instance of it.\
The engine will automatically load the necessary configurations
and provide methods to perform web content extraction actions.

Note that it must be loaded within an async context.

Below is a minimal example:

```
import asyncio
from webeater import Webeater

async def main():
    weat = await Webeater.create()
    content = await weat.get(url="https://example.com")
    print(content)

asyncio.run(main())
```

## Help and Contributions

For questions or discussions about changes and new features, please start a new [Discussion in the Webeater GitHub repository](https://github.com/tiagrib/webeater/discussions).

If you find bugs or want to contribute, please open an [Issue](https://github.com/tiagrib/webeater/issues).

## Develop with Source

To develop with WebEater from source code, you can clone the repository at:
```
https://github.com/tiagrib/webeater.git
```

then navigate to the project directory and install the required dependencies:

```
pip install -r requirements.txt
```
The current code was tested using python version 3.12.3, though other versions may work.


## Configuration and Advanced documentation
Web Eater uses a configuration file to manage its settings.
The configuration file is typically located at `config/weat.yaml`.

You can customize the settings in this file to suit your needs,
such as specifying the default user agent, timeout settings, and other parameters.

For more detailed documentation on configuration options and advanced usage,
please refer to the [Hints Documentation](hints/README.md).

    
    