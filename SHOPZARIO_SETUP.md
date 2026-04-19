# Shopzario - Fully Automated Dropshipping Store

## Store Details
- **URL**: https://shopzario.com
- **Admin**: https://shopzario.com/wp-admin
- **Username**: openclaw
- **Email**: openclaw@shopzario.com

## Automation System Created

### Core Scripts
| Script | Purpose |
|--------|---------|
| `dropshipping_core.py` | Core automation engine |
| `bulk_import.py` | Bulk product import (CSV/JSON) |
| `order_fulfillment.py` | Auto-forward orders to suppliers |
| `setup_shopzario.py` | Store setup wizard |

### Automation Features
✅ **Product Import** - Bulk import from CSV/JSON with auto markup  
✅ **Inventory Sync** - Real-time stock level updates  
✅ **Order Fulfillment** - Auto-forward orders to suppliers  
✅ **Price Management** - Dynamic markup rules (default 40%)  
✅ **Tracking Sync** - Automatic tracking number updates  

## What You Need To Do Now

### Step 1: Complete WordPress Setup
Login: https://shopzario.com/wp-admin  
User: openclaw

### Step 2: Install Essential Plugins
Go to Plugins → Add New:
- **Elementor** - Page builder
- **Yoast SEO** - SEO optimization
- **WPForms** - Contact forms
- **Tidio Chat** - Live chat
- **Mailchimp** - Email marketing

### Step 3: Configure Payment Gateways
WooCommerce → Settings → Payments:
- Connect **Stripe** (credit cards)
- Connect **PayPal** (international)
- Enable **Cash on Delivery** (optional)

### Step 4: Set Up Shipping
WooCommerce → Settings → Shipping:
- Free shipping over $50
- Flat rate $5 standard
- Express $15 (2-3 days)

### Step 5: Choose Theme
Appearance → Themes:
- **Astra** (fast, lightweight)
- **Flatsome** (e-commerce focused)

### Step 6: Import Products

#### Option A: Bulk Import
Create `products.csv`:
```csv
title,description,price,category,images,supplier_id,supplier_url
Wireless Earbuds,High-quality wireless earbuds,15.99,Electronics,https://image1.jpg|https://image2.jpg,AE123,https://aliexpress.com/item/123
```

Run:
```bash
cd /root/.openclaw/workspace/skills/woocommerce-dropshipping/scripts
python3 bulk_import.py products.csv --markup 40
```

#### Option B: Manual Import
Use WooCommerce → Products → Add New

### Step 7: Create Legal Pages
Pages → Add New:
- Privacy Policy
- Terms of Service
- Refund Policy
- Shipping Policy

### Step 8: Test Everything
1. Place test order
2. Check payment processing
3. Verify email notifications
4. Confirm order forwarding

## Running Automation

### Start Full Automation
```bash
cd /root/.openclaw/workspace/skills/woocommerce-dropshipping/scripts
python3 dropshipping_core.py
```

This runs:
- Inventory sync every 30 min
- Order processing every 5 min
- Price updates daily

### Process Orders Manually
```bash
python3 order_fulfillment.py
```

## Supplier Integration

### Supported Suppliers (To Be Configured)
1. **AliExpress** - Need API key
2. **Spocket** - Need API key
3. **CJ Dropshipping** - Need API key
4. **Modalyst** - Need API key

### To Add Supplier API:
Edit `dropshipping_core.py` and add API credentials

## Marketing Setup

### Recommended
- Google Ads ($10-20/day to start)
- Facebook/Instagram Ads
- TikTok organic content
- Pinterest product pins

### Email Flows
- Welcome series (3 emails)
- Abandoned cart recovery
- Post-purchase follow-up
- Re-engagement campaign

## Monthly Costs

| Item | Cost |
|------|------|
| WordPress Hosting | $10-30/month |
| Elementor Pro | $49/year |
| Email Marketing | $0-20/month |
| Domain | $12/year |
| **Total** | **~$30-60/month** |

## Support

Automation scripts located at:
`/root/.openclaw/workspace/skills/woocommerce-dropshipping/scripts/`

API Credentials stored securely in:
`/root/.openclaw/workspace/.env.shopzario`

---
Created: 2026-03-13  
Status: ⚠️ Setup Required (Manual steps pending)
