def test_version(insights_client):
    proc = insights_client.run("--version")
    assert b"Client: " in proc.stdout
    assert b"Core: " in proc.stdout
