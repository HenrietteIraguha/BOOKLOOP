# BookLoop

BookLoop is a web platform that collects school books that families no longer use and redistributes them to children who have no books or library access in Rwanda: households, community groups and schools that run take-home lending.

Donors submit a donation through a public form, without an account. Operators review donations, register and assess the books, keep the inventory, match books to recipients' needs and record every distribution. Administrators manage the team's accounts.

**Live site:** https://bookloop.henrietteinc.tech
(If the site has not been used for a while, the first page can take up to a minute to load while the free server wakes up.)

Built by Henriette Iraguha for Introduction to Software Engineering, African Leadership University, 2026.

---

## Try it: test accounts

Two test accounts are set up on the live site so reviewers can try both staff roles:

| Username | Role | What you can try |
|---|---|---|
| `grader` | Operator | Review donations, register books (barcode, ISBN lookup, cover OCR), search the inventory and change statuses, manage recipients, record distributions, view reports, choose homepage books |
| `grader-admin` | Administrator | Everything an operator can do, plus the Team page: create accounts, change roles, deactivate accounts |

The passwords are in the project submission document, not in this public repository.

Log in at https://bookloop.henrietteinc.tech/accounts/login/. No account is needed to view the homepage or submit a donation.

---

## Features


| SRS requirement | Where to find it |
|---|---|
| FR1 Book intake registration | Register a book |
| FR2 Barcode / ISBN lookup (Open Library, Google Books) | Register a book: scan the barcode, upload a photo of it, or type the ISBN |
| FR3 OCR cover fallback | Register a book: "No barcode? Read the cover" (Tesseract.js, runs in the browser) |
| FR4–FR6 Manual entry, classification, confirmation | Register a book: check and correct every suggested detail; BookLoop records whether details were typed, confirmed or corrected |
| FR7 Book suitability (pending, accepted, rejected) | Register a book, and the inventory list |
| FR8 Inventory with available quantities | Inventory |
| FR9 Book status tracking (with history) | Inventory: "Change status" on each row |
| FR10 Community registry | Recipients |
| FR11 Book-to-need matching | Distribution: choose a recipient, see matching books |
| FR12 Public donation form, no account | Homepage → Donate books |
| FR13 Donation review and status | Donations |
| FR14 Link books to their donation | Donations → open a donation → Register books from this donation |
| FR15 Login | /accounts/login/ |
| FR16 Account and role management | Team (administrators only) |
| FR17 Distribution recording, inventory updated | Distribution |
| FR18 Search and filter | Inventory |
| FR19 Reports | Reports |
| FR20 Donated books slideshow | Homepage; operators choose books and covers in Inventory → Homepage showcase |

## Built with

- **Backend:** Python 3.12, Django 6.1
- **Database:** PostgreSQL (Neon in production)
- **Frontend:** Django templates, one shared CSS file, small vanilla JavaScript
- **Barcode scanning:** html5-qrcode · **OCR:** Tesseract.js
- **Photo storage:** Cloudinary in production (local `media/` folder in development)
- **Hosting:** Render (web service), with WhiteNoise for static files and gunicorn as the server

## Project structure


```
BOOKLOOP/
├── config/          settings, main URLs, Cloudinary storage, test helpers
├── accounts/        roles (setup_roles command) and the Team page
├── inventory/       books, inventory lots, status history, ISBN lookup, showcase management
├── donations/       donors, donation submissions, photos
├── communities/     recipients and their needs
├── distribution/    recording distributions
├── reports/         summary reports
├── public/          homepage, donation form, public book covers
├── dashboard/       operator home page
├── templates/       all HTML templates
├── static/          css/bookloop.css, js/bookloop.js, images/
├── build.sh         build script used by Render on every deploy
└── requirements.txt Python packages
```

---

## Run BookLoop on your own computer

These steps were written on Windows with Git Bash. Mac and Linux commands are shown where they differ.

### 1. Install the tools

- **Python 3.12** from https://www.python.org/downloads/ (on Windows, tick "Add python.exe to PATH" during installation)
- **PostgreSQL** (version 16 or newer) from https://www.postgresql.org/download/ — remember the password you choose for the `postgres` user
- **Git** from https://git-scm.com/downloads (on Windows this also installs Git Bash)

Check they are installed:

```bash

python --version
git --version
psql --version
```

(On Mac/Linux, use `python3` instead of `python` if `python` is not found.)

### 2. Get the code

```bash
git clone https://github.com/HenrietteIraguha/BOOKLOOP.git
cd BOOKLOOP
```

### 3. Create and activate a virtual environment

A virtual environment keeps BookLoop's packages separate from the rest of your computer.

```bash
python -m venv venv
source venv/Scripts/activate      # Windows (Git Bash)
# source venv/bin/activate        # Mac / Linux
```

Your terminal line should now start with `(venv)`. Activate it again every time you open a new terminal.

### 4. Install the packages

```bash
pip install -r requirements.txt
```


### 5. Create the database

```bash
psql -U postgres -c "CREATE DATABASE bookloop;"
```

Type your `postgres` password when asked. (You can also create a database named `bookloop` in pgAdmin.)

### 6. Create your settings file (.env)

```bash
cp .env.example .env
```

Open `.env` in a text editor and fill it in:

- `SECRET_KEY`: generate one with
  ```bash
  python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
  ```
