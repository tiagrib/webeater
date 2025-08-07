# WebEater (weat)

WebEater is a web content extraction tool designed to fetch and process web pages.
It is made for developers and researchers who need to extract structured data from web pages efficiently.
The tool goes straight to the point, focusing on extracting text and structured data from web pages,
while providing some additional configurations and hits for better efficiency and effectiveness.

It's main purpose is to serve as a go-to-component that works out of the box for most general use cases.

## Features
- Fetches web pages and extracts text content into Markdown format.
- Handles JavaScript-heavy pages using Selenium and BeautifulSoup

## Quick Start
To use WebEater, you can import the `WebeaterEngine` class and
create an instance of it. The engine will automatically load the necessary configurations
and provide methods to perform web content extraction actions.

Note that it must be loaded within an async context.

```
from webeater import WebeaterEngine

async def main():
    weat = await WebeaterEngine.create()
    content = weat.get(url="https://example.com")

    print(content)
```

## Installation

To install Web Eater, you can clone the repository and install the required dependencies.

The current code was tested using python version 3.12.3, though other versions may work.

```
pip install -r requirements.txt
```


## Configuration
Web Eater uses a configuration file to manage its settings.
The configuration file is typically located at `config/weat.yaml`.

You can customize the settings in this file to suit your needs,
such as specifying the default user agent, timeout settings, and other parameters.

    
    