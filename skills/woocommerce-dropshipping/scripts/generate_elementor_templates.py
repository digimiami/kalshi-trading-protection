#!/usr/bin/env python3
"""
Shopzario Elementor Design Installer
Automatically sets up the Elementor design
"""
import json
import os

def generate_elementor_json():
    """Generate Elementor template JSON for import"""
    
    template = {
        "version": "0.4",
        "title": "Shopzario Homepage",
        "type": "page",
        "content": [
            # Hero Section
            {
                "id": "hero_section",
                "elType": "section",
                "settings": {
                    "background_background": "gradient",
                    "background_color": "#FF6B6B",
                    "background_color_b": "#4ECDC4",
                    "background_gradient_angle": {"unit": "deg", "size": 135},
                    "padding": {"unit": "px", "top": "120", "bottom": "120"}
                },
                "elements": [
                    {
                        "id": "hero_container",
                        "elType": "container",
                        "elements": [
                            {
                                "elType": "heading",
                                "settings": {
                                    "title": "Discover Trending Products",
                                    "align": "center",
                                    "typography_font_size": {"unit": "px", "size": 64},
                                    "typography_font_family": "Poppins",
                                    "title_color": "#FFFFFF"
                                }
                            },
                            {
                                "elType": "text-editor",
                                "settings": {
                                    "editor": "Premium quality at unbeatable prices. Free shipping over $50!",
                                    "align": "center",
                                    "typography_font_size": {"unit": "px", "size": 24},
                                    "text_color": "#FFFFFF"
                                }
                            },
                            {
                                "elType": "button",
                                "settings": {
                                    "text": "Shop Now",
                                    "align": "center",
                                    "background_color": "#FFFFFF",
                                    "text_color": "#FF6B6B",
                                    "border_radius": {"unit": "px", "top": "50", "right": "50", "bottom": "50", "left": "50"},
                                    "button_padding": {"unit": "px", "top": "20", "right": "50", "bottom": "20", "left": "50"},
                                    "link": {"url": "/shop"}
                                }
                            }
                        ]
                    }
                ]
            },
            
            # Trust Badges Section
            {
                "id": "trust_section",
                "elType": "section",
                "settings": {
                    "background_color": "#F7F9FC",
                    "padding": {"unit": "px", "top": "40", "bottom": "40"}
                },
                "elements": [
                    {
                        "elType": "container",
                        "settings": {"flex_direction": "row", "justify_content": "space-around"},
                        "elements": [
                            {
                                "elType": "icon-box",
                                "settings": {
                                    "icon": {"value": "fas fa-truck", "library": "fa-solid"},
                                    "title_text": "Free Shipping",
                                    "description_text": "On orders over $50"
                                }
                            },
                            {
                                "elType": "icon-box",
                                "settings": {
                                    "icon": {"value": "fas fa-shield-alt", "library": "fa-solid"},
                                    "title_text": "Secure Payment",
                                    "description_text": "100% protected"
                                }
                            },
                            {
                                "elType": "icon-box",
                                "settings": {
                                    "icon": {"value": "fas fa-undo", "library": "fa-solid"},
                                    "title_text": "Easy Returns",
                                    "description_text": "30-day policy"
                                }
                            },
                            {
                                "elType": "icon-box",
                                "settings": {
                                    "icon": {"value": "fas fa-headset", "library": "fa-solid"},
                                    "title_text": "24/7 Support",
                                    "description_text": "Always here"
                                }
                            }
                        ]
                    }
                ]
            },
            
            # Categories Section
            {
                "id": "categories_section",
                "elType": "section",
                "settings": {"padding": {"unit": "px", "top": "80", "bottom": "80"}},
                "elements": [
                    {
                        "elType": "heading",
                        "settings": {
                            "title": "Shop by Category",
                            "align": "center",
                            "typography_font_size": {"unit": "px", "size": 42},
                            "typography_font_family": "Poppins"
                        }
                    },
                    {
                        "elType": "container",
                        "settings": {"flex_direction": "row", "gap": {"unit": "px", "size": 30}},
                        "elements": [
                            {
                                "elType": "container",
                                "settings": {
                                    "background_background": "gradient",
                                    "background_color": "#667eea",
                                    "background_color_b": "#764ba2",
                                    "border_radius": {"unit": "px", "size": 16},
                                    "min_height": {"unit": "px", "size": 300}
                                },
                                "elements": [{
                                    "elType": "heading",
                                    "settings": {"title": "Electronics", "title_color": "#FFFFFF"}
                                }]
                            },
                            {
                                "elType": "container",
                                "settings": {
                                    "background_background": "gradient",
                                    "background_color": "#f093fb",
                                    "background_color_b": "#f5576c",
                                    "border_radius": {"unit": "px", "size": 16},
                                    "min_height": {"unit": "px", "size": 300}
                                },
                                "elements": [{
                                    "elType": "heading",
                                    "settings": {"title": "Home & Garden", "title_color": "#FFFFFF"}
                                }]
                            },
                            {
                                "elType": "container",
                                "settings": {
                                    "background_background": "gradient",
                                    "background_color": "#4facfe",
                                    "background_color_b": "#00f2fe",
                                    "border_radius": {"unit": "px", "size": 16},
                                    "min_height": {"unit": "px", "size": 300}
                                },
                                "elements": [{
                                    "elType": "heading",
                                    "settings": {"title": "Fashion", "title_color": "#FFFFFF"}
                                }]
                            },
                            {
                                "elType": "container",
                                "settings": {
                                    "background_background": "gradient",
                                    "background_color": "#43e97b",
                                    "background_color_b": "#38f9d7",
                                    "border_radius": {"unit": "px", "size": 16},
                                    "min_height": {"unit": "px", "size": 300}
                                },
                                "elements": [{
                                    "elType": "heading",
                                    "settings": {"title": "Sports", "title_color": "#FFFFFF"}
                                }]
                            }
                        ]
                    }
                ]
            },
            
            # Products Section
            {
                "id": "products_section",
                "elType": "section",
                "settings": {"padding": {"unit": "px", "top": "80", "bottom": "80"}},
                "elements": [
                    {
                        "elType": "heading",
                        "settings": {
                            "title": "🔥 Trending Now",
                            "typography_font_size": {"unit": "px", "size": 42},
                            "typography_font_family": "Poppins"
                        }
                    },
                    {
                        "elType": "wc-products",
                        "settings": {
                            "columns": 4,
                            "limit": 8,
                            "orderby": "popularity"
                        }
                    }
                ]
            },
            
            # Newsletter Section
            {
                "id": "newsletter_section",
                "elType": "section",
                "settings": {
                    "background_background": "gradient",
                    "background_color": "#FF6B6B",
                    "background_color_b": "#4ECDC4",
                    "padding": {"unit": "px", "top": "100", "bottom": "100"}
                },
                "elements": [
                    {
                        "elType": "heading",
                        "settings": {
                            "title": "Join the VIP Club",
                            "align": "center",
                            "title_color": "#FFFFFF",
                            "typography_font_size": {"unit": "px", "size": 42}
                        }
                    },
                    {
                        "elType": "text-editor",
                        "settings": {
                            "editor": "Subscribe and get 15% off your first order + exclusive deals",
                            "align": "center",
                            "text_color": "#FFFFFF"
                        }
                    },
                    {
                        "elType": "form",
                        "settings": {
                            "form_fields": [
                                {
                                    "field_type": "email",
                                    "field_label": "Email",
                                    "placeholder": "Enter your email",
                                    "required": "true"
                                }
                            ],
                            "button_text": "Subscribe",
                            "button_background_color": "#2C3E50",
                            "button_border_radius": {"unit": "px", "size": 50}
                        }
                    }
                ]
            }
        ]
    }
    
    return template

