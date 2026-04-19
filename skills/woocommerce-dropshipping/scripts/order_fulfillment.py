#!/usr/bin/env python3
"""
Order Fulfillment Automation
Auto-process orders and forward to suppliers
"""
import json
import time
import logging
from datetime import datetime
from dropshipping_core import WooCommerceDropshipping

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('order_fulfillment')

class OrderFulfillment:
    def __init__(self, store_url: str, consumer_key: str, consumer_secret: str):
        self.wc = WooCommerceDropshipping(store_url, consumer_key, consumer_secret)
        
    def get_pending_orders(self) -> list:
        """Get orders waiting for fulfillment"""
        return self.wc.get_orders(status='processing')
    
    def analyze_order(self, order: dict) -> dict:
        """Analyze order items and identify suppliers"""
        order_data = {
            'order_id': order['id'],
            'customer': {
                'name': f"{order['billing']['first_name']} {order['billing']['last_name']}",
                'email': order['billing']['email'],
                'address': order['billing']['address_1'],
                'city': order['billing']['city'],
                'country': order['billing']['country'],
                'phone': order['billing']['phone']
            },
            'items': [],
            'suppliers': set()
        }
        
        for item in order['line_items']:
            product_id = item['product_id']
            product = self.wc._request('GET', f'products/{product_id}')
            
            # Extract supplier info from meta
            meta = {m['key']: m['value'] for m in product.get('meta_data', [])}
            
            item_data = {
                'name': item['name'],
                'quantity': item['quantity'],
                'price': item['price'],
                'supplier_id': meta.get('_supplier_id', ''),
                'supplier_url': meta.get('_supplier_url', ''),
                'is_dropshipping': meta.get('_is_dropshipping') == 'yes'
            }
            
            order_data['items'].append(item_data)
            
            if item_data['is_dropshipping']:
                order_data['suppliers'].add(meta.get('_supplier_id', 'unknown'))
        
        return order_data
    
    def forward_to_supplier(self, order_data: dict) -> bool:
        """Forward order to supplier (placeholder for actual API)"""
        logger.info(f"Forwarding order #{order_data['order_id']} to suppliers")
        
        # This would integrate with:
        # - AliExpress API
        # - Spocket API
        # - CJ Dropshipping API
        # - Other supplier APIs
        
        for item in order_data['items']:
            if item['is_dropshipping']:
                logger.info(f"  - {item['name']} x{item['quantity']} -> {item['supplier_id']}")
        
        return True
    
    def update_order_status(self, order_id: int, tracking_number: str = None):
        """Update order with fulfillment info"""
        meta_data = [
            {'key': '_forwarded_to_supplier', 'value': 'yes'},
            {'key': '_forwarded_at', 'value': datetime.now().isoformat()}
        ]
        
        if tracking_number:
            meta_data.append({'key': '_supplier_tracking', 'value': tracking_number})
        
        self.wc.update_order(order_id, {
            'status': 'completed',
            'meta_data': meta_data
        })
        
        logger.info(f"✅ Order #{order_id} marked as fulfilled")
    
    def run_fulfillment(self):
        """Main fulfillment loop"""
        orders = self.get_pending_orders()
        logger.info(f"Found {len(orders)} orders to process")
        
        for order in orders:
            try:
                # Check if already processed
                meta = {m['key']: m['value'] for m in order.get('meta_data', [])}
                if meta.get('_forwarded_to_supplier'):
                    continue
                
                # Analyze and forward
                order_data = self.analyze_order(order)
                
                if self.forward_to_supplier(order_data):
                    self.update_order_status(order['id'])
                
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                logger.error(f"Error processing order #{order['id']}: {e}")

def main():
    fulfillment = OrderFulfillment(
        store_url="https://shopzario.com",
        consumer_key="ck_4ccb7bf7646bbdaf1cf93fe46de4e7b433183a6f",
        consumer_secret="cs_906249467eb29a94824634c31d3039d9754c871e"
    )
    
    logger.info("🚀 Starting order fulfillment automation")
    fulfillment.run_fulfillment()

if __name__ == '__main__':
    main()
