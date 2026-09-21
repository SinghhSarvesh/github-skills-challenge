from event_topic import EventTopic


class EventConsumer:
    """Consumes events from an in-memory topic."""

    def __init__(self, topic: EventTopic):
        self.topic = topic
        self.processed_events = []

    def consume(self):
        events = self.topic.get_messages()
        self.processed_events = [self.process(event) for event in events]
        return events

    def process(self, event):
        """Forward a consumed anomaly to the downstream AIOps component."""
        if event.get("type") != "ANOMALY":
            raise ValueError("Consumer received an unsupported event type")

        return {
            "service": event["service"],
            "timestamp": event.get("timestamp"),
            "issue": "; ".join(event.get("reasons", [])),
            "source_event": event
        }