from typing import Annotated

from pydantic import BaseModel, Field


class HtmxHeaders(BaseModel):
    request: Annotated[bool, Field(alias="HX-Request")]
    trigger: Annotated[str, Field(alias="HX-Trigger")]


class HtmxMessage(BaseModel):
    headers: Annotated[HtmxHeaders, Field(alias="HEADERS")]
