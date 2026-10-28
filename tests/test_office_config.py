import yaml

import office_config as oc


def test_office_config_name(tmp_path, monkeypatch):
    path = tmp_path / "office.yaml"
    path.write_text(yaml.safe_dump({"name": "Pixel HQ", "sign": {"show": True}}), encoding="utf-8")
    monkeypatch.setattr(oc, "OFFICE_CONFIG_PATH", str(path))
    view = oc.reload_office_config().public_view()
    assert view["name"] == "Pixel HQ"
    assert view["sign"]["show"] is True
