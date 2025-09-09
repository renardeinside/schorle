from schorle.json_schema import generate_schemas
from schorle.utils import schema_to_ts
from templates import models


def test_generate_schemas():
    json_schema = generate_schemas(models)
    assert json_schema is not None
    assert json_schema.startswith("{")
    assert json_schema.endswith("}")
    ts_schema = schema_to_ts(json_schema)
    assert ts_schema is not None
