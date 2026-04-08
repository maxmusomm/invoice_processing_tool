# Vercel Hosting Guide

This application has been structured to run smoothly as a serverless function on Vercel. Since we removed Ollama (which required local inference) and shifted fully to the Gemini Cloud LLM architecture alongside a lightweight FastAPI/HTML stack, Vercel is a fantastic platform for this!

## Prerequisites
- A [Vercel](https://vercel.com/) account.
- The `Vercel CLI` installed (optional but easiest): `npm i -g vercel`.
- A valid `GEMINI_API_KEY`.

## Setup Information

I have automatically created a `vercel.json` file in the root directory. This tells Vercel's Python builder (`@vercel/python`) to correctly route all HTTP requests natively into the `main:app` FastApi instance without requiring a traditional separate server daemon like Uvicorn!

## Deployment Instructions (Vercel CLI)

1. Open your terminal in the project root.
2. Run the deployment command:
   ```bash
   vercel
   ```
3. The CLI will prompt you to set up and link the project. You can accept the defaults.
4. **Environment Variables!** Once prompted, or immediately after deployment via your Vercel Dashboard Settings, you *must* declare your environment variables to match your local `.env`:
   - `GEMINI_API_KEY` = your actual key
   - `GEMINI_MODEL` = `gemini-3.1-flash-lite-preview`
   
5. *Optional*: Deploy to production once tested:
   ```bash
   vercel --prod
   ```

## Deployment Instructions (via GitHub)

If you prefer continuous deployment (CI/CD) from your GitHub repository:
1. Ensure all your current files (including `vercel.json` and `frontend/index.html`) are pushed to your GitHub `main` branch.
2. Go to the [Vercel Dashboard](https://vercel.com/dashboard).
3. Click **Add New...** -> **Project**.
4. Import your newly pushed GitHub repository (`invoice_processing_tool`).
5. In the "Configure Project" screen, expand the **Environment Variables** section and add `GEMINI_API_KEY` and `GEMINI_MODEL`.
6. Click **Deploy**. Vercel will automatically read the `vercel.json` and `requirements.txt` configurations, build the Python environment naturally, and deploy your live URL.

## Important Note on Storage
Vercel serverless functions are computationally ephemeral! The `processed_invoices` list (and `.tmp/` directory) inside `main.py` acts as an in-memory cache and *will eventually clear itself* when the Vercel function goes to sleep from inactivity. Therefore, users should regularly "Export CSV" to keep records, or eventually, a remote persistent backend (like Supabase/PostgreSQL) can be wired into `main.py` for permanent long-term storage!
