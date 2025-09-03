import asyncio
import argparse
from typing import Tuple
from webeater import Webeater
from webeater.config import WeatConfig


async def _process(engine, url, return_dict, content_only, silent=False):
    try:
        content = await engine.get(
            url, return_dict=return_dict, content_only=content_only
        )
        if silent:
            # In silent mode, only print the content result
            print(content)
        else:
            print(f"Content fetched from {url}: {content}")
    except Exception as e:
        if silent:
            # In silent mode, only print the error message without extra text
            print(f"Error: {e}")
        else:
            print(f"Error fetching content: {e}")


async def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Webeater - Web Content Extractor CLI")
    # parser.add_argument(
    #    "--nocli",
    #    help="Do not display the cli, just run once with the provided url and return toe result to the console",
    # )
    parser.add_argument("url", nargs="?", help="URL to fetch content from")
    parser.add_argument(
        "--config", "-c", default="weat.json", help="Config file to use"
    )
    parser.add_argument("--hints", nargs="*", help="Additional hint files to load")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument(
        "--silent",
        action="store_true",
        help="Silent mode - suppress all debug/info messages, only show results or errors",
    )
    parser.add_argument("--json", action="store_true", help="Return content as JSON")
    parser.add_argument(
        "--content-only", action="store_true", help="Return only content"
    )

    args = parser.parse_args()

    if args.debug:
        from webeater.log import setLogDebug

        setLogDebug(True)

    if args.silent:
        from webeater.log import setLogSilent

        setLogSilent(True)

    # Create config with all hints loaded and combined
    config = WeatConfig(
        filename=args.config, extra_hint_files=args.hints or [], debug=args.debug
    )

    # Create engine with the fully configured config
    engine = await Webeater.create(config=config)

    # Check if a URL was provided as a command line argument
    if args.url:
        url = args.url
        if not (url.startswith("http://") or url.startswith("https://")):
            if args.silent:
                print(
                    "Error: Please provide a valid URL starting with http:// or https://"
                )
            else:
                print("Please provide a valid URL starting with http:// or https://")
            await engine.shutdown()
            return
        await _process(
            engine,
            url,
            return_dict=args.json,
            content_only=args.content_only,
            silent=args.silent,
        )
    else:
        # user input loop until q is inserted
        while True:
            user_input = input("Enter a URL to fetch content (or 'q' to quit): ")
            valid_url, quit, rd, co, url = parse_input(user_input)

            if quit:
                break
            if url == "":
                continue
            if not valid_url:
                if args.silent:
                    print(
                        "Error: Please enter a valid URL starting with http:// or https://"
                    )
                else:
                    print("Please enter a valid URL starting with http:// or https://")
                continue

            await _process(
                engine,
                url,
                return_dict=rd,
                content_only=co,
                silent=args.silent,
            )

    await engine.shutdown()


def parse_input(url: str) -> Tuple[bool, bool, str]:
    """Parse the user input to determine flags and URL.

    Args:
        url (str): The user input string.

    Returns:
        tuple: A tuple containing:
            - return_dict (bool): Whether to return content as JSON.
            - content_only (bool): Whether to return only content.
            - cleaned_url (str): The cleaned URL without flags.
    """
    quit = url.lower() == "q"
    return_dict = False
    content_only = False

    cleaned_url = url.strip()

    if cleaned_url.lower().startswith("j!"):
        return_dict = True
        cleaned_url = cleaned_url[2:].strip()
    if cleaned_url.lower().startswith("c!"):
        content_only = True
        cleaned_url = cleaned_url[2:].strip()
    if cleaned_url.lower().startswith("jc!") or cleaned_url.lower().startswith("cj!"):
        return_dict = True
        content_only = True
        cleaned_url = cleaned_url[3:].strip()

    valid_url = cleaned_url.startswith("http://") or cleaned_url.startswith("https://")

    return valid_url, quit, return_dict, content_only, cleaned_url


def cli_main():
    """Entry point for console scripts"""
    asyncio.run(main())


if __name__ == "__main__":
    asyncio.run(main())
