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

- <img src="/images/architecture-diagram.png" width="screen" height="screen">
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

## Data

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


## Reliability

**Duplication of a payment is prevented through:**

- the `unique constraint` of the primary key `"id"` in the tables `payments` and `workerOutbox`. The `primary key` also has the role of an `idempotency key / deduplication key`.  It ensures that no two payments can share the samwe `id`.

**Retries with exponential backoff:**
- Retries with exponential backoff can be impleneted like this:

- <img src="/images/retries.png" height="screen" width="screen">

- Depending on the `ApproximateReceiveCount` the `MessageVisibility` can be changed so the message is visible after an exponential time has passed.
- This approach can be used for both validating and processing of paymnets and the notification of partners.

**Circuit breaker when SAP is overloaded or unreachable:**
- The circuit breaker pattern can be implemented as in the example below:
- <img src="/images/circuit-breaker.png" height="screen" width="screen">

**Dead Letter Queue for messages can be implemented as in the example:**
- <img src="/images/dlq.png">

**Guarantee: once acknowledged, no data is lost and no duplicate payments reach SAP.**

- The partner requests are acknowledged ONLY after a succesfull push to the SQS.
- After a validation by SAP succeeds or fails a payment request is stored in the `Payments Core` database with its respective status.
- The idempotency key `"id"` ensures that no duplicate payment requests are stored in the database and later on distributed to the services.
- The AWS SQS are thread secure and they ensure that once a message is read by a consumer it is not visible for other consumers. So once a payment request is being processed by a worker resource it is not visible for other consumers.
- Everything mentioned above is logged through a logger service and that ensures traceability across all services in the architecture.

## Failure handling & runbooks

**Runbook: SAP down - Validator failing to validate incoming payment requests:**
> If SAP is down for a prolonged time the incoming payment requests will be eventually transfered from the POST-SQS queue to its corresponding DLQ after the maximum read count is exceeded or the maximum retention tiome has elapsed. In such cases the runbook below can be used after SAP is healthy again.

1. Consult with the operations department and SAP.
2. Read the messages from the DLQ (either on the AWS platform or the logging platform).
3. Depending on the decision of the operations department do one of the following steps:
- A: Create a PaymentFailed outbox event in the Payments Core database for each DLQ message and all the partners will be notified automatically about the failure and they have to resend the payment requests. The payment process is nullified and it has to be initiated again by the partners.
- B: Transfer all payment request messages from the DLQ back to the POST-SQS and the processing of the requests will proceed to replay automatically.
- C: If there is a crisis scenario taking place at SAP consult with the operations department if the payment requests are still going to be stored in our system (increasing costs for the company) or a temporary shutdown of our system has to take place untill further notification from SAP in order to be cost efficient.

**Runbook: SAP down - Worker failing to process already validated payment requests (PaymentCreated)**

> If SAP is down for a prolonged time the payment requests that have already been validated are eventually going to be transfered from the Worker-SQS to its corresponding DLQ. This will happen either when the maximum retention time for the messages has elapsed or the maximum read count for the messages is exceeded. In such cases the runbook below can be utilized:

1. Consult with the operations department and SAP.
2. Read the messages from the DLQ (either on the AWS platform or the logging platform).
3. Depending on the decision of the operations department do one of the following steps:

- A: Create a PaymentFailed outbox event in the Payments Core database for each DLQ message and all the partners will be notified automatically about the failure and they have to resend the payment requests. Delete the corresponding payment requests from the payments table and outbox table respectively. The payment process is nullified and it has to be initiated again by the partners.
- B: Transfer all PaymentCreated messages from the DLQ back to the Worker-SQS and the process will be replayed automatically as usual.
- C: If there is a crisis scenario taking place at SAP consult with the operations department if the payment requests are still going to be stored in our system (increasing costs for the company) or a temporary shutdown of our system has to take place untill further notification from SAP in order to be cost efficient.

**Runbook: Partner not responding: Webhook Service failing to deliver payment updates to partner**

