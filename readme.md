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

> 📌 Notice that the workerOutbox and webhookOutbox are representative of the event schemas.
---
> 📌 The workerOutbox table does not include an eventType column because it can only contain PaymentCreated events.


**payments table:**
|id = string (uuid)|paymentDetails = JSONB object|status = string enum (QUEUED, FAILED, SETTLED)|createdAt = timestamp|updatedAt = timestamp|
|------------------|-----------------------------|----------------------------------------------|---------------------|---------------------|
|company12order34 |{"paymentDetails":{} } |QUEUED |	1758264781  |	1758264781             |
|...|...|...|...|...|
|...|...|...|...|...|


**Keys and constraints:**

- id = string (uuid) - This is the primary key with unique constraint. It is a combination of the company identifier and the order identifier. It is also the idempotency key and the correlation id for the logs. 
- paymentDetails = JSONB object - This is the object that holds the actual payment details. It is a required column. A paymentDetails column could look like this for example: 
```
{
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
}
```
- status = string enum - This is the status of the payment and it is a required column.
- createdAt = timestamp - This is the timestamp of creation and it is required.
- updatedAt = timestamp - This is the timestamp of the most recent update. It is optional when inserting a row into the table.

**workerOutbox table:**
| id = string (uuid) | mappingRules = JSONB object | status = string enum (PENDING, QUEUED, FAILED, SETTLED) | createdAt = timestamp | updatedAt = timestamp |
|--------------------------|-----------------------------|---------------------|-----------------------|-----------------------|
|company12order34|{"mappingRules": {}}|PENDING | 1758264781 | 1758264781|
|company23order34|{"mappingRules": {}}|QUEUED |1758264781|1758264781|
|company34order45|{"mappingRules": {}}|SETTLED|1758264781|1758264781|
|company23order45|{"mappingRules": {}}|FAILED |1758264781|1758264781|
**Keys and constraints:**

- id = string (uuid) - This is the primary key with unique constraint. It is a combination of the company identifier and the order identifier. It is also the idempotency key and the correlation id for the logs. 
- mappingRules = JSONB object - This object holds the mapping rules for the partner from SAP.
- status = string enum (PENDING, QUEUED, SETTLED, FAILED) - This is the current status of the payment it can either be pending to be queued, queued, settled or failed.
- createdAt = timestamp - This is the timestamp of creation and it is required.
- updatedAt = timestamp - This is the timestamp of the most recent update. It is optional when inserting a row into the table.

**webhookOutbox table:**
| id = string (uuid) | idempKey = string (uuid) | eventType = string enum | sapStatus = JSONB object | deliveryStatus = JSONB object| createdAt = timestamp | updatedAt = timestamp|
|--------------------|--------------------------|-------------------------|--------------------------|------------------------------|-----------------------|----------------------|
| uuid1233 | company12order23 | PaymentCreated | {"status": "PENDING", "description": "payment created"}|{"status": "PENDING", "description": "notification created"}|1758264781|1758264781
| uuid1233 | company12order23 | PaymentSettled | {"status": "SETTLED", "description": "SAP 4xx"}|{"status": "QUEUED", "description": "delivery in progress"}|1758264781|1758264781
| uuid1233 | company12order45 | PaymentFailed | {"status": "FAILED", "description": "SAP 5xx"}|{"status": "FAILED", "description": "partner 5xx"}|1758264781|1758264781
| uuid1233 | company12order45 | PaymentFailed | {"status": "FAILED", "description": "SAP 5xx"}|{"status": "DELIVERED", "description": "partner 2xx"}|1758264781|1758264781


**Keys and constraints:**

- id = string (uuid) - This is the unique id of the row and it is the primary key.
- idempKey = string (uuid) - This is the correlation id for the logs, the idempotency key and the order identifier for the partner notifications.
- eventType = string enum {PaymentCreated, PaymentSettled, PaymentFailed} it specifies the type of the event which is also the notification for the partner.
- deliveryStatus = JSONB object - This is the delivery status of the netification. The "status" attribute can be: PENDING, QUEUED, FAILED or DELIVERED. The "description" attribute is the according description.
- sapStatus = JSONB object - This is the current status of the payment and its description. The "status" attribute can be : PENDING, QUEUED, SETTLED or FAILED and the "description" attribute is the description.
- createdAt = timestamp - This is the timestamp of creation and it is required.
- updatedAt = timestamp - This is the timestamp of the most recent update. It is optional when inserting a row into the table.




