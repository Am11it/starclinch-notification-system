# Notification System (Django + React)

Admin manages every notification from **one table**: rows = triggers, columns = WhatsApp / Email / Web Push.
When something happens on the website (login, logout, order...), the backend sends every *enabled*
template of that trigger.

```
backend/   Django + DRF API      -> deploy on Render
frontend/  React (Vite) website  -> deploy on Vercel
```

## How it works (read this first)

```
User logs in on website
   └─> POST /api/auth/login/
         └─> fire_trigger("login", user)            backend/notifications/services.py
               ├─ WhatsApp template ON?  -> senders/whatsapp.py  (WhatsApp Cloud API)
               ├─ Email template ON?     -> senders/email.py     (Resend)
               └─ Web Push template ON?  -> senders/webpush.py   (OneSignal)
               every attempt is saved in NotificationLog (shown in admin as "Recent sends")
```

| Concept | Where in code |
|---|---|
| Trigger (a table row) | `Trigger` model — `backend/notifications/models.py` |
| Template (a table cell) | `Template` model — body, subject/title, on/off toggle, WhatsApp status + variable mapping |
| Sending | `backend/notifications/services.py` → `fire_trigger`, `send_one` |
| One file per channel | `backend/notifications/senders/` |
| Admin screen | `frontend/src/pages/AdminNotifications.jsx` |
| Website (login, logout, order) | `frontend/src/pages/` + `frontend/src/components/Navbar.jsx` |

**Variables** — write `{{name}}`, `{{email}}`, `{{phone}}`, `{{trigger}}`, `{{time}}`, `{{site_name}}` in any template.
For WhatsApp, Meta wants `{{1}}`, `{{2}}`…, so on *Sync* we convert names to numbers and store the order
in `wa_variables` (the variable mapping).

## Triggers built

| Key | Fires when |
|---|---|
| `login` | User logs in |
| `logout` | User logs out |
| `signup` | User creates an account |
| `password_reset` | "Forgot password" form |
| `order_placed` | "Place an order" button on the website |
| `inactive_1_day` / `inactive_1_week` | No visit for 24h / 7 days — checked every hour (see below) |

Every trigger comes with starter templates for **all 3 channels** (migrations `0002` and `0003`),
editable from the admin screen. A "visit" = any page load while logged in (`/api/auth/me/`), so a user who
stays logged in is not wrongly treated as inactive. Each inactive message is sent once per absence.

Admins can add, rename or delete triggers from the admin screen. Website code fires any trigger with
`POST /api/events/fire/ {"trigger": "<key>"}`.

## Run locally

**Backend**
```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # fill in your sandbox keys
python manage.py migrate        # also creates the trigger rows
python manage.py ensure_admin   # creates admin from ADMIN_EMAIL / ADMIN_PASSWORD
python manage.py runserver
```

**Frontend**
```bash
cd frontend
npm install
cp .env.example .env            # VITE_API_URL + VITE_ONESIGNAL_APP_ID
npm run dev                     # http://localhost:5173
```

## Log in as admin

Use `ADMIN_EMAIL` / `ADMIN_PASSWORD` (default local: `admin@example.com` / `admin123`).
You land on **Notification Settings**. At the top, **Send tests to** lets you choose the email / WhatsApp number
for the **Test** buttons (empty = your own profile). For Web Push tests, open **My account** and click
**Enable push notifications** in the browser you'll test with.

## Env vars

Backend (`backend/.env`):

| Var | What |
|---|---|
| `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` | Django basics |
| `CRON_SECRET` | Shared secret for the hourly inactivity check (GitHub Actions secret must match) |
| `DEFAULT_COUNTRY_CODE` | Added to 10-digit phone numbers for WhatsApp (default `91`) |
| `CORS_ALLOWED_ORIGINS` | Frontend URL, e.g. `https://your-app.vercel.app` |
| `DATABASE_URL` | Empty = SQLite. On Render = Postgres URL |
| `ADMIN_EMAIL`, `ADMIN_PASSWORD` | Admin account |
| `WHATSAPP_ACCESS_TOKEN`, `PHONE_NUMBER_ID`, `WHATSAPP_BUSINESS_ACCOUNT_ID` | Meta sandbox (API Setup page) |
| `RESEND_API_KEY`, `RESEND_FROM_EMAIL` | Resend. Without a domain: from `onboarding@resend.dev`, only to your Resend account email |
| `ONESIGNAL_APP_ID`, `ONESIGNAL_REST_API_KEY` | OneSignal web app |

