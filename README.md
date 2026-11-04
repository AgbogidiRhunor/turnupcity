# 🎉 TurnUpCity

A full-stack event ticketing platform built with Django. Organizers create events and sell tickets, attendees buy them with Paystack and receive QR-coded tickets, and staff check people in at the door with a camera scanner.

Built with Django, PostgreSQL and plain HTML/CSS/JavaScript (no frontend frameworks).

---

## ✨ Features

### Attendees
- Browse and search upcoming events by keyword, category and city
- Multi-tier ticket purchasing with live order summary
- Coupon codes (percentage or fixed amount)
- Secure online payment through **Paystack**
- QR-coded digital tickets in a wallet-style view, downloadable as PNG
- Order history and refund requests (before the event's refund deadline)
- Direct messaging with organizers

### Organizers
- Organizer profile with public page (logo, bio, social links)
- Event lifecycle: **Draft → Published → Cancelled / Completed**
- Multiple ticket types per event with price, quantity, per-order limit and sales windows
- Discount coupons with usage limits and validity dates
- Dashboard with revenue, tickets sold and staff overview
- Per-event analytics, attendee CSV export and email broadcast to all paid attendees
- Refund approval workflow with audit trail
- **Withdrawals:** save a verified Nigerian bank account and withdraw earnings through the Paystack Transfer API
- Approve or reject staff who request to work for them

### Staff / Check-in Agents
- Request to work for an organizer
- Camera-based QR scanner (jsQR) with instant success / already-used / invalid feedback
- Manual lookup by ticket UUID, email or name
- Duplicate-scan prevention and a full scan audit log (who, when, which gate, IP)

### Platform Admin
- Verify or reject organizers from the Django admin
- Manage users, events, orders, tickets and refunds

---

## 🧰 Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 4.2 |
| Database | PostgreSQL |
| Payments | Paystack (Transactions, Transfers, Webhooks) |
| QR codes | `qrcode` (generation), `jsQR` (scanning) |
| Static files | WhiteNoise |
| Frontend | HTML, CSS (custom design system), vanilla JavaScript |
| Config | `python-decouple` |

---

## 👥 User Roles

| Role | What they can do |
|---|---|
| **Guest / Attendee** | Browse events, buy tickets, request refunds, message organizers |
| **Organizer** | Create and manage events, ticket types, coupons, refunds, staff, analytics and withdrawals |
| **Staff** | Scan and check in tickets for organizers who approved them |
| **Admin** | Verify organizers and manage the whole platform |

---

## 📁 Project Structure

```
turnupcity/
├── core/                 # Project settings, root URLs, WSGI
├── accounts/             # Custom user model (email login), profile, my tickets
├── organizers/           # Organizer profiles, staff requests, bank account, withdrawals
├── events/               # Events, categories, coupons
├── tickets/              # Ticket types, tickets, QR generation, scan logs
├── orders/               # Checkout, orders, Paystack integration
├── checkin/              # QR scanner and manual lookup
├── refunds/              # Refund requests and audit log
├── messaging/            # Organizer ↔ attendee threads
├── analytics/            # Stats, CSV export, email broadcast
├── templates/            # HTML templates
├── static/               # CSS and JavaScript
├── manage.py
├── requirements.txt
└── .env.example
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- PostgreSQL
- A [Paystack](https://paystack.com) account (test keys are fine for development)

### 1. Clone and create a virtual environment

```bash
git clone https://github.com/<your-username>/turnupcity.git
cd turnupcity

python -m venv .venv

# Windows (PowerShell)
.venv\Scripts\Activate.ps1
# macOS / Linux
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Create the database

```sql
CREATE DATABASE turnupcity;
```

### 4. Configure environment variables

```bash
cp .env.example .env      # Windows: copy .env.example .env
```

Then edit `.env`:

```env
SECRET_KEY=change-me-to-a-long-random-string
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# PostgreSQL
DB_NAME=turnupcity
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

# Email (console backend prints emails to the terminal in development)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your@email.com
EMAIL_HOST_PASSWORD=your_app_password
EMAIL_USE_TLS=True

# Paystack  (Dashboard → Settings → API Keys & Webhooks)
PAYSTACK_SECRET_KEY=sk_test_xxxxxxxxxxxxxxxx
PAYSTACK_PUBLIC_KEY=pk_test_xxxxxxxxxxxxxxxx
```

### 5. Run migrations and create an admin

```bash
python manage.py migrate
python manage.py createsuperuser
```

### 6. Add a few categories

Open `http://localhost:8000/admin/`, go to **Events → Categories** and add some (e.g. Music, Sports, Arts, Tech) so events can be filtered.

### 7. Start the server

```bash
python manage.py runserver
```

Visit `http://localhost:8000`.

---

## 💳 Paystack Setup

### Callback and webhook URLs

Paystack redirects the buyer to the callback URL after payment and sends server-to-server events to the webhook URL.

| Setting | Path |
|---|---|
| Callback URL | `/orders/paystack/callback/` |
| Webhook URL | `/orders/paystack/webhook/` |

### Testing locally with ngrok

Paystack can't reach `localhost`, so use a tunnel for the webhook:

```bash
ngrok http 8000
```

Then in the Paystack dashboard:

```
Callback URL: https://<your-id>.ngrok-free.app/orders/paystack/callback/
Webhook URL:  https://<your-id>.ngrok-free.app/orders/paystack/webhook/
```

Add the ngrok host to `ALLOWED_HOSTS` in `.env`.

### Payment flow

1. Buyer selects tickets and clicks **Pay with Paystack**
2. A **pending** order is created and the buyer is redirected to Paystack
3. After payment, Paystack redirects to the callback URL
4. The server **verifies the transaction** with the Paystack API before marking the order **paid**
5. The webhook (`charge.success`) acts as a reliable backup confirmation
6. Free orders (total = 0) skip Paystack and confirm immediately

### Withdrawals

1. Organizer adds a bank account (the account is verified through Paystack and the account name is fetched automatically)
2. A Paystack transfer recipient is created and stored
3. Organizer requests a withdrawal and the Paystack Transfer API is called
4. `transfer.success` / `transfer.failed` webhooks update the withdrawal status

> Available balance = total paid order revenue − completed withdrawals − withdrawals in transit.
> Paystack Transfers must be enabled on your Paystack account, and your Paystack balance must cover the payout.

---

## 🔐 Security

- Email-based authentication with Django's password hashing
- CSRF protection on all forms
- Server-side payment verification, plus a webhook signature check (HMAC SHA-512)
- Tickets use non-sequential UUIDs and QR payloads in the form `TURNUPCITY:<uuid>`
- Staff can only scan tickets for organizers that approved them
- Every scan attempt is logged, and used tickets can't be scanned twice
- Role checks and ownership checks on organizer, staff and admin views

---

## 🧪 Typical Walkthrough

1. Sign up as an **Organizer** and complete the organizer profile
2. In `/admin/`, set the organizer's status to **Verified**
3. Create an event, add a ticket type (quantity > 0, **Active** ticked) and **Publish** it
4. Sign up as an attendee in another browser and buy a ticket
5. Open the ticket from **My Tickets** to see the QR code
6. As organizer or approved staff, open **Check-In**, scan the QR code and watch the scan history update
7. Open **Dashboard → Withdrawals** to add a bank account and withdraw earnings

---

## 🌍 Deployment Notes

- Set `DEBUG=False` and a strong `SECRET_KEY`
- Set `ALLOWED_HOSTS` to your domain
- Run `python manage.py collectstatic`
- Serve media files (event banners, avatars, QR codes) from persistent storage such as S3 or Cloudinary, since many hosts use ephemeral disks
- Configure a real SMTP provider for emails
- Switch to live Paystack keys and set the live callback and webhook URLs
- Serve everything over HTTPS (the camera scanner requires a secure context outside `localhost`)
- Consider Celery for large email broadcasts

---

## 🗺️ Roadmap

- [ ] Self-service organizer verification dashboard
- [ ] Email notifications for approvals, refunds and withdrawals
- [ ] Platform fee / commission on ticket sales
- [ ] Automatic Paystack refunds on approved refund requests
- [ ] Ticket transfer between attendees
- [ ] Multi-currency support

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m "Add my feature"`
4. Push the branch: `git push origin feature/my-feature`
5. Open a Pull Request

---

## 📄 License

Add your preferred license here (for example MIT) and include a `LICENSE` file in the repository.

---

## 👤 Author

**Rhunor**

Built as a full-stack Django project covering architecture, backend, frontend and payments.