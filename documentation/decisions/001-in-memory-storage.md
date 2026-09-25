# 001: Use in-memory case storage for the initial backend

Date: 2026-09-23
Owner: Tommaso Limonta
Status: Implemented for this branch; pending owner review

## Context

WhatNow needs a working case/task contract before AI interpretation and verified
workflows can be integrated. This university MVP prioritizes understandable
application logic, repeatable tests, and a small setup burden. The assigned
scope explicitly calls for in-memory storage.

## Alternatives

- A Python dictionary: no external service or schema migration; data is temporary.
- A JSON file: survives restarts, but needs file locking, atomic writes, and
  recovery behavior to avoid corruption.
- SQLite: durable local storage with transactions, but requires database schema
  and persistence decisions before the shared model has settled.
- PostgreSQL or MongoDB: shared persistence, but adds configuration and operational
  work outside the assigned scope.

## Decision

Use an `InMemoryCaseStore` containing a dictionary keyed by case ID. Each FastAPI
application instance owns one store and one `CaseService`. No external storage
dependency is required.

The API handles HTTP, the service handles case operations, and the store handles
copies of state. Deep copies on both reads and writes prevent a caller from
silently changing stored nested facts or tasks. A reentrant lock in the service
covers the entire task read-modify-write operation, avoiding lost updates between
request threads. All application operations must use that single service; the
store itself is not a standalone transactional or thread-safe database.

No repository interface, ORM, or generic persistence framework is introduced.
Those abstractions can be justified when a second storage implementation exists.

## Trade-offs

Setup is simple, tests get fresh state, and the core behavior is easy to explain.
However, a restart or development reload destroys every case. Separate workers
or processes cannot share cases. Memory use grows with case count; there is no
eviction, audit history, backup, or durable recovery. Deep copying and serializing
service operations are acceptable for this small local MVP, not a scaling design.

Run with one Uvicorn worker. Tests seed only synthetic tasks; the core does not
invent a workflow or classify messages to make a demonstration appear complete.

## When to replace it

Replace in-memory storage when cases must survive restarts, multiple processes
must share state, or the project needs durable history or larger datasets.
Consider SQLite first for a single-instance prototype and a shared database when
multiple application instances become necessary. Preserve the API contract and
service tests, and add storage tests for transactions, concurrency, and restart
durability. Decide schema migrations and data-retention requirements at that time.
