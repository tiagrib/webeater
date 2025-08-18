if __name__ == "__main__":
    import asyncio
    import sys
    from weat import Webeater

    # Example usage
    WINDOW_SIZE_W = 1920
    WINDOW_SIZE_H = 1080

    async def _process(engine, url):
        try:
            content = await engine.get(url)
            print(f"Content fetched from {url}: {content}")
        except Exception as e:
            print(f"Error fetching content: {e}")

    async def main():
        engine = await Webeater.create()

        # Check if a URL was provided as a command line argument
        if len(sys.argv) > 1:
            url = sys.argv[1]
            if not (url.startswith("http://") or url.startswith("https://")):
                print("Please provide a valid URL starting with http:// or https://")
                await engine.shutdown()
                return
            await _process(engine, url)
            
            
        else:
            # user input loop until q is inserted
            while True:
                user_input = input("Enter a URL to fetch content (or 'q' to quit): ")
                if user_input.lower() == "q":
                    break
                if user_input.strip() == "":
                    continue
                if not (
                    user_input.startswith("http://") or user_input.startswith("https://")
                ):
                    print("Please enter a valid URL starting with http:// or https://")
                    continue
                await _process(engine, user_input.strip())

        await engine.shutdown()

    asyncio.run(main())
