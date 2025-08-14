if __name__ == "__main__":
    import asyncio
    from weat import Webeater

    # Example usage
    WINDOW_SIZE_W = 1920
    WINDOW_SIZE_H = 1080

    async def main():
        engine = await Webeater.create()

        # user input loop until q is inserted
        while True:
            user_input = input("Enter a URL to fetch content (or 'q' to quit): ")
            if user_input.lower() == "q":
                break
            try:
                content = await engine.get(user_input)
                print(f"Content fetched from {user_input}: {content}")
            except Exception as e:
                print(f"Error fetching content: {e}")

        await engine.shutdown()

    asyncio.run(main())
