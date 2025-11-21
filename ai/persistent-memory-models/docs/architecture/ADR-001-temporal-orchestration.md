# ADR-001: Use Temporal for Workflow Orchestration

## Status
Accepted

## Context
We need a robust orchestration system for long-running ingestion workflows that can:
- Handle failures gracefully
- Resume from checkpoints
- Provide visibility into workflow execution
- Scale horizontally

## Decision
We will use Temporal as our workflow orchestration engine.

## Consequences

### Positive
- **Durability**: Workflows survive process crashes and restarts
- **Visibility**: Built-in UI for monitoring workflow execution
- **Scalability**: Can distribute work across multiple workers
- **Reliability**: Automatic retries and error handling
- **Versioning**: Support for workflow versioning and migration

### Negative
- **Complexity**: Additional infrastructure component to manage
- **Learning Curve**: Team needs to learn Temporal concepts
- **Operational Overhead**: Requires PostgreSQL and Elasticsearch

## Alternatives Considered

### Celery
- **Pros**: Simpler, widely adopted
- **Cons**: Less durable, no built-in workflow visualization

### Apache Airflow
- **Pros**: Great for batch ETL
- **Cons**: Heavier weight, designed for scheduled jobs not event-driven workflows

### AWS Step Functions
- **Pros**: Fully managed
- **Cons**: Vendor lock-in, higher cost at scale
