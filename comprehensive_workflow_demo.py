"""
Comprehensive Multi-Node Workflow Demo
========================================

This example demonstrates a realistic workflow with:
- 5+ nodes with different responsibilities
- Conditional routing based on data
- Error handling with fallback nodes
- LLM integration (optional - works without OpenAI key)
- Rich telemetry with node names and timing

Run this to see a complete workflow in your dashboard!
"""

import asyncio
import os
from agora.agora_tracer import init_agora, TracedAsyncNode, TracedAsyncFlow

# Initialize telemetry
init_agora(
    app_name="E-Commerce Order Processor",
    export_to_console=False,  # Set to True to see console output
    enable_cloud_upload=True,
    project_name="E-Commerce Demo"
)

# =============================================================================
# NODE 1: Validate Order Data
# =============================================================================

class ValidateOrderNode(TracedAsyncNode):
    """Validates incoming order data"""
    
    def __init__(self):
        super().__init__("Validate Order", max_retries=1)
        self.code = """
async def validate_order(order_data):
    required_fields = ['customer_id', 'items', 'total']
    for field in required_fields:
        if field not in order_data:
            raise ValueError(f'Missing required field: {field}')
    return order_data
"""
    
    async def prep_async(self, shared):
        # First node gets the raw shared data (which is the order)
        return shared
    
    async def exec_async(self, prep_res):
        order = prep_res
        
        # Validate required fields
        required = ['customer_id', 'items', 'total']
        for field in required:
            if field not in order:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate total is positive
        if order['total'] <= 0:
            raise ValueError("Order total must be positive")
        
        # Validate items list
        if not order['items'] or len(order['items']) == 0:
            raise ValueError("Order must contain at least one item")
        
        print(f"✅ Order validated: {order['customer_id']}, ${order['total']}")
        return order
    
    async def post_async(self, shared, prep_res, exec_res):
        shared['validated_order'] = exec_res
        # Route based on order total
        if exec_res['total'] > 1000:
            return "high_value"
        else:
            return "standard"

# =============================================================================
# NODE 2: Check Inventory
# =============================================================================

class CheckInventoryNode(TracedAsyncNode):
    """Checks if items are in stock"""
    
    def __init__(self):
        super().__init__("Check Inventory", max_retries=2, wait=1)
        self.code = """
async def check_inventory(items):
    # Simulate inventory check
    inventory = {'SKU001': 100, 'SKU002': 50, 'SKU003': 0}
    in_stock = all(inventory.get(item['sku'], 0) >= item['quantity'] for item in items)
    return in_stock
"""
    
    async def prep_async(self, shared):
        # Get validated order from shared state
        return shared.get('validated_order', shared)
    
    async def exec_async(self, prep_res):
        order = prep_res
        
        # Simulate inventory database
        inventory = {
            'SKU001': 100,
            'SKU002': 50,
            'SKU003': 0,  # Out of stock
            'SKU004': 25
        }
        
        # Check each item
        all_in_stock = True
        out_of_stock_items = []
        
        for item in order['items']:
            sku = item['sku']
            quantity = item['quantity']
            available = inventory.get(sku, 0)
            
            if available < quantity:
                all_in_stock = False
                out_of_stock_items.append(sku)
        
        if all_in_stock:
            print(f"✅ All items in stock for order {order['customer_id']}")
        else:
            print(f"⚠️  Items out of stock: {out_of_stock_items}")
        
        return {
            'in_stock': all_in_stock,
            'out_of_stock_items': out_of_stock_items
        }
    
    async def post_async(self, shared, prep_res, exec_res):
        shared['inventory_check'] = exec_res
        if exec_res['in_stock']:
            return "process_payment"
        else:
            return "notify_backorder"

# =============================================================================
# NODE 3: Process Payment
# =============================================================================

class ProcessPaymentNode(TracedAsyncNode):
    """Processes payment for the order"""
    
    def __init__(self):
        super().__init__("Process Payment", max_retries=3, wait=2)
        self.code = """
async def process_payment(order, payment_method='credit_card'):
    # Simulate payment processing
    import random
    success = random.random() > 0.1  # 90% success rate
    if success:
        return {'status': 'paid', 'transaction_id': 'TXN' + str(random.randint(10000, 99999))}
    else:
        raise Exception('Payment gateway timeout')
"""
    
    async def prep_async(self, shared):
        # Get validated order from shared state
        return shared.get('validated_order', shared)
    
    async def exec_async(self, prep_res):
        order = prep_res
        
        # Simulate payment processing
        import random
        await asyncio.sleep(0.5)  # Simulate API call
        
        # 90% success rate
        if random.random() > 0.1:
            transaction_id = f"TXN{random.randint(10000, 99999)}"
            print(f"💳 Payment processed: {transaction_id} for ${order['total']}")
            return {
                'status': 'paid',
                'transaction_id': transaction_id,
                'amount': order['total']
            }
        else:
            raise Exception("Payment gateway timeout")
    
    async def post_async(self, shared, prep_res, exec_res):
        shared['payment'] = exec_res
        return "ship_order"
    
    async def exec_fallback_async(self, prep_res, error):
        print(f"❌ Payment failed after retries: {error}")
        return {
            'status': 'failed',
            'error': str(error)
        }

