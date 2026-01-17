#!/bin/bash
# ============================================================================
# AGORA PLATFORM SETUP - Full Stack with Web UI
# ============================================================================

set -e

echo "========================================================================"
echo "🚀 AGORA PLATFORM SETUP"
echo "========================================================================"
echo ""

# Check if we're in the right directory
if [ ! -d "platform" ]; then
    echo "❌ Error: Run this from the Agora root directory"
    exit 1
fi

# ============================================================================
# 1. CREATE .env FILE
# ============================================================================

echo "📝 Step 1: Creating .env file..."

if [ ! -f .env ]; then
    cat > .env << 'EOF'
# OpenAI API Key (add your key here)
OPENAI_API_KEY=your_openai_key_here

# Supabase Credentials
VITE_SUPABASE_URL=https://tfueafatqxspitjcbukq.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRmdWVhZmF0cXhzcGl0amNidWtxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzY0NTAwNTcsImV4cCI6MjA1MjAyNjA1N30.9b3HqZ8wQYPx4FqPvPNKt8FPVFz_lqYHQJKwEQVL_rU
EOF
    echo "   ✅ .env created (add your OpenAI API key to .env file)"
else
    echo "   ℹ️  .env already exists, skipping"
fi

# ============================================================================
# 2. INSTALL BACKEND DEPENDENCIES
# ============================================================================

echo ""
echo "📦 Step 2: Installing backend dependencies..."
cd platform/backend

if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "   ✅ Virtual environment created"
fi

source venv/bin/activate
pip install -q -r requirements.txt
echo "   ✅ Backend dependencies installed"

cd ../..

# ============================================================================
# 3. INSTALL FRONTEND DEPENDENCIES
# ============================================================================

echo ""
echo "📦 Step 3: Installing frontend dependencies..."
cd platform/frontend

if [ ! -d "node_modules" ]; then
    npm install
    echo "   ✅ Frontend dependencies installed"
else
    echo "   ℹ️  node_modules exists, skipping"
fi

cd ../..

# ============================================================================
# 4. CREATE STARTUP SCRIPTS
# ============================================================================

echo ""
echo "📝 Step 4: Creating startup scripts..."

# Backend startup script
cat > start_backend.sh << 'EOF'
#!/bin/bash
echo "🚀 Starting Agora Backend..."
cd platform/backend
source venv/bin/activate
uvicorn main:app --reload --port 8000 --host 0.0.0.0
EOF
chmod +x start_backend.sh

# Frontend startup script
cat > start_frontend.sh << 'EOF'
#!/bin/bash
echo "🚀 Starting Agora Frontend..."
cd platform/frontend
npm run dev
EOF
chmod +x start_frontend.sh

# Combined startup script
cat > start_platform.sh << 'EOF'
#!/bin/bash
echo "========================================================================"
echo "🚀 STARTING AGORA PLATFORM"
echo "========================================================================"
echo ""
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:5173"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Starting services in background..."
echo ""

# Start backend
./start_backend.sh > backend.log 2>&1 &
BACKEND_PID=$!
echo "✅ Backend started (PID: $BACKEND_PID)"

# Wait for backend
sleep 3

# Start frontend
./start_frontend.sh > frontend.log 2>&1 &
FRONTEND_PID=$!
echo "✅ Frontend started (PID: $FRONTEND_PID)"

echo ""
echo "========================================================================"
echo "✅ AGORA PLATFORM RUNNING"
echo "========================================================================"
echo ""
echo "Access the platform:"
echo "  🌐 Frontend: http://localhost:5173"
echo "  📡 Backend API: http://localhost:8000"
echo "  📚 API Docs: http://localhost:8000/docs"
echo ""
echo "Logs:"
echo "  tail -f backend.log"
echo "  tail -f frontend.log"
echo ""
echo "To stop:"
echo "  kill $BACKEND_PID $FRONTEND_PID"
echo ""
echo "Process IDs saved to .platform_pids"
echo "$BACKEND_PID" > .platform_pids
echo "$FRONTEND_PID" >> .platform_pids
EOF
chmod +x start_platform.sh

# Stop script
cat > stop_platform.sh << 'EOF'
#!/bin/bash
if [ -f .platform_pids ]; then
    echo "Stopping Agora platform..."
    while read pid; do
        kill $pid 2>/dev/null && echo "  Stopped process $pid"
    done < .platform_pids
    rm .platform_pids
    echo "✅ Platform stopped"
else
    echo "No running platform found"
fi
EOF
chmod +x stop_platform.sh

echo "   ✅ Startup scripts created"

# ============================================================================
# 5. CREATE DEMO CHATBOT WITH PLATFORM INTEGRATION
# ============================================================================

echo ""
echo "📝 Step 5: Creating platform-integrated chatbot..."

cat > chatbot_with_platform.py << 'EOF'
"""
💬 Agora Chatbot with Platform Integration
Sends telemetry to the web platform for visualization
"""
from agora import init_agora
from agora.wide_events import set_business_context
from openai import OpenAI
import os

# Initialize Agora with platform upload
init_agora(
    app_name="chatbot-platform-demo",
    export_to_console=False,
    export_to_file="chatbot.jsonl",
    enable_cloud_upload=True,  # Upload to platform!
    project_name="chatbot-demo"
)

# Set business context
set_business_context(
    user_id="demo_user",
    custom={
        "app": "chatbot",
        "session": "platform_demo",
        "environment": "production"
    }
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

print("\n" + "="*80)
print("💬 AGORA CHATBOT - Platform Edition")
print("="*80)
print("")
print("Features:")
print("  ✅ All chats tracked in local file (chatbot.jsonl)")
print("  ✅ All telemetry uploaded to Agora platform")
print("  ✅ View conversation analytics at http://localhost:5173")
print("")
print("Type 'quit' to exit\n")

conversation = []

while True:
    user_input = input("You: ")

    if user_input.lower() in ['quit', 'exit', 'q']:
        break

    conversation.append({"role": "user", "content": user_input})

    # LLM call - tracked locally AND sent to platform!
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=conversation
    )

    assistant_message = response.choices[0].message.content
    conversation.append({"role": "assistant", "content": assistant_message})

    print(f"Bot: {assistant_message}\n")

print("\n✅ Session complete!")
print("📊 View your conversation analytics at: http://localhost:5173")
EOF

echo "   ✅ Platform chatbot created"

# ============================================================================
# SETUP COMPLETE
# ============================================================================

echo ""
echo "========================================================================"
echo "✅ AGORA PLATFORM SETUP COMPLETE!"
echo "========================================================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Start the platform:"
echo "   ./start_platform.sh"
echo ""
echo "2. Access the web UI:"
echo "   🌐 http://localhost:5173"
echo ""
echo "3. Check API docs:"
echo "   📚 http://localhost:8000/docs"
echo ""
echo "4. Run the chatbot:"
echo "   python3 chatbot_with_platform.py"
echo ""
echo "5. Stop the platform:"
echo "   ./stop_platform.sh"
echo ""
echo "Files created:"
echo "  • .env (credentials)"
echo "  • start_platform.sh (start everything)"
echo "  • stop_platform.sh (stop everything)"
echo "  • start_backend.sh (backend only)"
echo "  • start_frontend.sh (frontend only)"
echo "  • chatbot_with_platform.py (demo app)"
echo ""
echo "========================================================================"
