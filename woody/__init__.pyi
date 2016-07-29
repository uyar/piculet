from typing import Any, List, Mapping


ScrapeSpec = List[Mapping[str, Any]]


def _get_document(url: str) -> str: ...


def scrape(
        spec: ScrapeSpec,
        scraper_id: str,
        **kwargs
) -> Mapping[str, Any]: ...
