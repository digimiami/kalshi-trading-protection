#!/usr/bin/env python3
"""
Marketing Automation for Dropshipping
Email campaigns, social media, abandoned cart recovery
"""
import os
import json
import time
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, List
from dropshipping_core import WooCommerceDropshipping

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('marketing_automation')

class EmailMarketing:
    """Email campaign automation"""
    
    def __init__(self, wc_client: WooCommerceDropshipping):
        self.wc = wc_client
        self.mailchimp_api_key = os.getenv('MAILCHIMP_API_KEY')
        self.klaviyo_api_key = os.getenv('KLAVIYO_API_KEY')
        
    def get_customers(self, days: int = 30) -> List[dict]:
        """Get recent customers for email campaigns"""
        orders = self.wc.get_orders()
        customers = {}
        
        for order in orders:
            email = order['billing']['email']
            if email not in customers:
                customers[email] = {
                    'email': email,
                    'name': f"{order['billing']['first_name']} {order['billing']['last_name']}",
                    'orders': [],
                    'total_spent': 0
                }
            
            customers[email]['orders'].append(order['id'])
            customers[email]['total_spent'] += float(order.get('total', 0))
        
        return list(customers.values())
    
    def abandoned_cart_recovery(self):
        """Send abandoned cart recovery emails"""
        logger.info("Checking for abandoned carts...")
        
        # Get pending orders (abandoned carts)
        orders = self.wc.get_orders(status='pending')
        
        for order in orders:
            created = datetime.fromisoformat(order['date_created'].replace('Z', '+00:00'))
            hours_pending = (datetime.now(created.tzinfo) - created).total_seconds() / 3600
            
            if 1 < hours_pending < 24:
                # Send first recovery email
                self._send_recovery_email(order, sequence=1)
            elif 24 < hours_pending < 48:
                # Send second recovery email
                self._send_recovery_email(order, sequence=2)
            elif hours_pending > 72:
                # Final attempt with discount
                self._send_recovery_email(order, sequence=3, discount='10%')
    
    def _send_recovery_email(self, order: dict, sequence: int, discount: str = None):
        """Send recovery email (placeholder for actual email service)"""
        email = order['billing']['email']
        name = order['billing']['first_name']
        total = order['total']
        
        templates = {
            1: f"Hi {name}, you left items in your cart! Complete your order of ${total}.",
            2: f"Hey {name}, your cart is waiting! ${total} worth of items.",
            3: f"Last chance {name}! Your cart expires soon. Use code SAVE10 for 10% off!"
        }
        
        subject = f"Your cart is waiting 💎 (${total})"
        body = templates.get(sequence, templates[1])
        
        logger.info(f"📧 Recovery email to {email} (Sequence {sequence})")
        # Actual implementation would use Mailchimp/Klaviyo API
    
    def welcome_series(self, new_customer_email: str):
        """Send welcome email series"""
        series = [
            {
                'delay_hours': 0,
                'subject': 'Welcome to Shopzario! 🎉',
                'body': 'Thanks for joining! Here\'s 15% off your first order: WELCOME15'
            },
            {
                'delay_hours': 24,
                'subject': 'Discover our bestsellers ⭐',
                'body': 'Check out what other customers love most...'
            },
            {
                'delay_hours': 72,
                'subject': 'Your exclusive offer expires soon ⏰',
                'body': 'Don\'t miss out! Use WELCOME15 before it expires.'
            }
        ]
        
        for email in series:
            logger.info(f"📧 Scheduled: {email['subject']} (in {email['delay_hours']}h)")
    
    def post_purchase_followup(self, order_id: int):
        """Post-purchase email sequence"""
        order = self.wc._request('GET', f'orders/{order_id}')
        email = order['billing']['email']
        
        sequence = [
            {'delay_days': 0, 'subject': 'Order confirmed! 🎉', 'type': 'confirmation'},
            {'delay_days': 1, 'subject': 'Your order is on the way! 🚚', 'type': 'shipping'},
            {'delay_days': 7, 'subject': 'How do you like your purchase? ⭐', 'type': 'review'},
            {'delay_days': 14, 'subject': 'Complete the look 👀', 'type': 'cross_sell'},
            {'delay_days': 30, 'subject': 'We miss you! Come back 💝', 'type': 'winback'}
        ]
        
        for email_step in sequence:
            logger.info(f"📧 Post-purchase: {email_step['subject']} (Day {email_step['delay_days']})")

class SocialMediaAutomation:
    """Social media content automation"""
    
    def __init__(self, wc_client: WooCommerceDropshipping):
        self.wc = wc_client
        
    def generate_product_post(self, product: dict) -> dict:
        """Generate social media post for product"""
        name = product['name']
        price = product['regular_price']
        images = product.get('images', [])
        
        captions = [
            f"✨ {name} - Just ${price}! Transform your everyday with this must-have. Shop now 👆",
            f"🔥 Trending now: {name}! Limited stock at ${price}. Link in bio! 💎",
            f"New arrival! {name} - ${price} ✨ Perfect addition to your collection. Tap to shop!",
        ]
        
        import random
        return {
            'caption': random.choice(captions),
            'hashtags': '#shopzario #dropshipping #onlineshopping #musthave #trending',
            'image': images[0]['src'] if images else None,
            'product_url': product.get('permalink', '')
        }
    
    def schedule_product_posts(self, posts_per_day: int = 3):
        """Schedule daily product posts"""
        products = self.wc.get_products(per_page=posts_per_day)
        
        schedule = []
        for i, product in enumerate(products):
            post = self.generate_product_post(product)
            hour = 9 + (i * 4)  # 9am, 1pm, 5pm
            
            schedule.append({
                'time': f'{hour}:00',
                'platform': ['instagram', 'facebook', 'pinterest'],
                'content': post
            })
            
            logger.info(f"📱 Scheduled post: {post['caption'][:50]}... at {hour}:00")
        
        return schedule
    
    def generate_video_script(self, product: dict) -> str:
        """Generate TikTok/Reels video script"""
        name = product['name']
        price = product['regular_price']
        
        script = f"""
TikTok Video Script: {name}

Hook (0-3s): "POV: You just found the best deal on {name}"

Problem (3-8s): Show common frustration with alternatives

Solution (8-20s): Unbox/demo the product
  - "This changes everything"
  - Show 2-3 key features
  - "And it's only ${price}!"

CTA (20-25s): "Link in bio - limited stock!"

Text overlays:
- "WAIT FOR IT..."
- "${price}?!"
- "Link in bio 🛒"
"""
        return script