- `DB_PASSWORD`: the `postgres` password from step 1.
- Leave `CLOUDINARY_URL` commented out: photos will be saved in a local `media/` folder.

`.env` holds secrets and is listed in `.gitignore`, so it is never uploaded to GitHub.

### 7. Create the tables, the roles and your account

```bash
python manage.py migrate
python manage.py setup_roles
python manage.py createsuperuser
```


- `migrate` creates all database tables.
- `setup_roles` creates the **Operator** and **Administrator** roles with their permissions. Run it after `migrate`.
- `createsuperuser` creates your own owner account (choose a username and password).

### 8. Start the server

```bash
python manage.py runserver 8080
```

Open http://127.0.0.1:8080 for the public homepage, and http://127.0.0.1:8080/accounts/login/ to log in. Stop the server with `Ctrl + C`.

### 9. Run the automated tests

```bash
python manage.py test
```

19 tests check donations, access rules, inventory status, search, distribution and reports. They use a temporary database that is deleted afterwards, so your data is not touched. The last line should say `OK`.

---

## Roles

| Role | Can do |
|---|---|
| Website visitor / donor | See the homepage and slideshow, submit a donation (no account) |
| Operator | Review donations, register books, manage inventory and statuses, manage recipients, record distributions, view reports, choose homepage books |
| Administrator | Everything an operator can, plus create accounts, change roles and deactivate accounts on the Team page |

To give someone a role, log in as an administrator (or the superuser), open **Team** and create their account. No role can delete records: deactivating an account stops the person logging in but keeps everything they recorded.


---

## Deployment (Render + Neon + Cloudinary)

This is how the live site is set up. All three services have free plans that need no bank card.

### 1. Database on Neon
1. Sign up at https://neon.tech and create a project (region: Europe Central / Frankfurt, close to Rwanda) with a database named `bookloop`.
2. Copy the connection string (`postgresql://...`). This becomes `DATABASE_URL`.

### 2. Photo storage on Cloudinary
1. Sign up at https://cloudinary.com.
2. Under API Keys, copy the "API environment variable". Its value, starting with `cloudinary://`, becomes `CLOUDINARY_URL`.

Render's free plan deletes files saved on its own disk at every restart, so uploaded photos must be stored on Cloudinary.

### 3. Web service on Render
1. Sign up at https://render.com with GitHub and create a **Web Service** from this repository (branch `main`, region Frankfurt, Free plan).
2. **Build command:** `bash build.sh`
   It installs the packages, collects the static files, runs the migrations, runs `setup_roles` and creates the superuser.
3. **Start command:** `gunicorn config.wsgi:application`
4. **Environment variables:**

| Key | Value |
|---|---|
| `SECRET_KEY` | use Render's "Generate" button |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | `.onrender.com,bookloop.henrietteinc.tech` |
| `CSRF_TRUSTED_ORIGINS` | `https://*.onrender.com,https://bookloop.henrietteinc.tech` |
| `SECURE_HTTPS` | `True` |
| `DATABASE_URL` | the Neon connection string (no quotes) |
| `CLOUDINARY_URL` | the value starting with `cloudinary://` (without `CLOUDINARY_URL=` in front) |
| `DJANGO_SUPERUSER_USERNAME` | the owner account's username |
| `DJANGO_SUPERUSER_EMAIL` | the owner's email |
| `DJANGO_SUPERUSER_PASSWORD` | a strong password |
| `PYTHON_VERSION` | `3.12.1` |

Every push to `main` deploys automatically. If it does not, use **Manual Deploy → Deploy latest commit**.

### 4. Custom domain
1. In Render: Settings → Custom Domains → add `bookloop.henrietteinc.tech`.
2. At the domain provider, add a **CNAME** record: host `bookloop`, value `bookloop-wrts.onrender.com`. A CNAME points to Render's name rather than a fixed IP address, so the domain keeps working if Render's servers change.
3. Render verifies the record and issues a free HTTPS certificate.
4. Add the domain to `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` (see the table above).

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `No module named django` | The virtual environment is not active: run `source venv/Scripts/activate` (Windows) or `source venv/bin/activate` (Mac/Linux). |
| The page on port 8000 is empty or doesn't load | Another program uses port 8000. Use `python manage.py runserver 8080`. |
| `ImproperlyConfigured: Set the DB_NAME environment variable` | `.env` is missing or not in the project folder. Repeat step 6. |
| `password authentication failed for user "postgres"` | `DB_PASSWORD` in `.env` does not match your PostgreSQL password. |
| Team page shows 403, or roles are missing | Run `python manage.py setup_roles`. |
| "CSRF verification failed" when submitting a form | Refresh the page and submit again (this happens if you logged in in another tab after opening the form). On a new domain, check `CSRF_TRUSTED_ORIGINS`. |
| Cloudinary error "Must supply cloud_name" | `CLOUDINARY_URL` is missing or written twice, e.g. `CLOUDINARY_URL=CLOUDINARY_URL=...`. It must start with `cloudinary://`. |
| Photos disappear after a deploy | They were saved before Cloudinary was set up. Upload them again. |
| The live site is slow to open | The free Render plan sleeps after inactivity. Wait up to a minute. |

---


## Documents

- Software Requirements Specification (SRS):https://docs.google.com/document/d/1-HnQo4Gzf3K5NWCqj--hE1MNC_2aVd-tHczzyO9qcRo/edit?tab=t.0#heading=h.n8qheqbqtgun
