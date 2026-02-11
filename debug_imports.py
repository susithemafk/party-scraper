import sys
print("Starting imports...", flush=True)
try:
    import asyncio
    print("Imported asyncio", flush=True)
    import crawl4ai
    print("Imported crawl4ai", flush=True)
    from crawl4ai import AsyncWebCrawler
    print("Imported AsyncWebCrawler", flush=True)
    import google.generativeai
    print("Imported google.generativeai", flush=True)
except Exception as e:
    print(f"Error during imports: {e}", flush=True)

print("Imports complete.", flush=True)