# =============================================================================
# NODE 4: Ship Order
# =============================================================================

class ShipOrderNode(TracedAsyncNode):
    """Creates shipping label and schedules pickup"""
    
    def __init__(self):
        super().__init__("Ship Order")
        self.code = """
async def ship_order(order, payment):
    # Generate shipping label
    import random
    tracking_number = 'TRACK' + str(random.randint(100000, 999999))
    carrier = random.choice(['UPS', 'FedEx', 'USPS'])
    return {'tracking': tracking_number, 'carrier': carrier}
"""
    
    async def prep_async(self, shared):
        # Get validated order from shared state
        return shared.get('validated_order', shared)
    
    async def exec_async(self, prep_res):
        order = prep_res
        
        # Generate shipping label
        import random
        tracking = f"TRACK{random.randint(100000, 999999)}"
        carrier = random.choice(['UPS', 'FedEx', 'USPS'])
        
        print(f"📦 Shipping label created: {tracking} via {carrier}")
        
        return {
            'tracking_number': tracking,
            'carrier': carrier,
            'estimated_delivery': '3-5 business days'
        }
    
    async def post_async(self, shared, prep_res, exec_res):
        shared['shipping'] = exec_res
        return "send_confirmation"

# =============================================================================
# NODE 5: Send Confirmation Email
# =============================================================================

class SendConfirmationNode(TracedAsyncNode):
    """Sends order confirmation email to customer"""
    
    def __init__(self):
        super().__init__("Send Confirmation")
        self.code = """
async def send_confirmation(customer_id, order, payment, shipping):
    # Send email via SendGrid/SES
    email_body = f'''
    Order Confirmation
    Customer: {customer_id}
    Total: ${order['total']}
    Tracking: {shipping['tracking_number']}
    '''
    return {'email_sent': True}
"""
    
    async def prep_async(self, shared):
        # Get validated order from shared state
        return shared.get('validated_order', shared)
    
    async def exec_async(self, prep_res):
        order = prep_res
        customer_id = order['customer_id']
        
        # Simulate sending email
        await asyncio.sleep(0.3)
        
        print(f"📧 Confirmation email sent to customer {customer_id}")
        
        return {
            'email_sent': True,
            'recipient': customer_id,
            'timestamp': asyncio.get_event_loop().time()
        }
    
    async def post_async(self, shared, prep_res, exec_res):
        shared['confirmation'] = exec_res
        return "complete"

# =============================================================================
# NODE 6: Handle Backorder
# =============================================================================

class HandleBackorderNode(TracedAsyncNode):
    """Handles out-of-stock items"""
    
    def __init__(self):
        super().__init__("Handle Backorder")
        self.code = """
async def handle_backorder(order, out_of_stock_items):
    # Create backorder record
    # Notify customer about delay
    return {'backorder_created': True, 'estimated_restock': '2-3 weeks'}
"""
    
    async def prep_async(self, shared):
        # Get validated order and inventory check from shared state
        order = shared.get('validated_order', shared)
        inventory_check = shared.get('inventory_check', {})
        order['out_of_stock_items'] = inventory_check.get('out_of_stock_items', [])
        return order
    
    async def exec_async(self, prep_res):
        order = prep_res
        out_of_stock = order.get('out_of_stock_items', [])
        
        print(f"📋 Backorder created for items: {out_of_stock}")
        
        return {
            'backorder_created': True,
            'items': out_of_stock,
            'estimated_restock': '2-3 weeks'
        }
    
    async def post_async(self, shared, prep_res, exec_res):
        shared['backorder'] = exec_res
        return "notify_customer"

# =============================================================================
# NODE 7: Notify Customer (Backorder)
# =============================================================================

class NotifyBackorderNode(TracedAsyncNode):
    """Notifies customer about backorder"""
    
    def __init__(self):
        super().__init__("Notify Backorder")
    
    async def prep_async(self, shared):
        # Get validated order from shared state
        return shared.get('validated_order', shared)
    
    async def exec_async(self, prep_res):
        order = prep_res
        
        print(f"📧 Backorder notification sent to customer {order['customer_id']}")
        
        return {
            'notification_sent': True,
            'type': 'backorder'
        }
    
    async def post_async(self, shared, prep_res, exec_res):
        shared['notification'] = exec_res
        return "complete"

