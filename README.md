# En Garde Gear — Fencing Equipment Online Store

**Semester Project 2026–2027**  
**Team Members & Roles:**
- **Stan Oana Adriana** — *Catalog and UI Lead*  
  (A1 Catalog, A2 Search, A8 Orders, A9 Admin Panel, A11 Responsive Design, Seed Data, B1 Filtered Search)
- **Mitrea Vladut-Cristian** — *Backend Lead*  
  (A3 Cart, A4 Accounts, A5 Checkout, A6 Payment, A7 Stock Management, A10 Security, A12 Automated Tests, Docker Setup, B2 Recommendations)

---

## 1. Project Overview & Competitor Analysis
Specialized online store for fencing equipment (foil, épée, sabre gear, protective equipment, and electrical scoring components).

### Competitor Insights
- **Leon Paul**: Clear category tree by weapon; size guides. We will adopt a guided starter kit builder.
- **Absolute Fencing Gear**: Wide range, filters by weapon and level. We will show compatible accessories directly on product pages.
- **Blue Gauntlet**: Certification labels on protective gear (350N vs 800N FIE). We will add plain-language safety explanations.

---

## 2. Planned Technology Stack
- **Backend**: Python 3.12 + Django 5 (ORM, CSRF protection, Argon2 password hashing)
- **Frontend**: HTML5 Server-rendered Templates + Bootstrap 5.3
- **Database**: PostgreSQL 16 (fallback: SQLite3 for quick local development)
- **Payments**: Stripe Checkout (test mode) + Webhooks
- **DevOps**: Docker Compose, pytest

---

## 3. Getting Started

### Local Setup
```bash
uv venv --python 3.12 .venv
.venv\Scripts\activate
uv pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Docker Compose
```bash
docker compose up --build
```

---

## 4. Project Structure & Architecture
The application is structured into six business-logic apps inside `apps/`:
- `apps/catalog`: Categories, 33 products, variants, images, attributes, and starter-kit guide.
- `apps/accounts`: Custom `User` model, Argon2 hashing, saved addresses (`Address` model), register/login/logout.
- `apps/cart`: Database-backed `Cart` and `CartItem` models, guest-to-user session cart merging at login.
- `apps/orders`: 4-step checkout wizard, `DeliveryMethod`, `Order`, `OrderItem`, and 30-minute `StockReservation`.
- `apps/payments`: Stripe webhook listener with idempotency check (`stripe_event_id`).
- `apps/manage`: Staff administration portal (`/manage/`) protected by `@staff_required`.

## 5. Demo Accounts
- **Customer Account**: `fencer@engarde.com` / `fencer1234`
- **Staff Administrator Account**: `admin@engarde.com` / `admin1234`
