import asyncio
import platform
from crawl4ai import AsyncWebCrawler


async def main():
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(url="https://artbar.club/program/")
        print(f"Success! Content length: {len(result.html)}")

if __name__ == "__main__":
    asyncio.run(main())
