# AKA (Antier Knowledge Assistant)

# CLAUDE CODE MASTER IMPLEMENTATION DIRECTIVE

# VERSION 1.0

---

# IMPORTANT

You are NOT the architect of this system.

You are the implementation engineer.

Do not redesign architecture.
Do not introduce alternative technologies.
Do not simplify requirements.
Do not add features not explicitly requested.

Your responsibility is to implement exactly what is described in this specification.

If a decision is already documented here, follow it exactly.

---

# PROJECT OBJECTIVE

Build a Proof of Concept (POC) internal knowledge assistant that enables:

1. Document Upload
2. Document Search
3. Retrieval Augmented Generation (RAG)
4. Department Based RBAC
5. Information Request Workflow
6. Temporary Access Grants
7. Source Grounded AI Answers

The primary objective is:

Security > Correctness > Maintainability > Performance > UI

---

# MANDATORY TECHNOLOGY STACK

Backend

* Python 3.11
* Django 5+
* Django REST Framework

Authentication

* djangorestframework-simplejwt

Vector Database

* Qdrant

Embeddings

* sentence-transformers/all-mpnet-base-v2

RAG Framework

* LangChain

LLM

* Gemini 1.5 Flash

Database

* SQLite

Frontend

* React
* Vite

State Management

* React Context

Document Parsing

* PyMuPDF
* python-docx
* openpyxl

Containerization

* Docker only for Qdrant

---

# FORBIDDEN TECHNOLOGIES

Do NOT introduce:

* PostgreSQL
* Redis
* Celery
* RabbitMQ
* Kafka
* Pinecone
* Weaviate
* ChromaDB
* LangGraph
* Haystack
* Elasticsearch
* Redux
* Zustand
* GraphQL
* Microservices

This is a monolithic Django application.

---

# SYSTEM ARCHITECTURE

Frontend

↓

Django API

↓

Authentication

↓

RBAC

↓

Qdrant Filter

↓

Retrieval

↓

Gemini

↓

Response

Important:

Unauthorized chunks must NEVER reach Gemini.

Retrieval must already be filtered.

Forbidden:

Retrieve

↓

Filter

↓

Send to Gemini

Allowed:

Filter

↓

Retrieve

↓

Send to Gemini

---

# PROJECT STRUCTURE

Use ONE Django app.

Do not create multiple Django apps.

Structure:

backend/

config/

aka/

models/
serializers/
services/
api/
permissions/
authentication/
ingestion/
qdrant/
prompts/

admin.py
urls.py

Business logic belongs only in services.

Views must be thin.

---

# CODING STANDARDS

Mandatory:

* Type hints
* Service layer pattern
* Fat services
* Thin views
* Serializer validation
* No business logic in serializers
* No business logic in views
* Explicit error handling
* Structured logging
* Reusable utility functions

Avoid:

* Massive views
* Massive serializers
* Business logic inside models
* Hidden side effects

---

# DATABASE RULES

Primary keys:

UUID everywhere.

Every model must include:

created_at
updated_at

Use:

BaseModel

for shared fields.

---


# USER MODEL

Extend AbstractUser.

Fields:

id
username
email
org_role
created_at
updated_at

org_role:

member
super_admin

Do not add additional profile models.

---

# DEPARTMENT MODEL

Fields:

id
name
slug
type

Important:

department.slug == qdrant namespace

This mapping is mandatory.

---

# DEPARTMENT MEMBERSHIP MODEL

Purpose:

Department level RBAC.

Fields:

id
user
department
role
sensitivity_ceiling
granted_via

Role values:

lead
contributor
viewer

Sensitivity values:

open
internal
restricted
confidential

Unique:

(user, department)

---

# SENSITIVITY HIERARCHY

Hierarchy:

open

↓

internal

↓

restricted

↓

confidential

Rules:

viewer

open

contributor

open
internal

lead

open
internal
restricted

confidential

Only through explicit DocumentAccess

Never through role.

---

# DOCUMENT MODEL


Fields:

id
name
department
uploader
sensitivity
version
status
uploaded_at
file_size
mime_type
chunk_count

Status:

active
superseded
deleted

Version Rule:

same filename

AND

same department

means

new version

Old version:

status=superseded

New version:

status=active

---

# DOCUMENT ACCESS MODEL

Purpose:

Temporary permission grants.

Fields:

id
user
document
granted_by
expires_at
is_active

Rules:

DocumentAccess overrides role restrictions.

DocumentAccess may allow confidential documents.

Expired access automatically becomes invalid.

---

# INFORMATION REQUEST MODEL

Fields:

id
requester
approver
department
document
request_text
reason
status
approver_note
created_at
decided_at
access_expires_at

Statuses:

pending
approved
rejected
escalated

No other statuses allowed.

---

# NOTIFICATION MODEL

Fields:

id
recipient
title
message
notification_type
is_read

Types:

request_received
approved
rejected
access_granted

Database only.

No email.

No Slack.

---

# AUTHENTICATION

Use:

SimpleJWT

Store tokens in:

HttpOnly cookies

Cookie names:

access
refresh

Do NOT use:

localStorage

Do NOT use:

sessionStorage

---

# CUSTOM AUTHENTICATION

Create:

CookieJWTAuthentication

Responsibilities:

Read cookie

Validate token

Return user

Attach claims

No Authorization header dependency.

---

# JWT STRUCTURE

JWT MUST contain:

{
"user_id": "...",

"org_role": "member",

"departments": [
{
"dept_id": "ai-team",
"role": "lead",
"sensitivity_ceiling": "restricted",
"granted_via": "direct"
}
]
}

