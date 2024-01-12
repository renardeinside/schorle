from pydantic import Field


def Attribute(*args, **kwargs):  # noqa: N802
    """
    This is a helper function to make it easier to annotate attributes on elements.
    :param args: same as pydantic.Field
    :param kwargs: same as pydantic.Field
    """
    kwargs["attribute"] = True
    if "alias" in kwargs:
        kwargs["serialization_alias"] = kwargs.pop("alias")
    return Field(*args, **kwargs)
