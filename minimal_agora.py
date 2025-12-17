from agora import Node, Flow

# 1. Define Nodes
class VerifyUser(Node):
    def prep(self, shared):
        # Phase 1: Prepare data from shared state
        user_id = shared.get("user_id")
        print(f"[VerifyUser] Prepping user_id: {user_id}")
        return user_id

    def exec(self, user_id):
        # Phase 2: Execute core logic
        if user_id > 0:
            return "valid"
        return "invalid"

    def post(self, shared, prep_res, exec_res):
        # Phase 3: Update shared state and decide route
        print(f"[VerifyUser] Result: {exec_res}")
        return exec_res  # "valid" or "invalid"

class WelcomeUser(Node):
    def exec(self, prep_res):
        print("[WelcomeUser] sending welcome email...")
        return "sent"

class FlagError(Node):
    def exec(self, prep_res):
        print("[FlagError] logging invalid access attempt...")
        return "logged"

# 2. Build the Flow
flow = Flow("UserOnboarding")
verify = VerifyUser()
welcome = WelcomeUser()
error = FlagError()

flow.start(verify)

# 3. Connect Nodes (Conditional Routing)
verify - "valid" >> welcome
verify - "invalid" >> error

# 4. Run it
def main():
    print("--- Running Scenario 1: Valid User ---")
    shared_state = {"user_id": 123}
    flow.run(shared_state)
    
    print("\n--- Running Scenario 2: Invalid User ---")
    shared_state = {"user_id": -5}
    flow.run(shared_state)

if __name__ == "__main__":
    main()
