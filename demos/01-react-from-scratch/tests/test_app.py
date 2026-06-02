def test_app_builds_demo_object():
    import app

    assert app.demo is not None
    assert callable(app.run_fn)
