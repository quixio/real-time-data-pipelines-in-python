from typing import Dict
import os
import logging

from quixstreams import Application

logger = logging.getLogger()


class ProducerWrapper:
    """
    Wrapper around the Quix Streams Producer
    """

    def __init__(self, kafka_topic: str):

        app = Application(broker_address=os.getenv("KAFKA_BROKER_ADDRESS", None))
        self._topic = app.topic(name=kafka_topic, value_serializer="json")
        self._producer = app.get_producer()

    def produce(
        self,
        key,
        value: Dict[str, any],
        headers=None,
        timestamp=None
    ):
        msg = self._topic.serialize(
            key=key,
            value=value,
            headers=headers,
            timestamp_ms=timestamp
        )
        self._producer.produce(
            topic=self._topic.name,
            headers=msg.headers,
            key=msg.key,
            value=msg.value,
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._producer.__exit__(exc_type, exc_value, traceback)