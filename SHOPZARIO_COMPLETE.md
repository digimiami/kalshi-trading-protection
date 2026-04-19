# Shopzario - Complete Automated Dropshipping System

## 🚀 SYSTEM OVERVIEW

Fully automated dropshipping store with multi-supplier imports, marketing automation, and Elementor theme design.

**Store:** https://shopzario.com  
**Admin:** https://shopzario.com/wp-admin  
**User:** openclaw

---

## 📦 AUTOMATION SCRIPTS

### 1. Master Automation (`master_automation.py`)
**Central controller for all automation**

```bash
# Run full automation (runs forever)
python3 master_automation.py run

# Manual commands
python3 master_automation.py import --keyword "wireless earbuds" --count 20
python3 master_automation.py fulfill
python3 master_automation.py market
python3 master_automation.py status
```

**Automated Schedule:**
| Task | Frequency |
|------|-----------|
| Import trending products | 2x daily (6am, 6pm) |
| Inventory sync | Every 2 hours |
| Order fulfillment | Every 15 minutes |
| Marketing automation | Daily 9am |
| Abandoned cart recovery | Every hour |
| Tracking updates | Every 4 hours |
| Weekly report | Mondays 8am |

---

### 2. Multi-Supplier Import (`multi_supplier_import.py`)
**Import products from multiple suppliers automatically**

```bash
# Import by keyword from all suppliers
python3 multi_supplier_import.py
```

**Supported Suppliers:**
- ✅ AliExpress (50% markup)
- ✅ Spocket (45% markup) - US/EU suppliers
- ✅ CJ Dropshipping (55% markup)

**Features:**
- Auto-import by keyword
- Supplier-specific pricing rules
- Image downloading
- Stock synchronization
- Category mapping

---

### 3. Order Fulfillment (`order_fulfillment.py`)
**Auto-process and forward orders to suppliers**

```bash
# Process pending orders
python3 order_fulfillment.py
```

**Features:**
- Auto-forward to suppliers
- Tracking number updates
- Customer notifications
- Order status synchronization

---

### 4. Marketing Automation (`marketing_automation.py`)
**Complete marketing automation suite**

```bash
# Run daily marketing tasks
python3 marketing_automation.py
```

**Features:**

#### Email Marketing
- ✅ Abandoned cart recovery (3-email sequence)
- ✅ Welcome series (3 emails)
- ✅ Post-purchase follow-up (5 emails)
- ✅ Win-back campaigns

#### Social Media
- ✅ Auto-generate product posts
- ✅ Schedule daily content
- ✅ TikTok/Reels video scripts
- ✅ Hashtag generation

#### Ad Campaigns
- ✅ Facebook/Instagram ads
- ✅ Google Shopping ads
- ✅ Auto-scale winning products
- ✅ ROAS tracking

---

### 5. Elementor Designer (`elementor_designer.py`)
**Professional theme design system**

```bash
# Generate theme kit
python3 elementor_designer.py
```

**Generated Templates:**
- ✅ Header (sticky, announcement bar)
- ✅ Footer (4 columns, newsletter)
- ✅ Homepage (7 sections)
- ✅ Product page (6 sections)
- ✅ Category page (grid layout)
- ✅ Cart page (2-column)
- ✅ Checkout page (optimized)

