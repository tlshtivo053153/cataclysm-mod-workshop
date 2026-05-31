import json


def make_json_file(tmp_path, data, filename="test.json"):
    path = tmp_path / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))
    return path
