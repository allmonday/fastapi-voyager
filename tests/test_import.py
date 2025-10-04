def test_import():
    import fastapi_voyager as pkg
    assert hasattr(pkg, "__version__")