# =============================================================================
# WORKFLOW: Order Processing Flow
# =============================================================================

class OrderProcessingFlow(TracedAsyncFlow):
    """Complete order processing workflow"""
    
    def __init__(self):
        # Initialize nodes first
        self.validate = ValidateOrderNode()
        self.check_inventory = CheckInventoryNode()
        self.process_payment = ProcessPaymentNode()
        self.ship_order = ShipOrderNode()
        self.send_confirmation = SendConfirmationNode()
        self.handle_backorder = HandleBackorderNode()
        self.notify_backorder = NotifyBackorderNode()
        
        # Set up routing using successors
        # Validate routes to inventory check (both high_value and standard go to same node)
        self.validate.successors = {
            "high_value": self.check_inventory,
            "standard": self.check_inventory
        }
        
        # Inventory check routes to either payment or backorder
        self.check_inventory.successors = {
            "process_payment": self.process_payment,
            "notify_backorder": self.handle_backorder
        }
        
        # Payment routes to shipping
        self.process_payment.successors = {
            "ship_order": self.ship_order
        }
        
        # Shipping routes to confirmation
        self.ship_order.successors = {
            "send_confirmation": self.send_confirmation
        }
        
        # Backorder routes to notification
        self.handle_backorder.successors = {
            "notify_customer": self.notify_backorder
        }
        
        # Initialize flow with validate as start node
        super().__init__("Order Processing Workflow", start=self.validate)
    
    def to_dict(self):
        """Export workflow graph for visualization"""
        return {
            "nodes": [
                {"name": "Validate Order", "code": self.validate.code},
                {"name": "Check Inventory", "code": self.check_inventory.code},
                {"name": "Process Payment", "code": self.process_payment.code},
                {"name": "Ship Order", "code": self.ship_order.code},
                {"name": "Send Confirmation", "code": self.send_confirmation.code},
                {"name": "Handle Backorder", "code": self.handle_backorder.code},
                {"name": "Notify Backorder", "code": self.notify_backorder.code}
            ],
            "edges": [
                {"from": "Validate Order", "to": "Check Inventory", "action": "high_value"},
                {"from": "Validate Order", "to": "Check Inventory", "action": "standard"},
                {"from": "Check Inventory", "to": "Process Payment", "action": "process_payment"},
                {"from": "Check Inventory", "to": "Handle Backorder", "action": "notify_backorder"},
                {"from": "Process Payment", "to": "Ship Order", "action": "ship_order"},
                {"from": "Ship Order", "to": "Send Confirmation", "action": "send_confirmation"},
                {"from": "Handle Backorder", "to": "Notify Backorder", "action": "notify_customer"}
            ]
        }

# =============================================================================
# MAIN: Run the workflow
# =============================================================================

async def main():
    print("=" * 60)
    print("🚀 Starting E-Commerce Order Processing Workflow")
    print("=" * 60)
    
    # Create workflow
    flow = OrderProcessingFlow()
    
    # Test Case 1: Standard order with all items in stock
    print("\n📦 Test Case 1: Standard Order (In Stock)")
    print("-" * 60)
    order1 = {
        'customer_id': 'CUST001',
        'items': [
            {'sku': 'SKU001', 'name': 'Widget', 'quantity': 2, 'price': 25.00},
            {'sku': 'SKU002', 'name': 'Gadget', 'quantity': 1, 'price': 50.00}
        ],
        'total': 100.00
    }
    
    result1 = await flow.run_async(order1)
    print(f"\n✅ Order 1 completed: {result1}")
    
    # Test Case 2: High-value order
    print("\n\n💎 Test Case 2: High-Value Order")
    print("-" * 60)
    order2 = {
        'customer_id': 'CUST002',
        'items': [
            {'sku': 'SKU001', 'name': 'Premium Widget', 'quantity': 10, 'price': 150.00}
        ],
        'total': 1500.00
    }
    
    result2 = await flow.run_async(order2)
    print(f"\n✅ Order 2 completed: {result2}")
    
    # Test Case 3: Order with out-of-stock items
    print("\n\n⚠️  Test Case 3: Backorder (Out of Stock)")
    print("-" * 60)
    order3 = {
        'customer_id': 'CUST003',
        'items': [
            {'sku': 'SKU003', 'name': 'Rare Item', 'quantity': 1, 'price': 75.00}
        ],
        'total': 75.00
    }
    
    result3 = await flow.run_async(order3)
    print(f"\n✅ Order 3 completed: {result3}")
    
    print("\n" + "=" * 60)
    print("✅ All workflows completed!")
    print("=" * 60)
    print("\n📊 Check your dashboard at: http://localhost:5173/monitoring")
    print("   You should see 3 workflow executions with detailed node telemetry!")

if __name__ == "__main__":
    asyncio.run(main())
