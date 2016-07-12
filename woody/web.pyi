from typing import Optional, Set


def html_to_xhtml(
        content: str,
        omit_tags: Optional[Set[str]] = None,
        omit_attrs: Optional[Set[str]] = None
) -> str: ...


def retrieve(
        url: str,
        charset: Optional[str] = None,
        fallback_charset: Optional[str] = 'utf-8'
) -> str: ...
