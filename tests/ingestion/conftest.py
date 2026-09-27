import pytest


class FakeConnection:
    """Stands in for a psycopg connection and records whether it was closed."""

    def __init__(self):
        self.closed = False

    def rollback(self):
        pass

    def close(self):
        self.closed = True


@pytest.fixture
def fake_connection():
    return FakeConnection()


@pytest.fixture
def bad_header_csv(tmp_path, monkeypatch):
    """Run the test from a temp folder whose CSV files all have the wrong header."""
    csv_dir = tmp_path / "data" / "raw"
    csv_dir.mkdir(parents=True)
    for name in ["customers", "products", "orders", "order_items"]:
        (csv_dir / f"{name}.csv").write_text("wrong,header\n1,2\n")
    monkeypatch.chdir(tmp_path)
