from piculet import reducers


def test_reducer_first_should_return_first_item():
    assert reducers.first(["a", "b", "c"]) == "a"


def test_reducer_concat_should_return_concatenated_items():
    assert reducers.concat(["a", "b", "c"]) == "abc"
