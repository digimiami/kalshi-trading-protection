#!/usr/bin/env python3
"""
Bulk Product Importer for Dropshipping
Import products from CSV, JSON, or supplier APIs
"""
import csv
import json
import sys
import argparse
from dropshipping_core import WooCommerceDropshipping, DropshippingAutomator

class ProductImporter:
    def __init__(self, store_url: str, consumer_key: str, consumer_secret: str):
        self.wc = WooCommerceDropshipping(store_url, consumer_key, consumer_secret)
        self.automator = DropshippingAutomator(self.wc)
    
    def import_from_csv(self, csv_file: str, markup: float = 40):
        """Import products from CSV file"""
        print(f"📁 Importing from: {csv_file}")
        
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            imported = 0
            failed = 0
            
            for row in reader:
                try:
                    supplier_data = {
                        'title': row.get('title', ''),
                        'description': row.get('description', ''),
                        'price': float(row.get('price', 0)),
                        'images': row.get('images', '').split(','),
                        'category': row.get('category', 'General'),
                        'id': row.get('supplier_id', ''),
                        'url': row.get('supplier_url', '')
                    }
                    
                    result = self.automator.auto_import_product(supplier_data)
                    if result:
                        imported += 1
                        print(f"  ✅ {supplier_data['title'][:50]}...")
                    else:
                        failed += 1
                        
                except Exception as e:
                    print(f"  ❌ Error: {e}")
                    failed += 1
            
            print(f"\n📊 Import Complete: {imported} imported, {failed} failed")
    
    def import_from_json(self, json_file: str):
        """Import products from JSON file"""
        print(f"📁 Importing from: {json_file}")
        
        with open(json_file, 'r', encoding='utf-8') as f:
            products = json.load(f)
        
        imported = 0
        failed = 0
        
        for product in products:
            try:
                result = self.automator.auto_import_product(product)
                if result:
                    imported += 1
                    print(f"  ✅ {product.get('title', 'Unknown')[:50]}...")
                else:
                    failed += 1
            except Exception as e:
                print(f"  ❌ Error: {e}")
                failed += 1
        
        print(f"\n📊 Import Complete: {imported} imported, {failed} failed")

def main():
    parser = argparse.ArgumentParser(description='Bulk import products to WooCommerce')
    parser.add_argument('file', help='CSV or JSON file to import')
    parser.add_argument('--markup', type=float, default=40, help='Markup percentage (default: 40)')
    
    args = parser.parse_args()
    
    # Initialize
    importer = ProductImporter(
        store_url="https://shopzario.com",
        consumer_key="ck_4ccb7bf7646bbdaf1cf93fe46de4e7b433183a6f",
        consumer_secret="cs_906249467eb29a94824634c31d3039d9754c871e"
    )
    
    # Detect file type
    if args.file.endswith('.csv'):
        importer.import_from_csv(args.file, args.markup)
    elif args.file.endswith('.json'):
        importer.import_from_json(args.file)
    else:
        print("❌ Unsupported file format. Use .csv or .json")
        sys.exit(1)

if __name__ == '__main__':
    main()
