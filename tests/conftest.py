from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from triage.train import train

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def trained(tmp_path_factory):
    out = tmp_path_factory.mktemp("models")
    metrics = train(output_dir=out, test_csv=ROOT / "data" / "handwritten_test.csv")
    return out, metrics


@pytest.fixture()
def kb_dir(tmp_path):
    folder = tmp_path / "kb"
    folder.mkdir()
    (folder / "kb-a.md").write_text(
        "# Reset a password\nSteps to reset a forgotten user password and unlock an account.\n", encoding="utf-8"
    )
    (folder / "kb-b.md").write_text(
        "# Troubleshoot SSH access\nIf an ssh connection times out, check the network, the key, and the firewall.\n",
        encoding="utf-8",
    )
    return folder


@pytest.fixture()
def client(trained, kb_dir):
    app = create_app(model_dir=trained[0], kb_dir=kb_dir)
    with TestClient(app) as test_client:
        yield test_client