**Design System:**
- Colors: Coral (#FF6B6B), Teal (#4ECDC4), Yellow (#FFE66D)
- Fonts: Poppins (headings), Inter (body)
- Mobile-first responsive

---

## 🎯 QUICK START

### Step 1: Install WordPress Plugins
Login: https://shopzario.com/wp-admin

**Required:**
1. Elementor (page builder)
2. Elementor Pro (recommended)
3. WooCommerce (✅ installed)

**Recommended:**
- Yoast SEO
- WPForms
- Tidio Chat
- Mailchimp for WooCommerce

### Step 2: Configure Elementor Theme

1. Go to **Elementor → Tools → Import/Export Kit**
2. Import `/tmp/shopzario_elementor_kit.json`
3. Set global colors and fonts
4. Customize homepage sections

### Step 3: Set Up Payment Gateways

**WooCommerce → Settings → Payments:**
- Stripe (credit cards)
- PayPal (international)
- Cash on Delivery (optional)

### Step 4: Configure Shipping

**WooCommerce → Settings → Shipping:**
- Free shipping over $50
- Flat rate: $5 standard
- Express: $15 (2-3 days)

### Step 5: Start Automation

```bash
cd /root/.openclaw/workspace/skills/woocommerce-dropshipping/scripts

# Option A: Run full automation (background)
python3 master_automation.py run

# Option B: Run specific tasks
python3 multi_supplier_import.py              # Import products
python3 order_fulfillment.py                  # Process orders
python3 marketing_automation.py               # Run marketing
```

---

## 📦 SUPPLIER SETUP

### AliExpress API
1. Register: https://portals.aliexpress.com
2. Get API key and tracking ID
3. Add to environment:
```bash
export ALIEXPRESS_API_KEY="your_key"
export ALIEXPRESS_TRACKING_ID="your_tracking"
```

### Spocket API
1. Register: https://www.spocket.co
2. Get API key from dashboard
3. Add to environment:
```bash
export SPOCKET_API_KEY="your_key"
```

### CJ Dropshipping API
1. Register: https://cjdropshipping.com
2. Get API key
3. Add to environment:
```bash
export CJ_API_KEY="your_key"
```

---

## 📧 EMAIL MARKETING SETUP

### Mailchimp
1. Register: https://mailchimp.com
2. Get API key
3. Add to environment:
```bash
export MAILCHIMP_API_KEY="your_key"
```

### Klaviyo (Recommended)
1. Register: https://www.klaviyo.com
2. Get API key
3. Add to environment:
```bash
export KLAVIYO_API_KEY="your_key"
```

---

## 📱 SOCIAL MEDIA SETUP

### Facebook/Instagram Ads
1. Create Business Manager: https://business.facebook.com
2. Get API key
3. Add to environment:
```bash
export FACEBOOK_ADS_API_KEY="your_key"
```

### Google Ads
1. Create account: https://ads.google.com
2. Get API key
3. Add to environment:
```bash
export GOOGLE_ADS_API_KEY="your_key"
```

---

## 💰 PRICING STRATEGY

| Supplier | Markup | Example Cost | Selling Price |
|----------|--------|--------------|---------------|
| AliExpress | 50% | $10.00 | $15.00 |
| Spocket | 45% | $20.00 | $29.00 |
| CJ Dropshipping | 55% | $8.00 | $12.40 |

**Auto-pricing rules:**
- Round to .99 or .97
- Minimum profit: $5
- Competitive price checking (future)

---

## 📊 MONITORING

### Check Logs
```bash
tail -f /tmp/shopzario_master.log
tail -f /tmp/dropshipping.log
```

### Check Status
```bash
python3 master_automation.py status
```

### Store Metrics
- Products: Check WooCommerce → Products
- Orders: Check WooCommerce → Orders
- Revenue: Check WooCommerce → Reports

---

## 🛠️ TROUBLESHOOTING

### API Connection Failed
1. Check API credentials in `.env.shopzario`
2. Verify WooCommerce REST API is enabled
3. Check SSL certificate on shopzario.com

### Products Not Importing
1. Check supplier API keys
2. Verify rate limits
3. Check `/tmp/dropshipping.log`

### Orders Not Processing
1. Check order status (must be 'processing')
2. Verify supplier connections
3. Check tracking number updates

---

## 📈 GROWTH STRATEGY

### Phase 1: Launch (Week 1-2)
- [ ] Import 50-100 products
- [ ] Set up payment gateways
- [ ] Configure shipping
- [ ] Launch with $10-20/day ads

### Phase 2: Optimize (Week 3-4)
- [ ] Identify winning products
- [ ] Scale winning ads
- [ ] Add email automation
- [ ] Optimize conversions

### Phase 3: Scale (Month 2+)
- [ ] Increase ad spend
- [ ] Add new product categories
- [ ] Implement upsells
- [ ] Build email list

---

## 📞 SUPPORT

**Scripts Location:**
`/root/.openclaw/workspace/skills/woocommerce-dropshipping/scripts/`

**Credentials:**
`/root/.openclaw/workspace/.env.shopzario`

**Documentation:**
`/root/.openclaw/workspace/SHOPZARIO_COMPLETE.md`

---

**Created:** 2026-03-13  
**Status:** ✅ Automation Ready  
**Next:** Complete WordPress setup + Start automation
