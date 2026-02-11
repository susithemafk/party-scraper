try:
    from crawl4ai import Action, CrawlerRunConfig, CacheMode
    print("Imports successful")
except ImportError as e:
    print(f"Import failed: {e}")
    import crawl4ai
    print(f"crawl4ai dir: {dir(crawl4ai)}")
