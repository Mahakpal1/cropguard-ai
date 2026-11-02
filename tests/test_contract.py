import json

import yaml

from backend.app.config import Settings
from backend.app.main import create_app
from tests.conftest import ROOT


def test_openapi_paths_match_contract(tmp_path):
    app = create_app(Settings(db_path=tmp_path / "c.db", frontend_dir=tmp_path / "none"))
    live = {(p, m.upper()) for p, ops in app.openapi()["paths"].items() for m in ops}
    spec = yaml.safe_load(open(ROOT / "contracts" / "api.openapi.yaml"))
    promised = {(p, m.upper()) for p, ops in spec["paths"].items() for m in ops}
    assert live == promised, f"contract and implementation differ: {live ^ promised}"


def test_predict_status_values_match():
    spec = yaml.safe_load(open(ROOT / "contracts" / "api.openapi.yaml"))
    from backend.app.schemas import PredictResponse
    code = set(PredictResponse.model_json_schema()["properties"]["status"]["enum"])
    assert code == set(spec["components"]["schemas"]["PredictResponse"]["properties"]["status"]["enum"])


def test_class_list_is_the_single_source_of_truth():
    cls = json.load(open(ROOT / "contracts" / "class_names.json", encoding="utf-8"))["classes"]
    ids = [c["id"] for c in cls]
    assert len(ids) == len(set(ids)) == 15
