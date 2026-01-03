# Quick Test Guide - See Chat Messages in Monitoring

## Step 1: Set up your .env file

Edit `.env` and add your keys:
```bash
OPENAI_API_KEY=sk-proj-YOUR_ACTUAL_KEY
VITE_SUPABASE_URL=https://tfueafatqxspitjcbukq.supabase.co
VITE_SUPABASE_ANON_KEY=YOUR_ACTUAL_SUPABASE_KEY
```

## Step 2: Install dependencies

```bash
pip install traceloop-sdk openai supabase python-dotenv
```

## Step 3: Run the test

```bash
python3 test_chat_messages.py
```

## Step 4: View in your browser

1. Open http://localhost:5173/monitoring
2. You should see a new trace appear
3. Click on the trace
4. Click on the "openai.chat" span in the left panel
5. Look at the tabs on the right:
   - **Prompt** tab: Shows your chat messages
   - **Completions** tab: Shows the AI response
   - **LLM Data** tab: Shows model, tokens, cost

## What you should see:

**Prompt Tab:**
```
SYSTEM
You are a helpful assistant.

USER
What is 2+2? Answer in one sentence.
```

**Completions Tab:**
```
ASSISTANT
2 + 2 equals 4.
```

**LLM Data Tab:**
```
Model: gpt-4
Provider: openai
Temperature: 0.7
Token Usage: 25 input + 8 output = 33 total
```

## Running from Colab or different PC:

YES! You can run the Python script from anywhere:

1. **On Colab:**
   - Use `traceloop_comparison.py`
   - Set your API keys in the script
   - The telemetry goes to Supabase cloud
   - View it on http://localhost:5173/monitoring (your local frontend)

2. **On a different PC:**
   - Copy the Agora SDK folder
   - Set the same `VITE_SUPABASE_URL` in .env
   - Run your LLM calls
   - Data appears on ANY machine viewing the same Supabase

The key: **Supabase is in the cloud**, so telemetry from anywhere shows up everywhere!
