#!/usr/bin/env python3
"""
E-Commerce Order Processing Demo Workflow

This demonstrates a realistic e-commerce workflow with named nodes,
conditional routing, and comprehensive telemetry upload to the Agora dashboard.

Setup:
1. Ensure AGORA_API_KEY is set in your .env file
2. Run: python dashboard_demo.py
3. View results at http://localhost:5173/
"""

import asyncio
import random
from datetime import datetime

from agora.agora_tracer import (
    TracedAsyncFlow,
    init_agora,
    agora_node,
)

# Initialize Agora with the API key from environment
init_agora(
    app_name="ecommerce-platform",
    project_name="E-Commerce Order Processing",
    export_to_console=True,
    export_to_file="ecommerce_demo_traces.jsonl"
)


@agora_node(name="ValidateOrder")
async def validate_order(shared):
    """Validate incoming order data"""
    print("📋 Validating order...")
    
    # Simulate validation logic
    await asyncio.sleep(0.3)
    
    order_data = shared.get("order", {})
    
    # Check required fields
    required_fields = ["customer_id", "items", "total_amount"]
    missing_fields = [f for f in required_fields if f not in order_data]
    
    if missing_fields:
        shared["validation_error"] = f"Missing fields: {', '.join(missing_fields)}"
        print(f"  ❌ Validation failed: {shared['validation_error']}")
        return "invalid"
    
    if order_data.get("total_amount", 0) <= 0:
        shared["validation_error"] = "Invalid total amount"
        print(f"  ❌ Validation failed: {shared['validation_error']}")
        return "invalid"
    
    print("  ✅ Order validated successfully")
    return "valid"


@agora_node(name="CheckInventory")
async def check_inventory(shared):
    """Check product availability in inventory"""
    print("📦 Checking inventory...")
    
    await asyncio.sleep(0.5)
    
    items = shared["order"]["items"]
    
    # Simulate inventory check (90% success rate)
    in_stock = random.random() > 0.1
    
    if not in_stock:
        shared["inventory_status"] = "out_of_stock"
        shared["out_of_stock_items"] = [items[0]["product_id"]]
        print(f"  ⚠️  Items out of stock: {shared['out_of_stock_items']}")
        return "out_of_stock"
    
    shared["inventory_status"] = "available"
    print("  ✅ All items in stock")
    return "available"


@agora_node(name="ProcessPayment")
async def process_payment(shared):
    """Process payment for the order"""
    print("💳 Processing payment...")
    
    await asyncio.sleep(0.7)
    
    total_amount = shared["order"]["total_amount"]
    
    # Simulate payment processing (95% success rate)
    payment_success = random.random() > 0.05
    
    if not payment_success:
        shared["payment_status"] = "failed"
        shared["payment_error"] = "Payment gateway timeout"
        print(f"  ❌ Payment failed: {shared['payment_error']}")
        return "payment_failed"
    
    shared["payment_status"] = "completed"
    shared["transaction_id"] = f"TXN-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    print(f"  ✅ Payment processed: {shared['transaction_id']} (${total_amount:.2f})")
    return "payment_success"


@agora_node(name="UpdateInventory")
async def update_inventory(shared):
    """Update inventory after successful payment"""
    print("📊 Updating inventory...")
    
    await asyncio.sleep(0.4)
    
    items = shared["order"]["items"]
    
    # Simulate inventory update
    for item in items:
        print(f"  - Reduced stock for {item['product_id']} by {item['quantity']}")
    
    shared["inventory_updated"] = True
    print("  ✅ Inventory updated")
    return "continue"


@agora_node(name="SendConfirmation")
async def send_confirmation(shared):
    """Send order confirmation to customer"""
    print("📧 Sending order confirmation...")
    
    await asyncio.sleep(0.3)
    
    customer_id = shared["order"]["customer_id"]
    transaction_id = shared.get("transaction_id", "N/A")
    
    shared["confirmation_sent"] = True
    shared["confirmation_email"] = f"confirmation_{transaction_id}@example.com"
    
    print(f"  ✅ Confirmation sent to customer {customer_id}")
    print(f"  📬 Email: {shared['confirmation_email']}")
    return "complete"


