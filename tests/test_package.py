from ortelius import GraphBundle, __version__, load_graph_bundle, validate_graph_bundle


def test_package_exposes_version() -> None:
    assert __version__ == "0.1.0"


def test_package_exposes_stable_core_imports() -> None:
    assert GraphBundle.__name__ == "GraphBundle"
    assert callable(load_graph_bundle)
    assert callable(validate_graph_bundle)
