from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class HtmxHeaders(BaseModel):
    request: Annotated[bool, Field(alias="HX-Request")]
    trigger: Annotated[str, Field(alias="HX-Trigger")]


class HtmxMessage(BaseModel):
    model_config = ConfigDict(extra="allow")
    headers: Annotated[HtmxHeaders, Field(alias="HEADERS")]
