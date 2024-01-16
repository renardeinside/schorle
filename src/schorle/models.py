from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class HtmxHeaders(BaseModel):
    request: Annotated[bool, Field(alias="HX-Request")]
    trigger_element_id: Annotated[str, Field(alias="HX-Trigger")]
    trigger_type: Annotated[str | None, Field(None, alias="HX-Trigger-Type")]


class HtmxMessage(BaseModel):
    model_config = ConfigDict(extra="allow")
    headers: Annotated[HtmxHeaders, Field(alias="HEADERS")]
