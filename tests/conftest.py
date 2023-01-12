from pytest import fixture

from pathlib import Path
from types import SimpleNamespace

import piculet


EXAMPLES = Path(__file__).parent.parent / "examples"


@fixture
def examples():
    """Piculet example specs and documents."""
    movie_spec = EXAMPLES / "movie.json"
    shining_doc = EXAMPLES / "shining.html"
    shining_content = shining_doc.read_text()
    shining = piculet.build_tree(shining_content)
    return SimpleNamespace(
        movie_spec=movie_spec,
        shining_doc=shining_doc,
        shining_content=shining_content,
        shining=shining,
    )