def save_templates():
    """Save all templates to files"""
    
    # Homepage template
    homepage = generate_elementor_json()
    with open('/tmp/shopzario-elementor-homepage.json', 'w') as f:
        json.dump(homepage, f, indent=2)
    
    print("✅ Templates generated:")
    print("  - /tmp/shopzario-elementor-homepage.json")
    print("\n📥 IMPORT INSTRUCTIONS:")
    print("1. Go to Elementor → My Templates")
    print("2. Click 'Import' button")
    print("3. Upload: shopzario-elementor-homepage.json")
    print("4. Insert into your homepage")
    
def print_custom_css():
    """Print custom CSS for manual entry"""
    css_path = '/root/.openclaw/workspace/skills/woocommerce-dropshipping/assets/shopzario-custom.css'
    if os.path.exists(css_path):
        print("\n" + "="*60)
        print("📋 CUSTOM CSS (Copy to Appearance → Customize → CSS):")
        print("="*60)
        with open(css_path) as f:
            print(f.read()[:2000] + "\n... [truncated, see full file]")

def main():
    """Generate all templates"""
    print("="*60)
    print("🎨 SHOPZARIO ELEMENTOR DESIGN GENERATOR")
    print("="*60)
    
    save_templates()
    
    print("\n" + "="*60)
    print("📁 FILES READY:")
    print("="*60)
    print("1. Elementor Template: /tmp/shopzario-elementor-homepage.json")
    print("2. Custom CSS: ./assets/shopzario-custom.css")
    print("3. HTML Template: ./assets/elementor-homepage.html")
    print("4. Setup Guide: ./ELEMENTOR_SETUP_GUIDE.md")
    
    print("\n" + "="*60)
    print("🚀 NEXT STEPS:")
    print("="*60)
    print("1. Login: https://shopzario.com/wp-admin")
    print("2. Elementor → My Templates → Import")
    print("3. Upload the JSON file")
    print("4. Add CSS to Appearance → Customize")
    print("5. Set fonts: Poppins (headings), Inter (body)")
    
if __name__ == '__main__':
    main()
