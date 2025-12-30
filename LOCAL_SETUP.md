# 🏠 Local Setup Guide

This guide shows you how to run the Agora demos on your local machine (Mac, Linux, or Windows).

## 📋 Prerequisites

- Python 3.8 or higher
- pip or pip3 installed

## 🚀 Quick Start (5 minutes)

### 1. Install Dependencies

```bash
# Install Python dependencies
pip3 install traceloop-sdk openai supabase python-dotenv

# Install Agora (for comparison mode)
pip3 install -e .
```

### 2. Create `.env` File

Copy the example and fill in your credentials:

```bash
cp .env.example .env
```

Then edit `.env` with your favorite editor:

```bash
# .env file
OPENAI_API_KEY=sk-proj-YOUR_KEY_HERE
TRACELOOP_API_KEY=tl_6894c89d3a0343afab2828f7cf371a25
VITE_SUPABASE_URL=https://tfueafatqxspitjcbukq.supabase.co
VITE_SUPABASE_ANON_KEY=YOUR_SUPABASE_KEY_HERE
AGORA_API_KEY=YOUR_AGORA_KEY_HERE
AGORA_PROJECT_ID=YOUR_PROJECT_ID_HERE
```

**Important:** The `.env` file is in `.gitignore` so your secrets won't be committed!

### 3. Run the Demo

**Option A: Traceloop + Agora Comparison** (recommended)
```bash
python3 traceloop_comparison.py
```

**Option B: Traceloop Only** (simpler, no Agora needed)
```bash
python3 colab_traceloop_only.py
```

**Option C: Interactive Chatbot**
```bash
python3 interactive_chatbot.py
```

### 4. View Telemetry

Open both dashboards:
- **Traceloop**: https://app.traceloop.com
- **Agora**: http://localhost:5173/live (if running locally)

---

## 🔧 Detailed Instructions

### If you get "pip not found":

Use `pip3` instead:
```bash
pip3 install traceloop-sdk openai supabase python-dotenv
```

### If you get "python not found":

Use `python3` instead:
```bash
python3 traceloop_comparison.py
```

### If you get "No module named 'agora'":

You need to install Agora in development mode:
```bash
cd /path/to/Agora
pip3 install -e .
```

Or run Traceloop-only mode:
```bash
python3 colab_traceloop_only.py  # This doesn't need Agora installed
```

### If you get "OPENAI_API_KEY not set":

Make sure:
1. You created `.env` file
2. You added `OPENAI_API_KEY=sk-...` to it
3. The file is in the same directory as the script

---

## 📁 File Guide

| File | Description | Needs Agora? |
|------|-------------|--------------|
| `traceloop_comparison.py` | Compare Traceloop + Agora side-by-side | Optional |
| `colab_traceloop_only.py` | Traceloop only, preset queries | No |
| `interactive_chatbot.py` | Interactive Q&A with telemetry | Yes |
| `colab_setup.py` | **COLAB ONLY** - Don't run locally! | N/A |

---

## ✅ Expected Output

When you run `traceloop_comparison.py` successfully, you should see:

```
✅ Loaded credentials from .env file
🔧 Initializing Traceloop SDK...
Traceloop exporting traces to https://api.traceloop.com authenticating with bearer token

✅ Traceloop initialized!
📊 View telemetry at: https://app.traceloop.com

🔧 Also initializing Agora telemetry...
✅ Supabase uploader enabled for project: Traceloop Comparison
✅ Traceloop initialized: comparison-chatbot
✅ Agora telemetry enabled!
📊 View at: http://localhost:5173/live

Choose mode:
1. Demo mode (3 preset queries)
2. Interactive mode (ask your own questions)

Enter 1 or 2:
```

---

## 🐛 Troubleshooting

### "NameError: name 'get_ipython' is not defined"

You're running `colab_setup.py` which is **Colab-only**. Use `traceloop_comparison.py` instead:
```bash
python3 traceloop_comparison.py
```

### "ModuleNotFoundError: No module named 'dotenv'"

Install python-dotenv:
```bash
pip3 install python-dotenv
```

### "No telemetry showing up in Agora"

1. Make sure the Agora frontend is running:
   ```bash
   cd platform/frontend
   npm run dev
   ```

2. Check you set the Supabase credentials in `.env`

3. Make sure you installed Agora:
   ```bash
   pip3 install -e .
   ```

### "Traceloop works but Agora doesn't capture anything"

This should be fixed now! The latest code auto-creates standalone executions. Make sure you have the latest version:

```bash
git pull origin claude/llm-token-tracking-VfDEH
pip3 install -e . --force-reinstall
```

---

## 🎯 Next Steps

1. **Test Traceloop only** first:
   ```bash
   python3 colab_traceloop_only.py
   ```
   Check https://app.traceloop.com for telemetry

2. **Then test Agora**:
   ```bash
   # Start frontend
   cd platform/frontend && npm run dev

   # In another terminal, run demo
   python3 traceloop_comparison.py
   ```
   Check both dashboards

3. **Compare** the two telemetry systems!

---

Happy testing! 🚀
