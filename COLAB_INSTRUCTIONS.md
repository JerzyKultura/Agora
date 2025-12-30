# 🚀 Running Agora Demos in Google Colab

This guide shows you how to run the Traceloop comparison demos in Google Colab.

## 📋 Prerequisites

You'll need:
1. **OpenAI API Key**: Get from https://platform.openai.com/api-keys
2. **Traceloop API Key**: Get from https://app.traceloop.com
3. **Agora Credentials** (optional, for comparison):
   - Supabase URL
   - Supabase Anon Key
   - Agora API Key
   - Agora Project ID

## 🎯 Option 1: Traceloop Only (Simplest)

Perfect if you just want to see Traceloop's telemetry in action.

### Steps:

1. **Open Google Colab**: https://colab.research.google.com
2. **Create a new notebook**
3. **Copy the entire content** of `colab_traceloop_only.py` into a cell
4. **Update the API keys** (lines 24-25):
   ```python
   OPENAI_API_KEY = "your-openai-key-here"
   TRACELOOP_API_KEY = "tl_6894c89d3a0343afab2828f7cf371a25"  # Already set
   ```
5. **Run the cell**
6. **View telemetry** at: https://app.traceloop.com

### What You'll See:
- 3 automated LLM queries
- Full prompts and responses
- Token usage and costs
- Model parameters
- Latency timings

---

## 🔄 Option 2: Traceloop vs Agora Comparison

Compare Traceloop's dashboard with Agora's Live Telemetry side-by-side.

### Steps:

1. **Open Google Colab**: https://colab.research.google.com
2. **Create a new notebook**
3. **Add this setup cell** and run it:
   ```python
   # Install dependencies
   !pip install -q traceloop-sdk openai supabase
   !pip install -q git+https://github.com/JerzyKultura/Agora.git
   ```

4. **Create a new cell** and paste the entire content of `traceloop_comparison.py`

5. **Update the credentials** (lines 37-49):
   ```python
   OPENAI_API_KEY = "your-openai-key"
   TRACELOOP_API_KEY = "tl_6894c89d3a0343afab2828f7cf371a25"
   AGORA_SUPABASE_URL = "your-supabase-url"
   AGORA_SUPABASE_KEY = "your-supabase-anon-key"
   AGORA_API_KEY = "your-agora-api-key"
   AGORA_PROJECT_ID = "your-project-id"
   ```

6. **Uncomment the install lines** (lines 28-29):
   ```python
   !pip install -q traceloop-sdk openai
   !pip install -q git+https://github.com/JerzyKultura/Agora.git
   ```

   (Or skip if you did step 3)

7. **Run the cell**

8. **View telemetry in both dashboards**:
   - **Traceloop**: https://app.traceloop.com
   - **Agora**: http://localhost:5173/live (if running locally) or your hosted URL

### What You'll Compare:
- ✅ Prompt/response display
- ✅ Token tracking
- ✅ Cost calculations
- ✅ Model metadata
- ✅ Real-time streaming (Agora)
- ✅ UI/UX differences

---

## 🔐 Using Colab Secrets (Recommended)

Instead of hardcoding API keys, use Colab's built-in secrets feature:

1. Click the **🔑 key icon** in the left sidebar
2. Add your secrets:
   - `OPENAI_API_KEY`
   - `TRACELOOP_API_KEY`
   - `AGORA_SUPABASE_URL`
   - `AGORA_SUPABASE_KEY`
   - `AGORA_API_KEY`
   - `AGORA_PROJECT_ID`

3. **Update the code** to use secrets:
   ```python
   from google.colab import userdata

   OPENAI_API_KEY = userdata.get('OPENAI_API_KEY')
   TRACELOOP_API_KEY = userdata.get('TRACELOOP_API_KEY')
   AGORA_SUPABASE_URL = userdata.get('AGORA_SUPABASE_URL')
   # ... etc
   ```

---

## 📊 Expected Results

### Traceloop Dashboard Shows:
- **Traces** tab: All LLM calls organized by session
- **Prompt** tab: Full user prompts
- **Completions** tab: Full LLM responses
- **LLM Data** tab: Model, temperature, tokens, cost
- **Details** tab: Timestamps, latency, metadata

### Agora Live Telemetry Shows:
- Real-time streaming spans
- LLM badge indicators
- Collapsible attributes
- Token counts
- Temperature settings
- **Note**: Make sure to check the span attributes to verify prompt/response extraction

---

## 🐛 Troubleshooting

### Issue: "Module not found" errors
**Solution**: Make sure you ran the installation cell first

### Issue: "API key invalid"
**Solution**: Double-check your API keys are correct and active

### Issue: "Agora Live Telemetry shows spans but no prompts"
**Solution**: Expand the span attributes (`▶ View all N attributes`) to verify the data is there. The extraction may need adjustment based on Traceloop's attribute names.

### Issue: "Can't connect to localhost"
**Solution**: Agora's frontend needs to be running. If you're only in Colab, you won't be able to access `localhost:5173`. Consider:
- Running the frontend locally and using ngrok to expose it
- Only using Traceloop dashboard for now
- Checking Supabase directly for the data

---

## 🎓 Learn More

- **Traceloop Docs**: https://docs.traceloop.com
- **Agora Repo**: https://github.com/JerzyKultura/Agora
- **OpenAI API**: https://platform.openai.com/docs

---

## 💡 Tips

1. **Start with `colab_traceloop_only.py`** to verify Traceloop works
2. **Then try the comparison** once you have both systems working
3. **Use the interactive mode** to test your own queries
4. **Check both dashboards** immediately after running to see real-time updates

---

Happy testing! 🚀
