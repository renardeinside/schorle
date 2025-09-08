"""
Type generation utilities for extracting and exporting Pydantic model schemas.
"""

import inspect
import json
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, List, Type

from pydantic import BaseModel
from pydantic.alias_generators import to_camel
from pydantic.json_schema import GenerateJsonSchema, JsonSchemaValue


class CamelCaseSchemaGenerator(GenerateJsonSchema):
    """Custom JSON Schema generator that converts field names to camelCase."""

    def generate_field_schema(
        self, schema, validation_alias, serialization_alias, field_info, **kwargs
    ):
        """Override to apply camelCase transformation to field names."""
        json_schema = super().generate_field_schema(
            schema, validation_alias, serialization_alias, field_info, **kwargs
        )
        return json_schema

    def generate_schema(self, schema, **kwargs):
        """Generate schema with camelCase field names."""
        json_schema = super().generate_schema(schema, **kwargs)
        return self._transform_to_camel_case(json_schema)

    def _transform_to_camel_case(self, schema: JsonSchemaValue) -> JsonSchemaValue:
        """Recursively transform all field names in the schema to camelCase."""
        _copy = schema.copy()
        for k, v in _copy.items():
            if k == "properties":
                _copy[k] = {
                    to_camel(k): self._transform_to_camel_case(v) for k, v in v.items()
                }
            elif k == "required":
                _copy[k] = [to_camel(k) for k in v]
            else:
                _copy[k] = self._transform_to_camel_case(v)
        return _copy


def extract_pydantic_schemas(
    module: ModuleType, output_path: Path, use_camel_case: bool = True
) -> None:
    """
    Searches for all Pydantic models in the given module and saves their JSON schemas
    to a JSON file at the specified output path.

    Args:
        module: Python module to search for Pydantic models
        output_path: Path where the JSON schemas will be saved
        use_camel_case: If True, converts field names to camelCase (default: True)

    Example:
        >>> import myapp.models
        >>> from pathlib import Path
        >>> extract_pydantic_schemas(myapp.models, Path("schemas.json"))
        >>> # For snake_case field names:
        >>> extract_pydantic_schemas(myapp.models, Path("schemas.json"), use_camel_case=False)
    """
    schemas = {}
    pydantic_models = _find_pydantic_models(module)

    # Choose schema generator based on camelCase preference
    schema_generator = (
        CamelCaseSchemaGenerator if use_camel_case else GenerateJsonSchema
    )

    for model_name, model_class in pydantic_models:
        try:
            schema = model_class.model_json_schema(schema_generator=schema_generator)
            schemas[model_name] = schema
        except Exception as e:
            print(f"Warning: Failed to generate schema for {model_name}: {e}")
            continue

    # Ensure the output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write schemas to JSON file
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(schemas, f, indent=2, ensure_ascii=False)

    print(f"Exported {len(schemas)} Pydantic model schemas to {output_path}")


def _find_pydantic_models(module: ModuleType) -> List[tuple[str, Type[BaseModel]]]:
    """
    Find all Pydantic BaseModel classes in the given module.

    Args:
        module: Python module to search

    Returns:
        List of tuples containing (model_name, model_class)
    """
    models = []

    for name, obj in inspect.getmembers(module, inspect.isclass):
        # Check if the class is defined in this module (not imported)
        if obj.__module__ == module.__name__:
            # Check if it's a Pydantic BaseModel (but not BaseModel itself)
            if (
                issubclass(obj, BaseModel)
                and obj is not BaseModel
                and not obj.__name__.startswith("_")
            ):
                models.append((name, obj))

    return models


def extract_pydantic_schemas_recursive(
    module: ModuleType,
    output_path: Path,
    include_submodules: bool = True,
    use_camel_case: bool = True,
) -> None:
    """
    Extended version that can recursively search submodules for Pydantic models.

    Args:
        module: Python module to search for Pydantic models
        output_path: Path where the JSON schemas will be saved
        include_submodules: Whether to recursively search submodules
        use_camel_case: If True, converts field names to camelCase (default: True)

    Example:
        >>> import myapp
        >>> from pathlib import Path
        >>> extract_pydantic_schemas_recursive(myapp, Path("all_schemas.json"))
        >>> # For snake_case field names:
        >>> extract_pydantic_schemas_recursive(myapp, Path("all_schemas.json"), use_camel_case=False)
    """
    schemas = {}

    # Choose schema generator based on camelCase preference
    schema_generator = (
        CamelCaseSchemaGenerator if use_camel_case else GenerateJsonSchema
    )

    # Get models from the main module
    main_models = _find_pydantic_models(module)
    for model_name, model_class in main_models:
        try:
            schema = model_class.model_json_schema(schema_generator=schema_generator)
            schemas[f"{module.__name__}.{model_name}"] = schema
        except Exception as e:
            print(
                f"Warning: Failed to generate schema for {module.__name__}.{model_name}: {e}"
            )
            continue

    # Recursively search submodules if requested
    if include_submodules and hasattr(module, "__path__"):
        import pkgutil

        for importer, modname, ispkg in pkgutil.iter_modules(
            module.__path__, module.__name__ + "."
        ):
            try:
                submodule = __import__(modname, fromlist=[""])
                submodule_models = _find_pydantic_models(submodule)

                for model_name, model_class in submodule_models:
                    try:
                        schema = model_class.model_json_schema(
                            schema_generator=schema_generator
                        )
                        schemas[f"{modname}.{model_name}"] = schema
                    except Exception as e:
                        print(
                            f"Warning: Failed to generate schema for {modname}.{model_name}: {e}"
                        )
                        continue

            except ImportError as e:
                print(f"Warning: Could not import submodule {modname}: {e}")
                continue

    # Ensure the output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write schemas to JSON file
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(schemas, f, indent=2, ensure_ascii=False)

    print(f"Exported {len(schemas)} Pydantic model schemas to {output_path}")


def get_model_schema_summary(
    module: ModuleType, use_camel_case: bool = True
) -> Dict[str, Any]:
    """
    Get a summary of Pydantic models in a module without writing to file.

    Args:
        module: Python module to analyze
        use_camel_case: If True, converts field names to camelCase (default: True)

    Returns:
        Dictionary with model names as keys and schema info as values
    """
    models = _find_pydantic_models(module)
    summary = {}

    # Choose schema generator based on camelCase preference
    schema_generator = (
        CamelCaseSchemaGenerator if use_camel_case else GenerateJsonSchema
    )

    for model_name, model_class in models:
        try:
            schema = model_class.model_json_schema(schema_generator=schema_generator)
            summary[model_name] = {
                "title": schema.get("title", model_name),
                "description": schema.get("description", ""),
                "properties": list(schema.get("properties", {}).keys()),
                "required": schema.get("required", []),
                "type": schema.get("type", "unknown"),
            }
        except Exception as e:
            summary[model_name] = {"error": str(e)}

    return summary
