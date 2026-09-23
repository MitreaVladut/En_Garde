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