> If a partners APIs for payment status updates are not responding the notification messages such as PaymentCreated, PaymentSettled and PaymentFailed will eventually be transfered form the Webhook-SQS to its corresponding DLQ after the maximum read count is exceeded or the maximum retention time for the messages has elapsed. In such cases the runbook instructions below can be followed.

1. Consult with the operations department and the affected partner/s.
2. Read the DLQ messages.
3. Depending on the consultation results do one of the following steps:
- A: Delete messages from the DLQ and inform partners/s about all affected payment updates manually (E-Mail, Fax etc.). Alternatively the payment statuses can be fetched using our GET endpoint and in this case the only necessary step would be informing the affected partner/s and deleting the messages from the DLQ.  
- B: If partner/s APIs are online again and want to receive updates automatically, move the messages from the DLQ back to the Webhook-SQS and the notifications will be resent automatically.
- C: If the affected APIs are undergoing long term complications place the partners into an ignore list so that resources won't be wasted and costs can be reduced. The affected partner/s can stilll access the payment status updates by using our GET endpoint.

> Note that the transfer of messages from a DLQ to the original SQS can either be done manually: DLQ → Messages → “Send or Move Messages”
> Or using a Replay Lambda to automatically read the DLQ and publish the messages back to the original SQS.

## Observability

**Logs with correlation ids and traces across services**

- All database rows that are related to payments, SQS messages and incoming POST-Requests  (all log items) have a `correlation id / idempotency key / deduplication key` that consists of the company name and order id.
- This makes it possible to trace and monitor every single payment request from the `Payment POST-Request` to the `Payment notification events / messages` including all related metrics about the payment across all services involved.

**The key metrics that are relevat to this project are the following:**
- **SAP Succes Rate:** This metric represents the current percentile of the succesfull SAP calls made by the validator lambdas and the worker lambdas combined over a period of time (e.g. 10 minutes). If it is ever to fall below a certain threshold % an alert is raised on CloudWatch and the dev / ops team is notified about the situtation. The consequence of this is the manipulation / activation of the circuit breaker mechanism to balance the outgoing traffic to SAP in order to prevent potential overloading.

- **Queue Depth (Messages):** This metric represents the current amount of messages in a queue (SQS) and if a certain threshold amount is surpassed an alert is raised and the dev / ops team is informed about it. The consequence of this could be raising the lambda concurrency of the queue to improve performance / reduce processing time.

- **DLQ Count:** This metric represents the count of messages in a DLQ. It indicates that either the webhook endpoints of a partner / partners are overloaded or down or that SAP is under heavy load or is down. An alert should be raised immediately after a DLQ receives a message. Even a single message indicates that something is not right and the dev and or ops teams have to undertake immediate action (look at the runbooks above).

- **SAP Health:** This metric represents the amount of succesful SAP calls (e.g. pings or mocked calls) made by the health check service over a period of time (e.g. 10 minutes). If it falls below a certain threshold it should raise an alert on CloudWatch and trigger a lambda function that automatically activates the circuit breaker mechanism in order to reduce outgoing traffic or potentially shut down the validation and worker services completely. The dev / ops teams should be informed but the circuit breaker mechanism is activated automatically.

- **Gateway Latency:** This metric represents the latency of the Gateway. Higher latencies (in ms) indicate heavy load. A useful consequence would be automatically adapting the load balancing of the gateway by raising an alert on CloudWatch and triggering a lambda to adapt the load balancing of the Gateway. The dev team should be also informed and it should closely monitor the situation.

**In the graphic below you can see an example for a dashboard. In reality AWS CloudWatch Dashboards or Grafana for AWS CloudWatch can be used to monitor the metrics in real time. The alarms can also be monitored on CloudWatch Alarms View.**

<img src="/images/observability-metrics-graph.png" height="screen" width="screen">

> 📌 Notice that those thresholds are just examples.

## Security

**OAuth 2.0 is utilized in order to assure secure communication with each partner**

**Webhooks with secrets are utilized in order to securely notify partners about payment updates**

**No direct endpoint exposure - All services are inside a secure AWS environment and the only seervice that is exposed to the outside is the state machine responsible for distributing the incoming HTTP request to the corresponding services**