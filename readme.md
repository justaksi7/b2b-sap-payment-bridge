# SAP - B2B-Partner Payments Bridge

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


## OpenAPI REST API endpoints specification

### You can view the REST API endpoints documentation by clicking on the link below:
  [View OpenAPI spec](https://code.fbi.h-da.de/aksel.kenanov/visual-computing-ak/-/blob/master/openapi.yaml?ref_type=heads)
  
## AsyncAPI events specification
### In the following you will find the message brokerage channels documentation for this project including: process flow, event schemas and a Webhook example.
### You can view the AsyncAPI events documentation by clicking on the linkt below:
  [View the AsyncAPI spec](https://justaksi7.github.io/b2b-sap-payment-bridge/)

## Data and Reliability
### Payments Core database:

**The Payments Core database consists of 3 different tables: payments,  workerOutbox and webhookOutbox**

**payments table:**
|id = string (uuid)|paymentDetails = JSONB object|status = string enum (QUEUED, FAILED, SETTLED)|createdAt = timestamp|updatedAt = timestamp|
|------------------|-----------------------------|----------------------------------------------|---------------------|---------------------|
|company12order34 |{
  "paymentDetails": {
    "transactionId": "txn_789456123",
    "amount": 99.99,
    "currency": "EUR",
    "paymentMethod": "credit_card",
    "paymentMethodDetails": {
      "cardType": "visa",
      "lastFourDigits": "1234",
      "expirationDate": "12/2025"
    },
    "billingAddress": {
      "firstName": "Max",
      "lastName": "Mustermann",
      "street": "Musterstraße 123",
      "city": "Musterstadt",
      "postalCode": "12345",
      "country": "DE"
    },
    "status": "completed",
    "createdAt": "2023-10-05T14:48:00.000Z",
    "updatedAt": "2023-10-05T14:50:30.000Z",
    "metadata": {
      "orderId": "ord_123456",
      "customerId": "cust_789",
      "invoiceNumber": "INV-2023-1005"
    }
  }
}                          |asd                                           |asd                  |asd                  |