@agora_node(name="HandleInvalidOrder")
async def handle_invalid_order(shared):
    """Handle invalid order scenario"""
    print("⚠️  Handling invalid order...")
    
    await asyncio.sleep(0.2)
    
    error = shared.get("validation_error", "Unknown error")
    shared["order_status"] = "rejected"
    shared["rejection_reason"] = error
    
    print(f"  ❌ Order rejected: {error}")
    return None


@agora_node(name="HandleOutOfStock")
async def handle_out_of_stock(shared):
    """Handle out of stock scenario"""
    print("📦 Handling out of stock items...")
    
    await asyncio.sleep(0.3)
    
    out_of_stock_items = shared.get("out_of_stock_items", [])
    shared["order_status"] = "pending_restock"
    shared["notification_sent"] = True
    
    print(f"  📧 Customer notified about out of stock items: {out_of_stock_items}")
    return None


@agora_node(name="HandlePaymentFailure")
async def handle_payment_failure(shared):
    """Handle payment failure scenario"""
    print("💳 Handling payment failure...")
    
    await asyncio.sleep(0.3)
    
    error = shared.get("payment_error", "Unknown error")
    shared["order_status"] = "payment_failed"
    shared["retry_available"] = True
    
    print(f"  ❌ Payment failed: {error}")
    print(f"  🔄 Customer can retry payment")
    return None


async def run_demo():
    """Run the e-commerce demo workflow"""
    
    print("=" * 70)
    print("🛒 E-COMMERCE ORDER PROCESSING DEMO")
    print("=" * 70)
    print()
    
    # Create workflow
    flow = TracedAsyncFlow("E-Commerce Order Processing")
    
    # Build the workflow graph
    flow.start(validate_order)
    
    # Validation routing
    validate_order - "valid" >> check_inventory
    validate_order - "invalid" >> handle_invalid_order
    
    # Inventory routing
    check_inventory - "available" >> process_payment
    check_inventory - "out_of_stock" >> handle_out_of_stock
    
    # Payment routing
    process_payment - "payment_success" >> update_inventory
    process_payment - "payment_failed" >> handle_payment_failure
    
    # Success path
    update_inventory - "continue" >> send_confirmation
    
    # Sample order data
    shared = {
        "order": {
            "customer_id": "CUST-12345",
            "items": [
                {"product_id": "PROD-001", "name": "Laptop", "quantity": 1, "price": 999.99},
                {"product_id": "PROD-002", "name": "Mouse", "quantity": 2, "price": 29.99}
            ],
            "total_amount": 1059.97,
            "shipping_address": "123 Main St, City, State 12345"
        }
    }
    
    print("📦 Order Details:")
    print(f"  Customer: {shared['order']['customer_id']}")
    print(f"  Items: {len(shared['order']['items'])}")
    print(f"  Total: ${shared['order']['total_amount']:.2f}")
    print()
    
    # Execute workflow
    print("🚀 Starting workflow execution...")
    print()
    
    await flow.run_async(shared)
    
    print()
    print("=" * 70)
    print("📊 WORKFLOW EXECUTION COMPLETED")
    print("=" * 70)
    print()
    
    # Print final status
    final_status = shared.get("order_status", "completed")
    print(f"Final Status: {final_status}")
    
    if shared.get("confirmation_sent"):
        print(f"✅ Order confirmed - Transaction: {shared.get('transaction_id')}")
    elif shared.get("rejection_reason"):
        print(f"❌ Order rejected - Reason: {shared.get('rejection_reason')}")
    elif shared.get("out_of_stock_items"):
        print(f"⚠️  Pending restock - Items: {shared.get('out_of_stock_items')}")
    elif shared.get("payment_error"):
        print(f"❌ Payment failed - Error: {shared.get('payment_error')}")
    
    print()
    print("=" * 70)
    print("🎯 VIEW YOUR WORKFLOW IN THE DASHBOARD")
    print("=" * 70)
    print()
    print("  1. Open: http://localhost:5173/")
    print("  2. Navigate to 'Projects'")
    print("  3. Click on 'E-Commerce Order Processing'")
    print("  4. View workflow graph and execution details")
    print()
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_demo())
