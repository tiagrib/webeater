if __name__ == "__main__":
    import asyncio
    import argparse
    from weat import Webeater
    from weat.config import WeatConfig

    async def _process(engine, url, return_dict, content_only):
        try:
            content = await engine.get(
                url, return_dict=return_dict, content_only=content_only
            )
            print(f"Content fetched from {url}: {content}")
        except Exception as e:
            print(f"Error fetching content: {e}")

    async def main():
        # Parse command line arguments
        parser = argparse.ArgumentParser(
            description="Webeater - Web Content Extractor CLI"
        )
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
            "--json", action="store_true", help="Return content as JSON"
        )
        parser.add_argument(
            "--content-only", action="store_true", help="Return only content"
        )

        args = parser.parse_args()

        if args.debug:
            from weat.log import setLogDebug

            setLogDebug(True)

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
                print("Please provide a valid URL starting with http:// or https://")
                await engine.shutdown()
                return
            await _process(
                engine, url, return_dict=args.json, content_only=args.content_only
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
                    print("Please enter a valid URL starting with http:// or https://")
                    continue

                await _process(
                    engine,
                    url,
                    return_dict=rd,
                    content_only=co,
                )

        await engine.shutdown()

    from typing import Tuple

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
        if cleaned_url.lower().startswith("jc!") or cleaned_url.lower().startswith(
            "cj!"
        ):
            return_dict = True
            content_only = True
            cleaned_url = cleaned_url[3:].strip()

        valid_url = cleaned_url.startswith("http://") or cleaned_url.startswith(
            "https://"
        )

        return valid_url, quit, return_dict, content_only, cleaned_url

    asyncio.run(main())
