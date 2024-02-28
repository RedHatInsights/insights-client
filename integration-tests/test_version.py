def test_version(insights_client):
    proc = insights_client.run("--version")
    assert "Client: " in proc.stdout
    assert "Core: " in proc.stdout