JWT is primary RBAC source.

Avoid membership queries on every request.

---

# RBAC IMPLEMENTATION

Create:

RBACService

Responsibilities:

1. Read JWT claims
2. Resolve namespaces
3. Resolve sensitivity levels
4. Resolve DocumentAccess overrides
5. Build Qdrant filter

Output:

{
"namespaces": [],
"allowed_sensitivity": [],
"extra_doc_ids": []
}

Attach to request.

---

# QDRANT DESIGN

Collection:

aka_knowledge

Only ONE collection.

Never create:

sales_collection

finance_collection

engineering_collection

etc.

---

# CHUNK METADATA

Every chunk must contain:

{
"namespace": "...",
"doc_id": "...",
"doc_name": "...",
"chunk_id": "...",
"version": 1,
"sensitivity": "...",
"uploader": "...",
"timestamp": "..."
}

No missing metadata.

---

# DOCUMENT INGESTION FLOW

Upload

↓

Validation

↓

Parse

↓

Chunk

↓

Embed

↓

Metadata

↓

Qdrant

↓

SQL Metadata

---

# FILE TYPES

Supported:

PDF
DOCX
XLSX
TXT

Maximum:

50 MB

Reject unsupported types.

---

# PARSERS

PDF

PyMuPDF

DOCX

python-docx

XLSX

openpyxl

TXT

native open()

---

# CHUNKING

Use:

RecursiveCharacterTextSplitter

Configuration:

Chunk Size:

400 tokens

Overlap:

50 tokens

Token aware.

---

# EMBEDDINGS

Mandatory model:

sentence-transformers/all-mpnet-base-v2

Dimension:

768

Same model used for:

ingestion

retrieval

No exceptions.

---

# QUERY FLOW

Question

↓

Rewrite

↓

Embed

↓

Qdrant Search

↓

Top 10

↓

Top 5

↓

Prompt Builder

↓

Gemini

↓

Response

---

# QUERY REWRITE PROMPT

Rewrite the question into a self-contained retrieval query.

Keep it concise.

Return rewritten query only.

---

# RETRIEVAL SECURITY

Apply Qdrant filters BEFORE retrieval.

Algorithm:

(
namespace IN namespaces
AND
sensitivity IN allowed_levels
)

OR

(
doc_id IN extra_doc_ids
)

Only retrieve matching chunks.

Unauthorized chunks must never be retrieved.

---

# ANSWER GENERATION

Prompt:

You are an internal knowledge assistant.

Answer only using supplied context.

Never use external knowledge.

If context is insufficient:

"I do not have enough information to answer that question."

Always cite sources.

Format:

[Source: document_name]

---

# FILE MANAGEMENT

Upload:

lead
contributor

Delete:

lead

Viewer:

read-only

---

# VERSIONING RULES

If:

same filename

AND

same department

Uploaded again

Then:

version + 1

Mark previous version:

superseded

Delete old chunks from Qdrant.

Store only latest active version.

---

# INFORMATION REQUEST WORKFLOW

User

↓

Request Access

↓

InformationRequest

↓

Pending

↓

Lead Review

↓

Approve OR Reject

If Approved

↓

Create DocumentAccess

↓

30 Day Expiry

If Rejected

↓

Store Reason

↓

Notify User

---

# API DESIGN RULES

Use REST APIs.

No GraphQL.

Every endpoint must have:

Serializer

Service

View

Permission

Error Handling

Do not put business logic directly in views.

---

# REQUIRED ENDPOINTS

Authentication

POST /api/login/
POST /api/logout/
POST /api/refresh/

Departments

GET /api/departments/

Documents

GET /api/documents/
POST /api/documents/upload/
DELETE /api/documents/{id}/

Chat

POST /api/chat/query/

Requests

POST /api/requests/
GET /api/requests/pending/
POST /api/requests/{id}/approve/
POST /api/requests/{id}/reject/

Notifications

GET /api/notifications/

Do not invent additional endpoints.

---

# FRONTEND RULES

Pages:

Login

Dashboard

Chat

Documents

Requests

Nothing else.

---

# CHAT PAGE

Display:

Answer

Sources

Sensitivity

Request Access Button

Department Selector

---

# DOCUMENT PAGE

Display:

File Name
Department
Sensitivity
Version
Uploader

Actions:

Upload
Delete

Delete visible only for leads.

---

# REQUEST PAGE

Users:

Create Request

Leads:

Approve
Reject

Display request history.

---

# DO NOT BUILD

SSO

Admin Portal

Analytics

Audit Dashboard

Slack Integration

Email Integration

Conversation Memory

Fine Tuning

Mobile Application

Production Infrastructure

CI/CD

Background Jobs

Multi Tenant Support

---

# SEED DATA

Users:

Alice
Bob
Charlie

Departments:

AI Team
Sales
AI Showcases

Memberships:

Alice → AI Team → Lead

Bob → Sales → Viewer

Charlie → Sales → Viewer

Charlie → AI Showcases → Viewer

Use fixtures or management command.

---

# ACCEPTANCE CRITERIA

1. Upload document.

2. Document becomes searchable.

3. RBAC enforced before retrieval.

4. Unauthorized chunks never retrieved.

5. Information request workflow works end-to-end.

6. Temporary access grants work.

7. Versioning works.

8. Sources displayed.

9. Query latency below 5 seconds.

10. Entire implementation follows this specification exactly.

---

# FINAL INSTRUCTION

If any implementation choice is unclear:

Prefer consistency with this specification.

Do not introduce new architecture.

Do not introduce new technologies.

Implement exactly as documented.
