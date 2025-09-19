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
|company12order34 |{"paymentDetails":{} } |QUEUED |	1758264781  |	1758264781             |

**Constraints and keys:**

- id = string (uuid) - This is the primary key with unique constraint. It is a combination of the company identifier and the order identifier. a paymentDetails column could look like this for example: `{
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
    "createdAt": "2023-10-05T14:48:00.000Z",
    "updatedAt": "2023-10-05T14:50:30.000Z",
    "metadata": {
      "orderId": "ord_123456",
      "customerId": "cust_789",
      "invoiceNumber": "INV-2023-1005"
    }
  }
}`
- paymentDetails = JSONB object - This is the object that holds the actual payment details. It is a required column.
- status = string enum - This is the status of the payment and it is a required column.
- createdAt = timestamp - This is the timestamp of creation and it is required.
- updatedAt = timestamp - This is the timestamp of the most recent update. It is optional when inserting a row into the table.

