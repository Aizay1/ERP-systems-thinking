# Kadisco Procurement — Material Request Management

A lightweight, ERP-style prototype of a **Procurement Department** web application for Kadisco Manufacturing.
It is built with **Python only** (Flask + the standard-library `sqlite3` module), organised into small,
single-responsibility modules, and it demonstrates a **complete end-to-end procurement workflow** driven by
simulated inputs from other departments (Production, Management, Warehouse, Finance).

---

## Table of contents

1. [What it does](#what-it-does)
2. [The workflow](#the-workflow)
3. [Tech stack](#tech-stack)
4. [Prerequisites](#prerequisites)
5. [How to run it](#how-to-run-it)
6. [Project structure](#project-structure)
7. [Database schema](#database-schema)
8. [HTTP routes](#http-routes)
9. [Design conventions](#design-conventions)
10. [Resetting the database](#resetting-the-database)
11. [Notes & limitations](#notes--limitations)

---

## What it does

The app has two main screens:

| Screen | Purpose |
| --- | --- |
| **Dashboard** (`/`) | KPI cards + a table of every material request, with each department's status shown as a read-only badge. Create new requests here. |
| **Request detail** (`/requests/<id>`) | A vertical **workflow timeline** that tracks one request through all 7 stages, plus an **Action Required** panel showing the next available action. |

Key behaviours:

- A **submission form** (in a modal on the dashboard) creates a new material request. It simulates input from the
  **Production** department. Every status starts as **`Pending`** and the request begins at the **`Requested`** stage.
- Each request can be walked through the full lifecycle from the detail page.
- The **Management Approval**, **Warehouse**, and **Finance Payment** columns stay visible but are **read-only** —
  they are updated only by the *simulated external triggers*, modelling future system-integration points.
- **Procurement** actions are shown as solid blue buttons; **external-system triggers** are shown as dashed gray
  `[Simulate …]` buttons, so it is obvious which are real user actions and which are mocked integrations.

---

## The workflow

A request moves through these 7 stages (`app/workflow.py`). The stored `stage` column always holds the stage
currently being worked on.

| # | Stage | Who acts | Action / trigger | Result |
| --- | --- | --- | --- | --- |
| 1 | **Requested** | Procurement | `Start Quoting` *(solid)* | → moves to Quoting |
| 2 | **Quoting** | Procurement | enter **Supplier Name** + **Price**, click `Send for Approval` *(solid)* | → moves to Pending Approval |
| 3 | **Pending Approval** | Management (external) | `[Simulate Management Approval]` *(dashed)* | Management Approval → **`Approved`**; → moves to PO Issued |
| 4 | **PO Issued** | Procurement | `Issue Purchase Order` *(solid)* | → moves to In Transit |
| 5 | **In Transit** | Warehouse (external) | `[Simulate Warehouse Receipt]` *(dashed)* | Warehouse → **`Goods Received`** (quantity verified); → moves to Invoicing |
| 6 | **Invoicing** | Finance (external) | `[Simulate Finance Payment]` *(dashed)* | Finance Payment → **`Paid`**; → moves to Paid |
| 7 | **Paid** | — | — | Workflow complete, loop closed |

The timeline marks past stages with a green check, highlights the current stage, and greys out future stages.

---

## Tech stack

| Layer | Choice | Why |
| --- | --- | --- |
| Language | **Python 3.11+** | "Python only" requirement |
| Web framework | **Flask** | Minimal, no boilerplate, easy to read |
| Database | **`sqlite3`** (standard library) | Zero setup, single-file database |
| Front-end | Plain **Jinja2 templates + one CSS file** | No build step, no JS framework needed |
| Packaging | **uv** | Fast dependency management (plain `pip`/`venv` also works) |

No ORM, no JavaScript framework, no Node.js — the logic is plain Python and SQL.

---

## Prerequisites

- **Python 3.11 or newer** (developed on 3.14)
- **uv** (recommended) — install from <https://docs.astral.sh/uv/>:

  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

  Or use plain `pip` if you prefer (see the alternative below).

---

## How to run it

### Option A — with `uv` (recommended)

From the project root (the folder that contains `main.py` and `pyproject.toml`):

```bash
# 1. Create the virtual environment and install dependencies
uv sync

# 2. Start the development server
uv run python main.py
```

### Option B — with plain `venv` + `pip`

```bash
# 1. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. Install the single dependency
pip install flask

# 3. Start the server
python main.py
```

### Open the app

Once the server is running you will see:

```
 * Running on http://127.0.0.1:5000
```

Open **<http://127.0.0.1:5000>** in your browser.

The SQLite database file `kadisco.db` and its `Kadisco_Operations` table are created **automatically** on first
start — there is no separate migration or seed step.

> The dev server runs with `debug=True` (auto-reload on file changes). It is intended for local/prototype use only.

> **Moved or renamed the project folder?** The application code is path-independent, but the `.venv` folder stores
> an absolute path to itself. Just recreate it after moving/renaming:
>
> ```bash
> rm -rf .venv
> uv sync
> uv run python main.py
> ```
>
> Your data in `kadisco.db` is untouched, because it lives in the project root, not inside `.venv`.

---

## Project structure

```
<project-root>/
├── pyproject.toml            # Project metadata + dependency list (Flask)
├── main.py                   # Entry point: builds the app and runs the server
├── kadisco.db                # SQLite database (auto-created on first run)
└── app/
    ├── __init__.py           # Application factory + Jinja "status_class" filter
    ├── database.py           # SQLite connection handling + table schema + migrations
    ├── workflow.py           # Workflow definition: ordered stages + descriptions
    ├── repository.py         # Data-access layer: all CRUD + stage transitions
    ├── routes.py             # HTTP endpoints (Flask Blueprint)
    ├── templates/
    │   ├── base.html         # Shared ERP shell (sidebar + topbar + flash messages)
    │   ├── dashboard.html    # KPI cards, requests table, "New request" modal
    │   └── detail.html       # Workflow timeline + request facts + action panel
    └── static/
        └── style.css         # All styling (ERP look, timeline, badges, buttons)
```

**Separation of concerns**

- `database.py` knows *how* to talk to SQLite; `workflow.py` knows the *rules* of the process.
- `repository.py` is the only module that writes SQL — routes never touch the database directly.
- `routes.py` handles HTTP concerns (validation, flash messages, redirects) and calls the repository.
- Templates only render data; they contain no business logic.

---

## Database schema

Table: **`Kadisco_Operations`** (defined in `app/database.py`)

| Column | Type | Notes |
| --- | --- | --- |
| `request_id` | INTEGER PK, autoincrement | The Request ID |
| `material_name` | TEXT, not null | Material Name |
| `quantity` | INTEGER, not null | Quantity |
| `supplier_name` | TEXT | Supplier Name (filled in at the Quoting stage) |
| `price` | REAL | Price (filled in at the Quoting stage) |
| `stage` | TEXT, default `'Requested'` | Current workflow stage (drives the timeline) |
| `procurement_status` | TEXT, default `'Pending'` | Procurement Status |
| `management_approval_status` | TEXT, default `'Pending'` | Management Approval Status |
| `warehouse_status` | TEXT, default `'Pending'` | Warehouse Status |
| `finance_payment_status` | TEXT, default `'Pending'` | Finance Payment Status |
| `created_at` | TEXT, default `datetime('now')` | Creation timestamp |

Column names use `snake_case` for SQL friendliness while the UI displays the human-readable labels above.
If the table already exists from an earlier version, the missing `price` and `stage` columns are added
automatically by the lightweight migration in `init_db()`.

---

## HTTP routes

All routes live in `app/routes.py`.

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/` | Dashboard: KPI stats + requests table |
| `GET` | `/requests/<id>` | Request detail page with the workflow timeline |
| `POST` | `/requests` | Create a request (simulated Production input) |
| `POST` | `/requests/<id>/start-quoting` | Stage 1→2: begin sourcing |
| `POST` | `/requests/<id>/send-for-approval` | Stage 2→3: capture supplier + price |
| `POST` | `/requests/<id>/simulate-management-approval` | Stage 3: **mock** management approval |
| `POST` | `/requests/<id>/issue-po` | Stage 4: issue the purchase order |
| `POST` | `/requests/<id>/simulate-warehouse-receipt` | Stage 5: **mock** warehouse receipt |
| `POST` | `/requests/<id>/simulate-finance-payment` | Stage 6: **mock** finance payment |
| `POST` | `/requests/<id>/delete` | Delete a request |

Every workflow action redirects back to the request's detail page and shows a flash message.

---

## Design conventions

- **Solid blue buttons** → actions performed by the Procurement user (real user interactions).
- **Dashed gray `[Simulate …]` buttons** → triggers that represent *other systems* (Management, Warehouse,
  Finance) and are mocked for the prototype. A legend at the bottom of the action panel explains the difference.
- **Read-only badges** → the Management / Warehouse / Finance status columns are displayed but never edited
  directly; they change only when their simulated trigger fires.

---

## Resetting the database

To wipe all data and start from an empty table, stop the server and delete the database file:

```bash
rm kadisco.db
```

It will be recreated (empty) the next time you run `uv run python main.py`.

---

## Notes & limitations

- This is a **prototype** for demonstrating a process flow, not a production system.
- There is **no authentication/authorisation** — anyone who opens the app acts as the Procurement user, and the
  "external" department actions are deliberately mockable via buttons.
- The Flask development server (`debug=True`) must **not** be used in production; use a WSGI server (e.g.
  Gunicorn/Waitress) instead.
- The `[Simulate …]` endpoints represent the integration points where a real deployment would instead call out to
  the Management, Warehouse, and Finance systems (or receive webhooks from them).
