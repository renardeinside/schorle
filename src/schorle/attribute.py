from pydantic import Field


def Attribute(*args, **kwargs):  # noqa: N802
    """
    This is a helper function to make it easier to annotate attributes on elements.
    :param args: same as pydantic.Field
    :param kwargs: same as pydantic.Field
    """
    if "alias" in kwargs:
        attribute_name = kwargs.pop("alias")
    else:
        attribute_name = None

    kwargs["json_schema_extra"] = {"attribute_name": attribute_name, "attribute": True}
    return Field(*args, **kwargs)
