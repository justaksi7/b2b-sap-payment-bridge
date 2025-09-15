# Partner Payments Bridge

## Goal

Design a resilient architecture that **decouples multiple B2B partners from SAP**. The system must guarantee:
- **Durability** (no data loss)
- **Prevention of duplicates**
- **Reliable acknowledgements** to partners even if SAP is slow or down

## Why

 - Ensure every partner request is durably stored before confirming.
 - Support multiple partners with separate authentication, limits, and mapping rules.
 - Keep the system resilient: if SAP is down or overloaded, data is queued and retried until 
successful.
 - Provide visibility (metrics, logs, dashboards).
 - Keep the system secure (auth, signed webhooks, minimal PII).
## Intended Scope
- **Reliability:**  
    Retries with exponential backoff, Dead Letter Queues, Outbox, Idempotency
- **Security:**  
    OAuth2, Signed Webhooks, minimal PII
- **Observability:**  
    Logs, Software Metrics, etc.

## Architecture Design Diagrams.
-<img src="/images/architecture-diagram.svg" width="screen" height="screen">
- Gateway is an AWS API Gateway
- AWS Lambda Fuctions: Request Dispatcher, Event Dispatcher, Worker Lambda, Webhook Lamba, Logger Lambda, Validation Lambda
- AWS SQS Queues: POST SQS, Worker SQS, Webhook SQS, Logger SQS
- AWS RDS Databases: Payments Core, Partner Config


## OpenAPI Specification
  [View OpenAPI Spec](https://code.fbi.h-da.de/aksel.kenanov/visual-computing-ak/-/blob/master/openapi.yaml?ref_type=heads)
