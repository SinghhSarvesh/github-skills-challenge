# GitHub Challenge

<img src="https://octodex.github.com/images/Professortocat_v2.png" align="right" height="200px" />

Hey there!

Your challenge is ready.
Follow the instructions provided for this challenge and complete the required tasks in this repository.

Make sure your work is committed and pushed to your repository before submission.

Good luck!



&copy; 2025 GitHub &bull; [Code of Conduct](https://www.contributor-covenant.org/version/2/1/code_of_conduct/code_of_conduct.md) &bull; [MIT License](https://gh.io/mit)

# AIOps Payment Service Assessment

This repository contains a small Python simulation of monitoring and responding
to a `payment-service`. The service processes payment requests and exposes
response-time, CPU, and memory telemetry together with application log fields.

The operational problem is a short-lived service degradation: requests time out
while CPU and memory utilization rise, and the service also reports database
connection trouble. AIOps is used here to correlate those metric and log signals,
identify abnormal records, and move an actionable anomaly event through a
producer/topic/consumer workflow.

## Repository Components

| Component | Location | Purpose |
| --- | --- | --- |
| Operational data | [`data/service_data.json`](data/service_data.json) | Ten timestamped `payment-service` observations. |
| Metrics and logs | [`data/service_data.json`](data/service_data.json) | Metrics are `response_time_ms`, `cpu_percent`, and `memory_percent`; log data is `log_level` and `message`. `timestamp` identifies when each observation occurred. |
| Anomaly detection | [`src/anomaly_detector.py`](src/anomaly_detector.py) | Applies fixed thresholds and flags concerning `WARNING` or `ERROR` log levels. |
| Event production | [`src/event_producer.py`](src/event_producer.py) | Publishes a detected event to an in-memory topic. |
| Event topic | [`src/event_topic.py`](src/event_topic.py) | Stores published messages in memory and returns them to consumers. |
| Event consumption | [`src/event_consumer.py`](src/event_consumer.py) | Reads anomaly events from the topic. |
| Final AIOps processing | [`src/aiops_pipeline.py`](src/aiops_pipeline.py) | Loads data, invokes detection, publishes anomalies, consumes them, and prints the final report. |

`src/calculations.py` is an unrelated example module covered by the original
unit tests; it is not part of the AIOps path.

## Operational Data Analysis

The timestamps are ISO-like minute timestamps from `10:00` through `10:09` on
2026-09-20. They provide ordering and let the anomaly report identify exactly
when the service changed behavior. All records belong to `payment-service`.

### Normal observations

Records from `10:00` through `10:04` and `10:07` through `10:09` are normal:

- response time stays between 120 and 150 ms;
- CPU stays between 42% and 50%;
- memory stays between 51% and 57%; and
- the log level is `INFO` with a successful payment message.

### Unusual observations

- `10:05`: response time is 610 ms, the log level is `ERROR`, and the message is
	`Payment service timeout`. CPU is 75% and memory is 70%, both elevated but
	below the configured 80% thresholds.
- `10:06`: response time is 640 ms, CPU is 94%, memory is 91%, and the log level
	is `ERROR` with `Database connection timeout`. This is the strongest anomaly.

The detector thresholds are response time greater than 500 ms, CPU greater than
80%, and memory greater than 80%. The data therefore contains two anomalous
observations and eight normal observations.

## Detection Findings

The final detector report contains two events:

| Timestamp | Service | Reasons |
| --- | --- | --- |
| `2026-09-20T10:05:00` | `payment-service` | High response time; Error log detected |
| `2026-09-20T10:06:00` | `payment-service` | High response time; High CPU utilization; High memory utilization; Error log detected |

No expected anomaly in the supplied data was missed, and no normal observation
was flagged. Each event includes its timestamp, service, anomaly type, reasons,
and complete source record, which makes the result explainable.

One limitation is that the detector uses static thresholds and evaluates each
record independently. It does not learn a service baseline, correlate adjacent
records, or distinguish a short spike from a sustained incident. A possible
improvement would be a rolling baseline or configurable alert policy with
duration and severity rules.

## Event-Processing Flow

The end-to-end path is:

```text
service_data.json
		-> AnomalyDetector.detect(record)
		-> anomaly event
		-> EventProducer.publish(event)
		-> shared EventTopic("anomaly-events")
		-> EventConsumer.consume()
		-> AIOps pipeline result and report
```

The producer and consumer must use the same topic instance. The original
workflow created separate `service-events` and `anomaly-events` topics, so the
consumer received zero messages. That was corrected by sharing one
`anomaly-events` topic. The original detector checked only `WARNING`, while the
provided incidents use `ERROR`; it now treats both levels as concerning.

## Final Execution

Run the workflow from the repository root:

```bash
PYTHONPATH=.:src python3 -m src.aiops_pipeline
```

The verified result is:

```text
Records processed: 10
Anomalies detected: 2
Events consumed: 2
```

The consumed events are the `10:05` payment timeout and the `10:06` database
connection timeout, with the metric and log reasons shown above. This confirms
the complete path from operational data through detection, event generation,
publication, consumption, and final AIOps output.

## Validation

The focused end-to-end check can be run with:

```bash
PYTHONPATH=.:src python3 - <<'PY'
from src.aiops_pipeline import run_pipeline

result = run_pipeline("data/service_data.json")
assert result["records_processed"] == 10
assert len(result["anomalies_detected"]) == 2
assert len(result["events_consumed"]) == 2
assert result["events_consumed"] == result["anomalies_detected"]
PY
```

The provided tests can be run with:

```bash
PYTHONPATH=. python3 -m pytest -q
```

