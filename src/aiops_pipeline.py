import json

from anomaly_detector import AnomalyDetector
from event_consumer import EventConsumer
from event_producer import EventProducer
from event_topic import EventTopic


def load_data(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def run_pipeline(file_path):
    data = load_data(file_path)

    anomaly_topic = EventTopic("anomaly-events")

    detector = AnomalyDetector()
    producer = EventProducer(anomaly_topic)
    consumer = EventConsumer(anomaly_topic)

    detected_events = []

    for record in data:
        event = detector.detect(record)

        if event:
            producer.publish(event)
            detected_events.append(event)

    consumed_events = consumer.consume()

    return {
        "records_processed": len(data),
        "anomalies_detected": detected_events,
        "events_consumed": consumed_events,
        "aiops_results": consumer.processed_events
    }


if __name__ == "__main__":
    result = run_pipeline("data/service_data.json")

    print("=" * 50)
    print("AIOps Pipeline Result")
    print("=" * 50)

    print(f"Records processed: {result['records_processed']}")
    print(f"Anomalies detected: {len(result['anomalies_detected'])}")
    print(f"Events consumed: {len(result['events_consumed'])}")
    print(f"AIOps results: {len(result['aiops_results'])}")

    print("\nProcessed AIOps Events:")

    for result in result["aiops_results"]:
        print(f"\nService: {result['service']}")
        print(f"Timestamp: {result['timestamp']}")
        print(f"Issue: {result['issue']}")