# Shopzario Elementor Design Implementation Guide

## 🎨 DESIGN SYSTEM

**Colors:**
- Primary: `#FF6B6B` (Coral Red)
- Secondary: `#4ECDC4` (Teal)
- Accent: `#FFE66D` (Yellow)
- Dark: `#2C3E50` (Navy)
- Light: `#F7F9FC` (Off-white)

**Fonts:**
- Headings: Poppins (700)
- Body: Inter (400)

---

## 🚀 IMPLEMENTATION STEPS

### Step 1: Install Required Plugins

1. **Login:** https://shopzario.com/wp-admin
2. **Plugins → Add New:**
   - ✅ Elementor (free)
   - ✅ Elementor Pro (recommended for theme builder)
   - ✅ WooCommerce (already installed)
   - ✅ Essential Addons for Elementor (optional)

### Step 2: Add Custom CSS

1. **Appearance → Customize → Additional CSS**
2. Copy all CSS from: `shopzario-custom.css`
3. Click "Publish"

### Step 3: Set Global Fonts & Colors

1. **Elementor → Settings → Global Settings**
2. **Colors:**
   - Primary: #FF6B6B
   - Secondary: #4ECDC4
   - Text: #333333
   - Accent: #FFE66D
3. **Typography:**
   - Heading Font: Poppins
   - Body Font: Inter

### Step 4: Create Homepage

1. **Pages → Add New**
2. **Title:** Home
3. **Edit with Elementor**
4. Click **"Add Template"** → **"Import"**
5. Use the sections from `elementor-homepage.html`

**OR Build Manually:**

#### Section 1: Hero
- **Structure:** Full width
- **Background:** Gradient (FF6B6B → 4ECDC4)
- **Padding:** 120px top/bottom
- **Widgets:**
  - Heading: "Discover Trending Products" (64px, white, center)
  - Text: "Premium quality at unbeatable prices..." (24px, white, center)
  - Buttons: "Shop Now" (white bg, coral text) + "New Arrivals" (border)

#### Section 2: Trust Badges
- **Background:** #F7F9FC
- **4 Columns:**
  - 🚚 Free Shipping
  - 🛡️ Secure Payment
  - ↩️ Easy Returns
  - 💬 24/7 Support

#### Section 3: Categories
- **4 Columns:**
  - Electronics (purple gradient)
  - Home & Garden (pink gradient)
  - Fashion (blue gradient)
  - Sports (green gradient)

#### Section 4: Trending Products
- **Widget:** WooCommerce Products
- **Settings:**
  - Filter: Best Selling
  - Count: 8
  - Columns: 4

#### Section 5: Features
- **Background:** #2C3E50 (dark)
- **4 Icon Boxes:**
  - ⚡ Fast Shipping
  - 💎 Premium Quality
  - 🏷️ Best Prices
  - 🎁 Gift Ready

#### Section 6: New Arrivals
- **Widget:** WooCommerce Products
- **Settings:**
  - Filter: Recent
  - Count: 4
  - Columns: 4

#### Section 7: Testimonials
- **3 Columns:** Review cards with stars

#### Section 8: Newsletter
- **Background:** Gradient (FF6B6B → 4ECDC4)
- **Email form** with subscribe button

### Step 5: Create Header Template

1. **Elementor → My Templates → Add New**
2. **Type:** Header
3. **Name:** Shopzario Header

**Structure:**
```
[Announcement Bar - Full width, coral bg, white text]
[Header - Logo | Nav Menu | Icons (Search, Account, Cart)]
```

**Settings:**
- Sticky: Yes
- Transparent on scroll: No
- Border: None
- Shadow: 0 2px 10px rgba(0,0,0,0.05)

### Step 6: Create Footer Template

1. **Elementor → My Templates → Add New**
2. **Type:** Footer
3. **Name:** Shopzario Footer

**Structure:**
```
[4 Columns]
  - About + Social
  - Quick Links
  - Customer Service
  - Newsletter
[Bottom Bar - Copyright + Payment Icons]
```

**Background:** #2C3E50 (dark)
**Text:** White

### Step 7: Create Product Page Template

1. **Elementor → Theme Builder → Single Product**
2. **Add New**

**Structure:**
```
[Product Gallery - Left]
[Product Info - Right]
  - Title
  - Rating
  - Price (coral color)
  - Short Description
  - Add to Cart
  - Trust Badges

[Tabs]
  - Description
  - Reviews
  - Shipping

[Related Products - 4 columns]
[Recently Viewed - 4 columns]
```

### Step 8: Create Category Page

1. **Elementor → Theme Builder → Product Archive**
2. **Add New**

**Structure:**
```
[Page Header]
  - Breadcrumbs
  - Category Title
  - Description

[Products Grid]
  - Filter sidebar
  - Sort dropdown
  - 4 columns grid
  - Pagination
```

### Step 9: Create Cart Page

1. **Pages → Cart → Edit with Elementor**
2. **Add WooCommerce Cart widget**
3. **Style:**
   - 2 columns (70/30)
   - Left: Cart items + coupon
   - Right: Order summary + checkout button

### Step 10: Create Checkout Page

1. **Pages → Checkout → Edit with Elementor**
2. **Add WooCommerce Checkout widget**
3. **Style:** Minimal, clean layout
4. **2 columns:** Form | Order summary

---

## 📱 MOBILE OPTIMIZATION

1. **Elementor → Responsive Mode**
2. **Tablet (1024px):**
   - Reduce padding
   - 2-column grids
3. **Mobile (768px):**
   - Single column
   - Stacked sections
   - Larger touch targets (44px min)

---

## 🖼️ IMAGES NEEDED

Upload these to **Media Library:**

1. **Hero Background** (optional, gradient is default)
2. **Category Images:**
   - electronics-category.jpg
   - home-garden-category.jpg
   - fashion-category.jpg
   - sports-category.jpg
3. **Trust Badge Icons** (or use emojis)
4. **Product placeholder** (for products without images)

**Image Sizes:**
- Category: 600x600px
- Products: 800x800px
- Hero: 1920x800px

---

## 🔧 WOOCOMMERCE SETTINGS

1. **WooCommerce → Settings → Products:**
   - Shop page: Shop
   - Add to cart behavior: AJAX

2. **WooCommerce → Settings → Accounts:**
   - Enable registration
   - Enable guest checkout

3. **WooCommerce → Settings → Emails:**
   - Customize email templates with brand colors

---

## 🧪 TESTING CHECKLIST

- [ ] Homepage loads correctly
- [ ] All buttons work
- [ ] Product grid displays
- [ ] Add to cart works
- [ ] Cart page styled
- [ ] Checkout flows properly
- [ ] Mobile responsive
- [ ] Header sticky on scroll
- [ ] Footer shows on all pages
- [ ] Newsletter form submits

---

## 🚀 GO LIVE CHECKLIST

- [ ] All plugins updated
- [ ] SSL certificate active
- [ ] Payment gateways configured
- [ ] Shipping rates set
- [ ] Tax settings configured
- [ ] Legal pages created
- [ ] Products imported
- [ ] Automation scripts running
- [ ] Backups configured

---

**Design Assets Location:**
`/root/.openclaw/workspace/skills/woocommerce-dropshipping/assets/`

**Support:** Full documentation in `SHOPZARIO_COMPLETE.md`