Frontend (`frontend/.env`): `VITE_API_URL`, `VITE_ONESIGNAL_APP_ID`.

Email provider used: **Resend** (`backend/notifications/senders/email.py`).

## Sandbox notes

- **WhatsApp**: add your number to the test recipient list in Meta. Create the template → **Sync** (submits to Meta)
  → press **Sync** again until `APPROVED` → **Test**. Until it's approved we send plain text, which Meta only
  delivers if you messaged the test number in the last 24h. Temporary tokens expire — regenerate when sends fail.
- **Web Push**: in OneSignal create a *Web* app with your site URL (Vercel URL, or `http://localhost:5173` locally).
  `frontend/public/OneSignalSDKWorker.js` is the service worker it needs.
- **Not logged in for 1 day / 1 week** run automatically every hour: Render's free tier has no cron, so
  `.github/workflows/inactivity-check.yml` (GitHub Actions, free) calls `POST /api/cron/inactivity-check/`
  with the `X-Cron-Secret` header. In GitHub → Settings → Secrets → Actions add `BACKEND_URL` and `CRON_SECRET`
  (same value as on Render). Admins can also press **Run "not logged in" check now**, or run
  `python manage.py check_inactive_users`.

## Deploy

- **Backend → Render**: New → Blueprint → this repo (uses `render.yaml`), then fill in the env vars.
  Or create a Web Service manually with root `backend`, build `./build.sh`, start `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --timeout 120`.
- **Frontend → Vercel**: import repo, root directory `frontend`, set `VITE_API_URL` (Render URL) and
  `VITE_ONESIGNAL_APP_ID`. `vercel.json` makes page refreshes work on routes like `/admin`.
- Put the Vercel URL into the backend's `CORS_ALLOWED_ORIGINS`.

## API

| Method | URL | Who |
|---|---|---|
| POST | `/api/auth/signup/`, `/api/auth/login/`, `/api/auth/password-reset/` | anyone |
| POST | `/api/auth/logout/` · GET/PATCH `/api/auth/me/` · POST `/api/events/fire/` | logged-in user |
| GET/POST/PATCH/DELETE | `/api/admin/triggers/`, `/api/admin/templates/` | admin |
| POST | `/api/admin/templates/<id>/test/`, `/api/admin/templates/<id>/sync/` | admin |
| GET | `/api/admin/logs/`, `/api/admin/variables/` · POST `/api/admin/run-inactivity-check/` | admin |
| POST | `/api/cron/inactivity-check/` (header `X-Cron-Secret`) | scheduler |

## Task D — in simple words

**What is a trigger?** Something that happens on the website that should send a message. Examples:
a user logs in, a user places an order, a user asks to reset their password, a user hasn't visited for a week.

**What are the three channels?** WhatsApp (message on the phone, via WhatsApp Cloud API), Email (via Resend)
and Web Push (pop-up in the browser, via OneSignal).

**Why create templates in our admin panel instead of on Postmark / WhatsApp?** One screen for everything:
the admin sees every trigger and channel in one table, can edit text, turn channels on/off and test without
logging into three provider websites. Our backend stores the templates and fills in each user's details
(`{{name}}`, `{{time}}`…); it also submits WhatsApp templates to Meta for approval for us.

**What is Web Push?** A notification that pops up from the browser (even when the site tab is closed),
after the user clicks "Allow". It works only in browsers here — not iOS / Android apps.

## Checklist

- [x] Django backend: triggers, templates, on/off, variable mapping, test send, logs
- [x] React website (sign up, log in/out, order, password reset) + admin panel (one table)
- [x] 7 triggers, each with WhatsApp / Email / Web Push templates
- [x] Email working (Resend)
- [ ] WhatsApp sandbox keys + test phone added
- [ ] OneSignal keys + browser subscribed
- [ ] Deployed: backend on Render, frontend on Vercel
- [ ] GitHub repo + live URLs submitted
- [ ] Walkthrough video
