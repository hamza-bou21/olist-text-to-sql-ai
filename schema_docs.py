# schema_docs.py

TABLE_SCHEMAS = {
    "orders": (
        "Main transactional table containing one row per item ordered. "
        "Key columns include: 'order_id' (unique identifier), 'customer_id' (links to customers table), "
        "'product_id' (links to products table), 'seller_id' (identifies the vendor), 'order_status', "
        "'order_purchase_timestamp', 'delivery_time_days' (how long shipping took), 'delay_days' (positive numbers mean late delivery, negative mean early), "
        "'price' (cost of the product), and 'freight_value' (shipping cost). "
        "Use this table for calculating total sales, order volumes, shipping durations, delays, financial performance, and timeline metrics."
    ),
    
    "customers": (
        "Contains demographic information about the buyers. Each row represents a unique customer-to-order mapping. "
        "Key columns include: 'customer_id' (matches the customer_id in the orders table), "
        "'customer_unique_id' (uniquely tracks the actual person across multiple distinct orders), "
        "'customer_city', and 'customer_state'. "
        "Use this table when filtering or grouping metrics by geographic locations (cities/states) or analyzing repeat customer purchasing patterns."
    ),
    
    "products": (
        "Contains descriptive data for all items sold on the platform. "
        "Key columns include: 'product_id' (matches product_id in the orders table), "
        "'product_category_name_english' (the category translated to English, e.g., 'housewares', 'perfumery'), "
        "'product_weight_g' (weight in grams), 'product_length_cm', 'product_height_cm', and 'product_width_cm'. "
        "Use this table to filter or group performance metrics by product categories or analyze how physical dimensions affect shipping constraints."
    ),
    
    "payments": (
        "Contains financial details regarding how orders were paid for. An order can have multiple payment methods. "
        "Key columns include: 'order_id' (links back to the orders table), 'payment_type' (e.g., 'credit_card', 'boleto', 'voucher'), "
        "'payment_installments' (number of monthly splits chosen), and 'payment_value' (total amount paid in that transaction line). "
        "Use this table to analyze preferred payment types, installment distribution, or to cross-verify gross cash flow figures."
    ),
    
    "reviews": (
        "Contains customer feedback and rating metrics left after delivery. "
        "Key columns include: 'review_id', 'order_id' (links to the orders table), 'review_score' (numeric rating from 1 to 5), "
        "and text fields like 'review_comment_title' and 'review_comment_message'. "
        "Use this table to measure customer satisfaction, calculate average review scores across categories, or evaluate how shipping delays impact overall ratings."
    )
}