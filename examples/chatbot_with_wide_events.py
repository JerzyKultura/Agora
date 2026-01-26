"""
Example: Chatbot with Wide Events / Business Context

This shows how to use Agora's wide events pattern in a real chatbot application.
"""

from openai import OpenAI
from agora.agora_tracer import init_agora
from agora.wide_events import BusinessContext, enrich_current_span
from traceloop.sdk import Traceloop
from datetime import datetime, timezone


# Initialize telemetry
Traceloop.init(app_name="production-chatbot", disable_batch=True)
init_agora(
    app_name="production-chatbot",
    project_name="Customer Support Bot",
    enable_cloud_upload=True
)

client = OpenAI()


class User:
    """Example user model"""
    def __init__(self, user_id, email, subscription, created_at, ltv):
        self.id = user_id
        self.email = email
        self.subscription = subscription
        self.created_at = created_at
        self.ltv = ltv

    @property
    def account_age_days(self):
        return (datetime.now(timezone.utc) - self.created_at).days


class ChatSession:
    """Example session model"""
    def __init__(self, session_id):
        self.id = session_id
        self.messages = []
        self.total_tokens = 0
        self.turn_number = 0

    def add_message(self, role, content):
        self.messages.append({"role": role, "content": content})
        self.turn_number += 1


def get_feature_flags(user: User) -> dict:
    """Get feature flags for a user"""
    return {
        "gpt4_access": user.subscription in ["pro", "enterprise"],
        "priority_support": user.subscription == "enterprise",
        "beta_features": user.ltv > 100000,  # $1000+ LTV gets beta access
        "advanced_analytics": user.subscription in ["pro", "enterprise"]
    }


def process_chat_message(
    user: User,
    session: ChatSession,
    message: str,
    workflow_type: str = "customer_support"
) -> str:
    """
    Process a chat message with full business context enrichment.

    This is the key pattern: build your context, enrich the span,
    then make the LLM call. All the context will be attached to the
    telemetry automatically.
    """

    # Build comprehensive business context
    context = BusinessContext(
        # User context
        user_id=user.id,
        user_email=user.email,
        subscription_tier=user.subscription,
        lifetime_value_cents=user.ltv,
        account_age_days=user.account_age_days,

        # Session context
        session_id=session.id,
        conversation_turn=session.turn_number,
        total_tokens_this_session=session.total_tokens,

        # Feature flags
        feature_flags=get_feature_flags(user),

        # App-specific context
        workflow_type=workflow_type,
        priority="high" if user.subscription == "enterprise" else "normal",
        app_version="1.0.0",

        # Custom business logic
        custom={
            "is_vip": user.ltv > 100000,
            "conversation_length": len(session.messages),
            "time_of_day": datetime.now().hour
        }
    )

    # Enrich the current span with all this context
    # This happens BEFORE the LLM call, so if it fails, you'll know:
    # - Who the user was (and if they're VIP!)
    # - What feature flags they had
    # - How many tokens they'd used
    # - What workflow type
    # - etc.
    enrich_current_span(context)

    # Add user's message to session
    session.add_message("user", message)

    # Make the LLM call (Traceloop auto-instruments this)
    response = client.chat.completions.create(
        model="gpt-4" if context.feature_flags.get("gpt4_access") else "gpt-3.5-turbo",
        messages=session.messages,
        temperature=0.7,
        max_tokens=500
    )

    # Extract response
    assistant_message = response.choices[0].message.content
    session.add_message("assistant", assistant_message)

    # Update session totals
    session.total_tokens += response.usage.total_tokens

    return assistant_message


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # Simulate a user
    user = User(
        user_id="user_789",
        email="jane@example.com",
        subscription="enterprise",  # VIP!
        created_at=datetime(2023, 6, 1, tzinfo=timezone.utc),  # ~1.5 years ago
        ltv=150000  # $1500 LTV - very important customer!
    )

    # Create a chat session
    session = ChatSession(session_id="sess_xyz123")

    print("🤖 Chatbot with Wide Events Demo")
    print("=" * 60)
    print(f"User: {user.email} ({user.subscription})")
    print(f"LTV: ${user.ltv / 100:.2f}")
    print(f"Account age: {user.account_age_days} days")
    print("=" * 60)
    print()

    # Message 1
    print("User: How do I reset my password?")
    response = process_chat_message(
        user=user,
        session=session,
        message="How do I reset my password?",
        workflow_type="customer_support"
    )
    print(f"Assistant: {response}\n")

    # Message 2
    print("User: Thanks! One more question - can I export my data?")
    response = process_chat_message(
        user=user,
        session=session,
        message="Thanks! One more question - can I export my data?",
        workflow_type="customer_support"
    )
    print(f"Assistant: {response}\n")

    print("=" * 60)
    print("✅ Conversation complete!")
    print()
    print("📊 Check your monitoring dashboard:")
    print("   http://localhost:5173/monitoring")
    print()
    print("   Look for these attributes in the Details tab:")
    print("   - user.id = 'user_789'")
    print("   - user.subscription_tier = 'enterprise'")
    print("   - user.lifetime_value_cents = 150000")
    print("   - feature_flags.gpt4_access = True")
    print("   - feature_flags.priority_support = True")
    print("   - session.conversation_turn = 1, 2")
    print("   - app.priority = 'high'")
    print("   - custom.is_vip = True")
    print()
    print("Now you can query:")
    print('   "Show me errors for enterprise users"')
    print('   "Find slow requests for VIP customers"')
    print('   "What\'s the error rate for users with gpt4_access?"')
    print("=" * 60)