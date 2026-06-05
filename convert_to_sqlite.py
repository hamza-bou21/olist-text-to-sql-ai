import sqlite3
import pandas as pd

def reverse_engineer_db():
    print("⏳ Loading master cleaned data from olist_clean.csv...")
    df = pd.read_csv('olist_clean.csv')
    
    # Connect to SQLite database (creates olist.db automatically)
    conn = sqlite3.connect('olist.db')
    print("Connected to database: olist.db")
    
    # 1. Create 'customers' table 
    print("Creating 'customers' table...")
    customers = df[[
        'customer_id', 'customer_unique_id', 'customer_zip_code_prefix', 
        'customer_city', 'customer_state'
    ]].drop_duplicates(subset=['customer_id'])
    customers.to_sql('customers', conn, if_exists='replace', index=False)
    
    # 2. Create 'products' table 
    print("Creating 'products' table...")
    products = df[[
        'product_id', 'product_category_name', 'product_category_name_english',
        'product_name_lenght', 'product_description_lenght', 'product_photos_qty',
        'product_weight_g', 'product_length_cm', 'product_height_cm', 'product_width_cm'
    ]].drop_duplicates(subset=['product_id'])
    products.to_sql('products', conn, if_exists='replace', index=False)
    
    # 3. Create 'payments' table
    print("Creating 'payments' table...")
    payments = df[[
        'order_id', 'payment_sequential', 'payment_type', 
        'payment_installments', 'payment_value'
    ]].dropna(subset=['payment_value'])
    payments.to_sql('payments', conn, if_exists='replace', index=False)
    
    # 4. Create 'reviews' table
    print("Creating 'reviews' table...")
    reviews = df[[
        'review_id', 'order_id', 'review_score', 'review_comment_title', 
        'review_comment_message', 'review_creation_date', 'review_answer_timestamp'
    ]].drop_duplicates(subset=['review_id'])
    reviews.to_sql('reviews', conn, if_exists='replace', index=False)

    # 5. Create core 'orders' table
    print("Creating 'orders' table...")
    orders = df[[
        'order_id', 'customer_id', 'product_id', 'seller_id', 'order_status', 
        'order_purchase_timestamp', 'order_approved_at', 'order_delivered_carrier_date', 
        'order_delivered_customer_date', 'order_estimated_delivery_date', 
        'delivery_time_days', 'delay_days', 'price', 'freight_value', 'order_month'
    ]]
    orders.to_sql('orders', conn, if_exists='replace', index=False)
    
    conn.close()
    print("\n🎉 Success! Relational SQLite database 'olist.db' created with 5 clean tables.")

if __name__ == "__main__":
    reverse_engineer_db()