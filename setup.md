Perfect 👍 Here’s a clean **`SETUP.md`** you can drop into your repo so teammates can get up and running quickly:

---

# 🚀 Project Setup Guide – OmniDesk AI

This guide explains how to set up the **backend (FastAPI)** with **Neon (Postgres)** and **Qdrant (vector DB)** so that anyone who clones the repo can run it locally or deploy it.

---

## 1️⃣ Prerequisites

Make sure you have:

* **Python 3.9+**
* **Node.js v18+** (for frontend, if needed)
* **Git**
* A free **Neon** account ([https://neon.tech](https://neon.tech))
* A free **Qdrant Cloud** account ([https://cloud.qdrant.io](https://cloud.qdrant.io))
* API key for **Anthropic Claude** ([https://console.anthropic.com](https://console.anthropic.com))

---

## 2️⃣ Clone Repository

```bash
git clone https://github.com/<your-org>/<your-repo>.git
cd <your-repo>
```

---

## 3️⃣ Environment Variables

We use `.env` for all secrets.

1. Copy the example file:

   ```bash
   cp .env.example .env
   ```

2. Open `.env` and fill in your details:

   ```env
   # Neon Postgres
   DATABASE_URL=postgresql://<user>:<password>@<host>/<db>?sslmode=require

   # Qdrant Cloud
   QDRANT_URL=https://<your-cluster>.cloud.qdrant.io
   QDRANT_API_KEY=<your-qdrant-key>

   # Claude API
   ANTHROPIC_API_KEY=<your-claude-api-key>
   ```

---

## 4️⃣ Python Dependencies

Install backend dependencies:

```bash
pip install -r requirements.txt
```

*(use a virtual environment if you prefer)*

---

## 5️⃣ Database Setup (Neon)

1. Make sure your `.env` has a valid `DATABASE_URL`.

2. Run migrations with Alembic:

   ```bash
   alembic upgrade head
   ```

3. (Optional) Run smoke test:

   ```bash
   python scripts/smoke_db_test.py
   ```

   You should see:

   ```
   MODULES_IMPORTED
   TABLES_CREATED
   ```

---

## 6️⃣ Vector DB Setup (Qdrant)

The backend will auto-create collections in Qdrant when first run.
To verify connection:

```bash
python steup_env.py
```

Expected output (truncated):

```
✅ Database connection successful
✅ Database tables created
✅ Qdrant connection successful. Collections: 1
✅ Claude API connection successful
✅ Sample data created
🎉 Environment setup completed successfully!
```

---

## 7️⃣ Run Backend Locally

```bash
uvicorn main:app --reload
```

Visit: [http://localhost:8000/health](http://localhost:8000/health) → should return:

```json
{"status": "healthy", "timestamp": "..."}
```

---

## 8️⃣ Frontend (Optional)

If you’re working on the Next.js frontend:

```bash
cd frontend
npm install
npm run dev
```

Visit: [http://localhost:3000](http://localhost:3000)

---

## 9️⃣ Deployment

* **Backend** → Deploy to **Railway** or **Render**.

  * Use `railway.json` for auto start command.
  * Add all env vars (`DATABASE_URL`, `QDRANT_URL`, `QDRANT_API_KEY`, `ANTHROPIC_API_KEY`) in Railway dashboard.

* **Frontend** → Deploy to **Vercel**.

  * Add API base URL as env var.

---

## ✅ Quick Recap

1. Clone repo
2. Copy `.env.example` → `.env` and fill keys
3. `pip install -r requirements.txt`
4. `alembic upgrade head`
5. `python steup_env.py`
6. `uvicorn main:app --reload`

---

Now your system is fully connected to **Neon + Qdrant + Claude AI** 🎉

---

Do you want me to also make a **`.env.example` file** right now, tailored to your project, so you can commit it alongside `SETUP.md`?
