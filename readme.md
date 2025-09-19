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
---

> 📌 You can copy the excalidraw code from the file below and paste it on [Excalidraw](https://excalidraw.com/) for a better resolution.
> 
> 📌 [Click here to open the excalidraw file.](./Excalidraw-12-09-2025-Final-Version.excalidraw)
---

-<img src="/images/architecture-diagram.png" width="screen" height="screen">
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
|id = `string (uuid)`|paymentDetails = `JSONB objet`|mappingRules = `JSONB object`|status = `string enum (QUEUED, FAILED, SETTLED)`|createdAt = `timestamp`|updatedAt = `timestamp`|
|------------------|-----------------------------|----------------------------------------------|---------------------|---------------------|--------|
|company12order34 |{"paymentDetails":{} } |{"mappingRules": {}}|QUEUED |	1758264781  |	1758264781             |
|...|...|...|...|...|...|
|...|...|...|...|...|...|


**Keys and constraints:**

- id = `string (uuid)` - This is the primary key with unique constraint. It is a combination of the company identifier and the order identifier. It is also the idempotency key and the correlation id for the logs. 
- paymentDetails = `JSONB objet` - This is the object that holds the actual payment details. It is a required column. A paymentDetails column could look like this for example: 
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
- mappingRules = `JSONB object` - This is the object holding the partner mapping rules from SAP.
- status = `string enum `- This is the status of the payment and it is a required column.
- createdAt = `timestamp` - This is the `timestamp` of creation and it is required.
- updatedAt = `timestamp` - This is the `timestamp` of the most recent update. It is optional when inserting a row into the table.

**workerOutbox table:**
| id = `string (uuid)` | mappingRules = `JSONB objet` | status = `string enum (PENDING, QUEUED, FAILED, SETTLED)` | createdAt = `timestamp` | updatedAt = `timestamp` |
|--------------------------|-----------------------------|---------------------|-----------------------|-----------------------|
|company12order34|{"mappingRules": {}}|PENDING | 1758264781 | 1758264781|
|company23order34|{"mappingRules": {}}|QUEUED |1758264781|1758264781|
|company34order45|{"mappingRules": {}}|SETTLED|1758264781|1758264781|
|company23order45|{"mappingRules": {}}|FAILED |1758264781|1758264781|
**Keys and constraints:**

- id = `string (uuid)` - This is the primary key with unique constraint. It is a combination of the company identifier and the order identifier. It is also the idempotency key and the correlation id for the logs. 
- mappingRules = `JSONB objet` - This object holds the mapping rules for the partner from SAP.
- status = `string enum `(PENDING, QUEUED, SETTLED, FAILED) - This is the current status of the payment it can either be pending to be queued, queued, settled or failed.
- createdAt = `timestamp` - This is the `timestamp` of creation and it is required.
- updatedAt = `timestamp` - This is the `timestamp` of the most recent update. It is optional when inserting a row into the table.

**webhookOutbox table:**
| id = `string (uuid)` | idempKey = `string (uuid)` | eventType = `string enum `| sapStatus = `JSONB objet` | deliveryStatus = `JSONB objet`| createdAt = `timestamp` | updatedAt = `timestamp`|
|--------------------|--------------------------|-------------------------|--------------------------|------------------------------|-----------------------|----------------------|
| uuid1233 | company12order23 | PaymentCreated | {"status": "PENDING", "description": "payment created"}|{"status": "PENDING", "description": "notification created"}|1758264781|1758264781
| uuid1268 | company12order23 | PaymentSettled | {"status": "SETTLED", "description": "SAP 4xx"}|{"status": "QUEUED", "description": "delivery in progress"}|1758264781|1758264781
| uuid1226 | company12order45 | PaymentFailed | {"status": "FAILED", "description": "SAP 5xx"}|{"status": "FAILED", "description": "partner 5xx"}|1758264781|1758264781
| uuid1254 | company12order46 | PaymentFailed | {"status": "FAILED", "description": "SAP 5xx"}|{"status": "DELIVERED", "description": "partner 2xx"}|1758264781|1758264781


**Keys and constraints:**

- id = `string (uuid)` - This is the unique id of the row and it is the primary key.
- idempKey = `string (uuid)` - This is the correlation id for the logs, the idempotency key and the order identifier for the partner notifications. It is the same id from the payments and workerOutbox table.
- eventType = `string enum {PaymentCreated, PaymentSettled, PaymentFailed}` it specifies the type of the event which is also the notification for the partner.
- deliveryStatus = `JSONB objet` - This is the delivery status of the netification. The "status" attribute can be: PENDING, QUEUED, FAILED or DELIVERED. The "description" attribute is the according description.
- sapStatus = `JSONB objet` - This is the current status of the payment and its description. The "status" attribute can be : PENDING, QUEUED, SETTLED or FAILED and the "description" attribute is the description.
- createdAt = `timestamp` - This is the `timestamp` of creation and it is required.
- updatedAt = `timestamp` - This is the `timestamp` of the most recent update. It is optional when inserting a row into the table.

## Partner Config database:

**The Partner Config database has only one table: partnerConfig**

**partnerConfig table**

| partnerId `string (uuid)`         | partnerName `string`     | clientIdInternal `string`      | clientSecretInternal `string`   | clientIdSAP `string`           | clientSecretSAP `string`        | webhookSecret `JSONB object`                         | webhookURLs   `JSONB object`                                                                      |
|--------------------------------------|------------------|----------------------|-----------------------|-----------------------|-----------------------|-----------------------------------------------|-----------------------------------------------------------------------------------------------|
| 7a1b2c3d-4e5f-6789-abcd-1234567890ab | Partner GmbH     | int-client-001       | secret-internal-001   | sap-client-001        | secret-sap-001         | {"hashType": "SHA256", "secret": "abc123"}    | {"PaymentCreated": "https://partner.de/created", "PaymentSettled": "https://partner.de/settled", "PaymentFailed": "https://partner.de/failed"} |
| 8b2c3d4e-5f6a-7890-bcde-2345678901bc | Acme AG          | int-client-002       | secret-internal-002   | sap-client-002        | secret-sap-002         | {"hashType": "SHA512", "secret": "def456"}    | {"PaymentCreated": "https://acme.com/created", "PaymentSettled": "https://acme.com/settled", "PaymentFailed": "https://acme.com/failed"}      |
| 9c3d4e5f-6a7b-8901-cdef-3456789012cd | Beta Solutions   | int-client-003       | secret-internal-003   | sap-client-003        | secret-sap-003         | {"hashType": "SHA256", "secret": "ghi789"}    | {"PaymentCreated": "https://beta.sol/created", "PaymentSettled": "https://beta.sol/settled", "PaymentFailed": "https://beta.sol/failed"}       |


**Keys and constraints:**

- partnerId = `string (uuid)` - This is the unique partner identifier and it is the primary key of the rows.
- partnerName = `string` - This is the name of the partner company.
- clientIdInternal = `string` - This is the OAuth2 client id of the partner for generating access tokens for our middleware.
- clientSecretInternal = `string` - This is the OAuth2 client secret of the partner for generating access token for our middleware.
- clientIdSAP = `string` - This is the OAuth2 client id of the partner for generating access tokens for SAP.
- clientSecretSAP = `string` - This is the OAuth2 client secret of the partner for generating access token for SAP.
- webhookSecret = `JSON object` - This is the client secret for signing the Webhooks and it has following structure: `{"hashType": " ", "secret": " "}`.
- webhookURLs = `JSON object` - This object holds the Webhook URLs of the partner to receive notifications about payments. It has the following structure: 
`{"PaymentCreated": "URL", "PaymentSettled": "URL", "PaymentFailed": "URL"}`





