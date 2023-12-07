from loguru import logger

from schorle.elements.base import onclick_mapper
from schorle.proto_gen.schorle import ClickEvent


class ClickHandler:
    @classmethod
    async def handle(cls, event: ClickEvent):
        mapped = onclick_mapper.get()[event.target_id]
        logger.info(f"Handling click event {event} with {mapped}")
        await mapped()