class AdCampaignAutomation:
    """Automated ad campaign management"""
    
    def __init__(self, wc_client: WooCommerceDropshipping):
        self.wc = wc_client
        self.facebook_api_key = os.getenv('FACEBOOK_ADS_API_KEY')
        self.google_api_key = os.getenv('GOOGLE_ADS_API_KEY')
        
    def get_winning_products(self, min_sales: int = 5) -> List[dict]:
        """Identify winning products for ad spend"""
        products = self.wc.get_products()
        
        winners = []
        for product in products:
            meta = {m['key']: m['value'] for m in product.get('meta_data', [])}
            sales_count = int(meta.get('_sales_count', 0))
            
            if sales_count >= min_sales:
                winners.append({
                    'product': product,
                    'sales': sales_count,
                    'margin': self._calculate_margin(product)
                })
        
        return sorted(winners, key=lambda x: x['sales'], reverse=True)
    
    def _calculate_margin(self, product: dict) -> float:
        """Calculate profit margin"""
        meta = {m['key']: m['value'] for m in product.get('meta_data', [])}
        cost = float(meta.get('_cost_price', 0))
        price = float(product.get('regular_price', 0))
        
        if price > 0:
            return ((price - cost) / price) * 100
        return 0
    
    def create_facebook_ad(self, product: dict, budget: float = 10.0) -> dict:
        """Generate Facebook/Instagram ad campaign"""
        ad = {
            'campaign_name': f"{product['name']} - Prospecting",
            'objective': 'CONVERSIONS',
            'budget': budget,
            'audience': {
                'locations': ['US', 'CA', 'UK', 'AU'],
                'age_min': 25,
                'age_max': 55,
                'interests': ['Online shopping', 'Home decor', 'Gadgets']
            },
            'creative': {
                'headline': product['name'],
                'primary_text': f"✨ {product['name']} - Transform your space today! Free shipping on orders over $50.",
                'call_to_action': 'SHOP_NOW',
                'image_url': product.get('images', [{}])[0].get('src', '')
            }
        }
        
        logger.info(f"📢 Facebook Ad: {ad['campaign_name']} (${budget}/day)")
        return ad
    
    def create_google_shopping_ad(self, product: dict, budget: float = 15.0) -> dict:
        """Generate Google Shopping ad"""
        ad = {
            'campaign_name': f"Shopping - {product['name']}",
            'budget': budget,
            'target_cpa': 15.0,
            'products': [product['id']],
            'countries': ['US', 'CA']
        }
        
        logger.info(f"🔍 Google Shopping: {ad['campaign_name']} (${budget}/day)")
        return ad
    
    def auto_scale_winners(self, min_roas: float = 2.0):
        """Automatically scale winning ads"""
        winners = self.get_winning_products()
        
        for winner in winners[:5]:  # Top 5 products
            product = winner['product']
            roas = winner.get('roas', 0)
            
            if roas >= min_roas:
                logger.info(f"🚀 Scaling: {product['name']} (ROAS: {roas}x)")
                # Increase budget by 20%
                self.create_facebook_ad(product, budget=20.0)

class MarketingAutomation:
    """Main marketing automation orchestrator"""
    
    def __init__(self, wc_client: WooCommerceDropshipping):
        self.wc = wc_client
        self.email = EmailMarketing(wc_client)
        self.social = SocialMediaAutomation(wc_client)
        self.ads = AdCampaignAutomation(wc_client)
        
    def daily_automation(self):
        """Run daily marketing tasks"""
        logger.info("🚀 Running daily marketing automation")
        
        # 1. Abandoned cart recovery
        self.email.abandoned_cart_recovery()
        
        # 2. Schedule social posts
        self.social.schedule_product_posts(posts_per_day=3)
        
        # 3. Auto-scale winning ads
        self.ads.auto_scale_winners()
        
        logger.info("✅ Daily marketing automation complete")
    
    def weekly_report(self):
        """Generate weekly marketing report"""
        customers = self.email.get_customers(days=7)
        winners = self.ads.get_winning_products()
        
        report = {
            'new_customers': len(customers),
            'winning_products': len(winners),
            'recommended_action': 'Scale top 3 products'
        }
        
        logger.info(f"📊 Weekly Report: {report}")
        return report

def main():
    """Run marketing automation"""
    from dropshipping_core import WooCommerceDropshipping
    
    wc = WooCommerceDropshipping(
        'https://shopzario.com',
        'ck_4ccb7bf7646bbdaf1cf93fe46de4e7b433183a6f',
        'cs_906249467eb29a94824634c31d3039d9754c871e'
    )
    
    automation = MarketingAutomation(wc)
    automation.daily_automation()

if __name__ == '__main__':
    main()
