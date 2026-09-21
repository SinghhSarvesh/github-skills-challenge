# AIOps Workflow Assessment Report

## 1. Scenario

The project monitors a synthetic `payment-service`. Each operational record contains
metrics and application log information. The AIOps workflow detects slow or unhealthy
service behaviour, creates anomaly events, transports them through an in-memory event
stream, and produces a downstream issue summary.

## 2. Files and Components

| Component | File | Responsibility |
| --- | --- | --- |
| Operational data | `data/service_data.json` | Ten timestamped payment-service observations. |
| Anomaly detection | `src/anomaly_detector.py` | Checks response time, CPU, memory, and `WARNING`/`ERROR` logs. |
| Event/message | Detector result | Contains timestamp, service, type, reasons, and source record. |
| Producer | `src/event_producer.py` | Publishes an anomaly event to a topic. |
| Topic | `src/event_topic.py` | Stores messages in memory for the consumer. |
| Consumer | `src/event_consumer.py` | Receives and processes anomaly events. |
| Downstream AIOps | `src/aiops_pipeline.py` | Reports processed operational issues. |

## 3. Code Changes

The following corrections and additions are present in the final implementation:

1. The producer and consumer share the same `EventTopic("anomaly-events")` instance.
   This fixes the original routing problem where the consumer listened to a different
   topic and received no events.
2. `AnomalyDetector` treats both `WARNING` and `ERROR` logs as concerning. This fixes
   the original issue where the supplied `ERROR` incidents were not identified from
   their log level.
3. `EventConsumer.consume()` calls `process()` for every received event and stores the
   resulting downstream records in `processed_events`.
4. `EventConsumer.process()` validates anomaly events and creates an AIOps result with
   the service, timestamp, issue summary, and source event.
5. `run_pipeline()` returns `aiops_results`, and the command-line report prints the
   processed issue summaries.

## 4. Operational Data and Findings

The metric fields are `response_time_ms`, `cpu_percent`, and `memory_percent`. The log
fields are `log_level` and `message`. `timestamp` orders the observations minute by
minute from `10:00` through `10:09` on 2026-09-20.

Eight records are normal. They have response times from 120 to 150 ms, CPU from 42% to
50%, memory from 51% to 57%, and `INFO` success logs.

Two records are anomalous:

| Timestamp | Evidence | Detection reasons |
| --- | --- | --- |
| `2026-09-20T10:05:00` | 610 ms response time and `ERROR` payment timeout log | High response time; Error log detected |
| `2026-09-20T10:06:00` | 640 ms response time, 94% CPU, 91% memory, and `ERROR` database timeout log | High response time; High CPU utilization; High memory utilization; Error log detected |

No expected anomaly was missed and no normal record was incorrectly flagged.

## 5. Test Cases Added or Updated

The AIOps tests in `tests/test_aiops_pipeline.py` cover:

1. `test_normal_record_is_not_anomaly`: verifies a normal record returns no event.
2. `test_anomalous_record_is_detected`: verifies an abnormal record produces an
   `ANOMALY` event.
3. `test_producer_publishes_event`: verifies the producer places an event on the topic.
4. `test_consumer_receives_event`: verifies the consumer receives and processes a
   published event.
5. `test_pipeline_delivers_processed_event_to_aiops`: verifies the complete pipeline
   produces two downstream AIOps results and the expected issue summary.

## 6. Validation Commands and Results

Run from the repository root:

```bash
PYTHONPATH=. python3 -m pytest -q
```

Observed result:

```text
.........                                                                [100%]
9 passed in 0.02s
```

Run the complete workflow:

```bash
PYTHONPATH=.:src python3 -m src.aiops_pipeline
```

Observed result:

```text
==================================================
AIOps Pipeline Result
==================================================
Records processed: 10
Anomalies detected: 2
Events consumed: 2
AIOps results: 2

Processed AIOps Events:

Service: payment-service
Timestamp: 2026-09-20T10:05:00
Issue: High response time; Error log detected

Service: payment-service
Timestamp: 2026-09-20T10:06:00
Issue: High response time; High CPU utilization; High memory utilization; Error log detected
```

The complete verified flow is:

```text
Operational data -> AnomalyDetector -> Event -> EventProducer
-> EventTopic -> EventConsumer -> downstream AIOps result
```

## 7. Evidence Screenshots

Take screenshots in the VS Code terminal after running the commands above. The
following screenshots provide the required evidence:

- Screenshot 1: `cat data/service_data.json`, showing the metrics, logs, and timestamps.
- Screenshot 2: `PYTHONPATH=.:src python3 -m src.aiops_pipeline`, showing anomaly detection,
  event consumption, and final AIOps output.
- Screenshot 3: `PYTHONPATH=. python3 -m pytest -q`, showing `9 passed`.
- Screenshot 4: the source view showing `EventProducer`, `EventTopic`, and
  `EventConsumer` connected through the shared `anomaly-events` topic.

The command output above is also recorded here so the evidence remains understandable
when screenshots are reviewed separately.

## 8. Limitation and Improvement

The detector uses fixed thresholds and evaluates each record independently. It does not
learn a normal service baseline, correlate adjacent records, or distinguish a short spike
from a sustained incident. A rolling baseline with configurable duration and severity
rules would improve the approach.

## 9. Reproduction

1. Clone the repository and open it in VS Code or a Codespace.
2. From the repository root, run `PYTHONPATH=.:src python3 -m src.aiops_pipeline`.
3. Run `PYTHONPATH=. python3 -m pytest -q`.
4. Compare the output with the results in this report.
