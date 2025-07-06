# Grocery Genie Database Schema Documentation

## 🎯 Overview

This document provides comprehensive documentation for the Grocery Genie database schema, designed for AI agents to understand and query grocery purchase data from multiple retailers.

**Database Type:** PostgreSQL  
**Total Tables:** 5 (1 utility + 4 retailer tables)  
**Total Records:** 4,392 grocery purchase items  
**Data Coverage:** 2023-2025 purchase history  

## 📊 Database Statistics

| Table | Record Count | Primary Retailer | Data Range |
|-------|-------------|------------------|------------|
| `costco_purchases` | 3,169 | Costco Wholesale | 2024-2025 |
| `walmart_purchases` | 545 | Walmart | 2023-2024 |
| `cvs_purchases` | 156 | CVS Pharmacy | 2024 |
| `publix_purchases` | 522 | Publix Super Markets | 2024-2025 |
| `grocery_stores` | N/A | Store metadata | Utility table |

## 🏪 Table Schemas

### 1. costco_purchases

**Purpose:** Stores Costco warehouse and gas station purchase data  
**Design:** One row per item purchased  
**Key Features:** Fuel purchases, membership tracking, warehouse locations  

#### Core Fields
```sql
-- Primary identification
id SERIAL PRIMARY KEY
purchase_date DATE NOT NULL              -- Date of purchase
purchase_time TIME                       -- Time of purchase
store_location VARCHAR(200)              -- "PEMBROKE PINES #742"
receipt_number VARCHAR(50)               -- Unique receipt identifier

-- Item details
item_code VARCHAR(20)                    -- Costco item number
item_name VARCHAR(300) NOT NULL          -- "BANANAS 3 LB / 1.36 KG"
item_price DECIMAL(10,2) NOT NULL        -- Individual item total price
item_quantity INTEGER DEFAULT 1         -- Quantity purchased
item_unit_price DECIMAL(10,2)           -- Price per unit
tax_indicator VARCHAR(10)               -- Tax status code
item_type VARCHAR(50)                   -- Receipt type (warehouse/gas)
item_department VARCHAR(20)             -- Department number

-- Financial totals (repeated per item)
subtotal DECIMAL(10,2)                  -- Receipt subtotal
tax_total DECIMAL(10,2)                 -- Total taxes
total_amount DECIMAL(10,2)              -- Grand total
instant_savings DECIMAL(10,2)           -- Costco instant savings

-- Costco-specific fields
membership_number VARCHAR(20)           -- Member ID
warehouse_number VARCHAR(10)            -- Store number
transaction_number VARCHAR(20)          -- Transaction ID
register_number VARCHAR(10)             -- Register number
operator_number VARCHAR(10)             -- Cashier ID

-- Fuel-specific fields (for gas purchases)
fuel_quantity DECIMAL(10,3)             -- Gallons purchased
fuel_grade VARCHAR(50)                  -- "Regular", "Premium"
fuel_unit_price DECIMAL(10,3)           -- Price per gallon

-- Additional info
payment_method VARCHAR(100)             -- Payment type
store_address VARCHAR(300)              -- Store address
raw_data JSONB                          -- Complete receipt data
created_at TIMESTAMP DEFAULT NOW()
updated_at TIMESTAMP DEFAULT NOW()
```

#### Sample Data
```sql
-- Example Costco record
purchase_date: 2024-11-17
purchase_time: 11:49:00
store_location: "PEMBROKE PINES #742"
receipt_number: "21074200900682411171149"
item_code: "30669"
item_name: "BANANAS 3 LB / 1.36 KG"
item_price: 2.98
item_quantity: 2
item_unit_price: 1.49
membership_number: "1234567890"
warehouse_number: "742"
```

### 2. walmart_purchases

**Purpose:** Stores Walmart in-store and online purchase data  
**Design:** One row per item purchased  
**Key Features:** Order tracking, fulfillment types, detailed item metadata  

#### Core Fields
```sql
-- Order identification
id SERIAL PRIMARY KEY
order_id VARCHAR(50) NOT NULL           -- "82212587690309178447"
group_id VARCHAR(50)                    -- Order group identifier
purchase_order_id VARCHAR(50)           -- PO number
display_id VARCHAR(50)                  -- "8221-2587-6903-0917-8447"
purchase_date DATE NOT NULL
purchase_time TIME

-- Order details
order_type VARCHAR(50)                  -- "IN_STORE", "ONLINE"
fulfillment_type VARCHAR(50)            -- "IN_STORE", "DELIVERY", "PICKUP"
status_type VARCHAR(50)                 -- Order status
delivery_message VARCHAR(200)           -- Delivery instructions

-- Item details
item_id VARCHAR(50)                     -- Walmart item ID
item_name VARCHAR(300) NOT NULL         -- Product name
item_price DECIMAL(10,2)                -- Item price
item_quantity INTEGER DEFAULT 1        -- Quantity
item_unit_price DECIMAL(10,2)          -- Unit price
item_brand VARCHAR(200)                -- Brand name
item_category VARCHAR(100)             -- Product category
item_subcategory VARCHAR(100)          -- Subcategory
item_sku VARCHAR(50)                   -- SKU
item_upc VARCHAR(50)                   -- UPC code
item_image_url VARCHAR(500)            -- Product image URL

-- Store information
store_id VARCHAR(20)                   -- Store number
store_name VARCHAR(200)                -- Store name
store_address VARCHAR(300)             -- Full address
store_city VARCHAR(100)
store_state VARCHAR(10)
store_zip VARCHAR(20)

-- Financial data
subtotal DECIMAL(10,2)                 -- Order subtotal
tax_total DECIMAL(10,2)                -- Total tax
shipping_total DECIMAL(10,2)           -- Shipping cost
total_amount DECIMAL(10,2)             -- Grand total
payment_method VARCHAR(100)            -- Payment type

-- Fulfillment tracking
tracking_number VARCHAR(100)           -- Shipment tracking
carrier VARCHAR(50)                    -- Shipping carrier
delivery_date DATE                     -- Delivered date
pickup_date DATE                       -- Pickup date

-- Flags
is_pet_rx BOOLEAN DEFAULT FALSE        -- Prescription item
is_active BOOLEAN DEFAULT FALSE        -- Active order
is_shipped_by_walmart BOOLEAN DEFAULT FALSE

-- Metadata
raw_data JSONB
created_at TIMESTAMP DEFAULT NOW()
updated_at TIMESTAMP DEFAULT NOW()
```

#### Sample Data
```sql
-- Example Walmart record
order_id: "82212587690309178447"
display_id: "8221-2587-6903-0917-8447"
purchase_date: 2023-04-02
purchase_time: 19:03:09
order_type: "IN_STORE"
fulfillment_type: "IN_STORE"
item_name: "Great Value Whole Milk, 1 Gallon"
item_price: 3.48
item_quantity: 1
item_brand: "Great Value"
store_name: "Walmart Supercenter #1234"
```

### 3. cvs_purchases

**Purpose:** Stores CVS Pharmacy purchase data including prescriptions and retail items
**Design:** One row per item purchased
**Key Features:** FSA/HSA tracking, ExtraCare rewards, prescription management

#### Core Fields
```sql
-- Order identification
id SERIAL PRIMARY KEY
order_number VARCHAR(50) NOT NULL       -- "5083-2-4898-20240708"
order_type VARCHAR(50)                  -- "STORE", "ONLINE"
purchase_date DATE NOT NULL
purchase_time TIME

-- Financial totals
subtotal DECIMAL(10,2)                  -- Order subtotal
tax_total DECIMAL(10,2)                 -- Total tax
savings_total DECIMAL(10,2)             -- Total savings (negative)
shipping_total DECIMAL(10,2)            -- Shipping cost
grand_total DECIMAL(10,2)               -- Final total

-- Store information
store_id VARCHAR(20)                    -- CVS store number
ec_card VARCHAR(20)                     -- ExtraCare card number
transaction_number VARCHAR(20)          -- Transaction ID
register_number VARCHAR(20)             -- Register number

-- Item details
item_id VARCHAR(50)                     -- CVS item ID
item_name VARCHAR(300) NOT NULL         -- Product name
item_size VARCHAR(50)                   -- Package size
item_size_uom VARCHAR(20)               -- Size unit of measure
item_weight VARCHAR(50)                 -- Product weight
item_weight_uom VARCHAR(20)             -- Weight unit
item_quantity INTEGER DEFAULT 1        -- Quantity purchased
item_price_total DECIMAL(10,2)          -- Total item price
item_price_final DECIMAL(10,2)          -- Final price after discounts
item_savings DECIMAL(10,2)              -- Item-level savings
item_tax DECIMAL(10,2)                  -- Item tax amount
item_line_total_without_tax DECIMAL(10,2) -- Pre-tax total
item_status VARCHAR(50)                 -- Item status
item_image_url VARCHAR(500)             -- Product image
item_url VARCHAR(500)                   -- Product page URL

-- CVS-specific features
ec_rewards_eligible BOOLEAN DEFAULT FALSE -- ExtraCare eligible
in_store_only_item BOOLEAN DEFAULT FALSE   -- Store-only item

-- Payment information
payment_type VARCHAR(50)                -- Payment method
payment_last_four VARCHAR(10)           -- Last 4 digits of card
payment_amount_charged DECIMAL(10,2)    -- Amount charged
payment_amount_returned DECIMAL(10,2)   -- Amount returned

-- Return/exchange flags
split_shipment BOOLEAN DEFAULT FALSE
split_fulfillment BOOLEAN DEFAULT FALSE
return_eligible BOOLEAN DEFAULT FALSE
return_eligible_final_date DATE         -- Return deadline

-- Metadata
raw_data JSONB
created_at TIMESTAMP DEFAULT NOW()
updated_at TIMESTAMP DEFAULT NOW()
```

#### Sample Data
```sql
-- Example CVS record
order_number: "5083-2-4898-20240708"
order_type: "STORE"
purchase_date: 2024-07-08
purchase_time: 15:27:00
subtotal: 41.70
tax_total: 2.36
savings_total: -2.00
grand_total: 42.06
item_name: "CVS Health Ibuprofen 200mg, 100 Tablets"
item_price_final: 8.99
ec_rewards_eligible: true
```

### 4. publix_purchases

**Purpose:** Stores Publix Super Markets purchase data with detailed receipt parsing
**Design:** One row per item purchased
**Key Features:** FSA tracking, digital coupons, receipt line-item parsing

#### Core Fields
```sql
-- Transaction identification
id SERIAL PRIMARY KEY
transaction_number VARCHAR(100) NOT NULL -- Transaction ID
receipt_id VARCHAR(200)                  -- Unique receipt identifier
purchase_date DATE NOT NULL
purchase_time TIME

-- Store information
store_name VARCHAR(100)                  -- "Publix At Glade Crossing"
store_address VARCHAR(200)               -- Store address
store_manager VARCHAR(100)               -- Store manager name
store_phone VARCHAR(20)                  -- Store phone number

-- Financial totals
order_total DECIMAL(10,2)                -- Order subtotal
sales_tax DECIMAL(10,2)                  -- Sales tax amount
grand_total DECIMAL(10,2)                -- Final total
vendor_coupon_amount DECIMAL(10,2)       -- Manufacturer coupons
store_coupon_amount DECIMAL(10,2)        -- Store coupons
digital_coupon_savings DECIMAL(10,2)     -- Digital coupon savings
total_savings DECIMAL(10,2)              -- Total savings amount

-- Item details (from API)
item_id VARCHAR(100)                     -- Publix item ID
item_name VARCHAR(300) NOT NULL          -- Product name
item_description VARCHAR(500)            -- Extended description
item_quantity INTEGER DEFAULT 1         -- Quantity purchased
item_price DECIMAL(10,2)                 -- Item price
item_size_description VARCHAR(100)       -- Size description
item_image_url VARCHAR(500)              -- Product image URL
item_detail_url VARCHAR(500)             -- Product detail page
upc VARCHAR(100)                         -- UPC barcode
base_product_id VARCHAR(200)             -- Base product identifier
retail_sub_section_number VARCHAR(50)    -- Department section
activation_status VARCHAR(10)            -- Item activation status

-- Receipt line parsing
receipt_line_text VARCHAR(500)           -- Raw receipt line text
is_voided_item BOOLEAN DEFAULT FALSE     -- Voided/returned item
item_tax_flag VARCHAR(10)                -- Tax flag (T, H, F, P)

-- Payment information
payment_method VARCHAR(100)              -- Payment type
payment_amount DECIMAL(10,2)             -- Payment amount
payment_account_number VARCHAR(100)      -- Account number (masked)
payment_auth_number VARCHAR(100)         -- Authorization number
payment_trace_number VARCHAR(100)        -- Trace number
payment_reference_number VARCHAR(100)    -- Reference number

-- FSA/HSA tracking
fsa_prescription_amount DECIMAL(10,2)    -- FSA prescription amount
fsa_non_prescription_amount DECIMAL(10,2) -- FSA non-prescription
fsa_total DECIMAL(10,2)                  -- Total FSA amount

-- Staff information
cashier_name VARCHAR(100)                -- Cashier name
supervisor_number VARCHAR(20)            -- Supervisor ID

-- Metadata
raw_data JSONB
created_at TIMESTAMP DEFAULT NOW()
updated_at TIMESTAMP DEFAULT NOW()
```

#### Sample Data
```sql
-- Example Publix record
transaction_number: "1234567890"
receipt_id: "XEjVwCKyXa7GcB7N6G3IWxbgIZ948g..."
purchase_date: 2024-12-30
purchase_time: 15:00:00
store_name: "Publix At Glade Crossing"
order_total: 45.67
sales_tax: 3.21
grand_total: 48.88
item_name: "Publix Organic Bananas"
item_price: 3.98
digital_coupon_savings: 1.50
item_tax_flag: "F"
```

### 5. grocery_stores (Utility Table)

**Purpose:** Store metadata and reference information
**Design:** One row per store location
**Usage:** Lookup table for store information normalization

```sql
id SERIAL PRIMARY KEY
name VARCHAR(50) NOT NULL               -- Store chain name
location VARCHAR(200)                   -- Store location/address
store_number VARCHAR(50)                -- Store identifier
created_at TIMESTAMP DEFAULT NOW()
updated_at TIMESTAMP DEFAULT NOW()
```

## 🔍 Database Indexes

**Performance Optimization:** All tables include strategic indexes for common query patterns:

### Primary Indexes
- **Date-based queries:** `idx_[retailer]_purchase_date` on all tables
- **Store lookups:** Store location/name indexes for geographic analysis
- **Item searches:** Item name indexes for product analysis
- **Transaction tracking:** Receipt/order number indexes for transaction lookup

### Query Performance
- **Date range queries:** Optimized for monthly/yearly analysis
- **Store analysis:** Fast aggregation by location
- **Product searches:** Full-text search capabilities on item names
- **Cross-retailer analysis:** Consistent field naming enables JOIN operations

## 📈 Data Quality & Characteristics

### Data Completeness
- **Costco:** 100% complete with fuel and warehouse data
- **Walmart:** Complete order tracking with fulfillment details
- **CVS:** Complete with ExtraCare and FSA tracking
- **Publix:** Complete with receipt parsing and coupon details

### Data Patterns
- **Purchase Frequency:** Daily to weekly purchases across retailers
- **Item Diversity:** 4,000+ unique products across categories
- **Price Ranges:** $0.50 to $500+ per item
- **Geographic Coverage:** Multiple store locations per retailer
- **Time Span:** 2+ years of historical data

### Data Integrity
- **No Duplicates:** Each item purchase is a unique record
- **Referential Integrity:** All foreign keys properly maintained
- **Data Types:** Proper decimal precision for financial calculations
- **Null Handling:** Graceful handling of missing optional fields

## 🎯 Common Use Cases & Query Patterns

### 1. Spending Analysis

**Monthly spending by retailer:**
```sql
SELECT
    DATE_TRUNC('month', purchase_date) as month,
    'Costco' as retailer,
    SUM(item_price) as total_spent,
    COUNT(*) as items_purchased
FROM costco_purchases
WHERE purchase_date >= '2024-01-01'
GROUP BY DATE_TRUNC('month', purchase_date)
ORDER BY month DESC;
```

**Top spending categories:**
```sql
-- Costco department analysis
SELECT
    item_department,
    SUM(item_price) as total_spent,
    COUNT(*) as items,
    AVG(item_price) as avg_price
FROM costco_purchases
WHERE purchase_date >= '2024-01-01'
GROUP BY item_department
ORDER BY total_spent DESC
LIMIT 10;
```

### 2. Product Analysis

**Most frequently purchased items:**
```sql
SELECT
    item_name,
    COUNT(*) as purchase_count,
    SUM(item_quantity) as total_quantity,
    AVG(item_price) as avg_price,
    SUM(item_price) as total_spent
FROM costco_purchases
GROUP BY item_name
ORDER BY purchase_count DESC
LIMIT 20;
```

**Price tracking over time:**
```sql
SELECT
    item_name,
    purchase_date,
    item_price,
    item_unit_price,
    LAG(item_price) OVER (PARTITION BY item_name ORDER BY purchase_date) as prev_price
FROM costco_purchases
WHERE item_name ILIKE '%bananas%'
ORDER BY item_name, purchase_date;
```

### 3. Store Performance Analysis

**Store comparison by total sales:**
```sql
SELECT
    store_location,
    COUNT(DISTINCT receipt_number) as total_visits,
    COUNT(*) as total_items,
    SUM(item_price) as total_spent,
    AVG(total_amount) as avg_receipt_total
FROM costco_purchases
GROUP BY store_location
ORDER BY total_spent DESC;
```

### 4. Cross-Retailer Analysis

**Compare spending across all retailers:**
```sql
WITH retailer_spending AS (
    SELECT 'Costco' as retailer, SUM(item_price) as total, COUNT(*) as items FROM costco_purchases
    UNION ALL
    SELECT 'Walmart' as retailer, SUM(item_price) as total, COUNT(*) as items FROM walmart_purchases
    UNION ALL
    SELECT 'CVS' as retailer, SUM(item_price_final) as total, COUNT(*) as items FROM cvs_purchases
    UNION ALL
    SELECT 'Publix' as retailer, SUM(item_price) as total, COUNT(*) as items FROM publix_purchases
)
SELECT
    retailer,
    total,
    items,
    ROUND(total/items, 2) as avg_item_price
FROM retailer_spending
ORDER BY total DESC;
```

### 5. Savings & Discounts Analysis

**Costco instant savings tracking:**
```sql
SELECT
    DATE_TRUNC('month', purchase_date) as month,
    SUM(instant_savings) as total_savings,
    COUNT(DISTINCT receipt_number) as receipts_with_savings
FROM costco_purchases
WHERE instant_savings > 0
GROUP BY DATE_TRUNC('month', purchase_date)
ORDER BY month DESC;
```

**Publix coupon effectiveness:**
```sql
SELECT
    DATE_TRUNC('month', purchase_date) as month,
    SUM(digital_coupon_savings) as digital_savings,
    SUM(store_coupon_amount) as store_coupons,
    SUM(vendor_coupon_amount) as vendor_coupons,
    SUM(total_savings) as total_savings
FROM publix_purchases
WHERE total_savings > 0
GROUP BY DATE_TRUNC('month', purchase_date)
ORDER BY month DESC;
```

### 6. Fuel Purchase Analysis (Costco-specific)

**Fuel consumption and pricing:**
```sql
SELECT
    DATE_TRUNC('month', purchase_date) as month,
    fuel_grade,
    SUM(fuel_quantity) as total_gallons,
    AVG(fuel_unit_price) as avg_price_per_gallon,
    SUM(item_price) as total_fuel_cost
FROM costco_purchases
WHERE fuel_quantity > 0
GROUP BY DATE_TRUNC('month', purchase_date), fuel_grade
ORDER BY month DESC, fuel_grade;
```

### 7. Health & Pharmacy Analysis

**FSA/HSA eligible purchases (CVS & Publix):**
```sql
-- CVS FSA tracking
SELECT
    item_name,
    SUM(item_price_final) as total_spent,
    COUNT(*) as purchase_count
FROM cvs_purchases
WHERE item_name ILIKE ANY(ARRAY['%vitamin%', '%medicine%', '%health%', '%pharmacy%'])
GROUP BY item_name
ORDER BY total_spent DESC;

-- Publix FSA tracking
SELECT
    DATE_TRUNC('month', purchase_date) as month,
    SUM(fsa_prescription_amount) as prescription_fsa,
    SUM(fsa_non_prescription_amount) as non_prescription_fsa,
    SUM(fsa_total) as total_fsa
FROM publix_purchases
WHERE fsa_total > 0
GROUP BY DATE_TRUNC('month', purchase_date)
ORDER BY month DESC;
```

## 🤖 AI Agent Usage Guidelines

### Query Best Practices

1. **Always use proper date filtering** for performance:
   ```sql
   WHERE purchase_date >= '2024-01-01' AND purchase_date < '2025-01-01'
   ```

2. **Use appropriate aggregation functions:**
   - `SUM()` for financial totals
   - `COUNT()` for item counts
   - `AVG()` for averages
   - `DATE_TRUNC()` for time-based grouping

3. **Handle NULL values gracefully:**
   ```sql
   COALESCE(item_price, 0) as price
   ```

4. **Use ILIKE for case-insensitive searches:**
   ```sql
   WHERE item_name ILIKE '%organic%'
   ```

### Common Patterns for AI Agents

**Pattern 1: Time-series analysis**
```sql
SELECT
    DATE_TRUNC('month', purchase_date) as period,
    SUM(item_price) as total
FROM [retailer]_purchases
WHERE purchase_date >= [start_date]
GROUP BY DATE_TRUNC('month', purchase_date)
ORDER BY period;
```

**Pattern 2: Top N analysis**
```sql
SELECT
    [grouping_field],
    SUM([metric_field]) as total,
    COUNT(*) as count
FROM [retailer]_purchases
GROUP BY [grouping_field]
ORDER BY total DESC
LIMIT [n];
```

**Pattern 3: Comparison analysis**
```sql
WITH current_period AS (...),
     previous_period AS (...)
SELECT
    c.metric - p.metric as change,
    ROUND((c.metric - p.metric) / p.metric * 100, 2) as percent_change
FROM current_period c
JOIN previous_period p ON c.key = p.key;
```

### Field Mapping for Cross-Retailer Queries

| Concept | Costco | Walmart | CVS | Publix |
|---------|--------|---------|-----|--------|
| **Item Price** | `item_price` | `item_price` | `item_price_final` | `item_price` |
| **Total Amount** | `total_amount` | `total_amount` | `grand_total` | `grand_total` |
| **Store ID** | `store_location` | `store_name` | `store_id` | `store_name` |
| **Transaction ID** | `receipt_number` | `order_id` | `order_number` | `transaction_number` |
| **Tax Amount** | `tax_total` | `tax_total` | `tax_total` | `sales_tax` |

### Data Interpretation Notes

1. **Financial Fields:** All monetary values are in USD with 2 decimal precision
2. **Date Fields:** All dates are in YYYY-MM-DD format, times in HH:MM:SS
3. **Quantity Fields:** Integer values representing units purchased
4. **Boolean Fields:** TRUE/FALSE values for flags and indicators
5. **Text Fields:** VARCHAR with appropriate length limits
6. **JSON Fields:** `raw_data` contains complete original data for reference

### Performance Considerations

- **Large Result Sets:** Use LIMIT and pagination for large queries
- **Date Ranges:** Always specify date ranges to avoid full table scans
- **Indexes:** Leverage existing indexes for optimal performance
- **Aggregations:** Use appropriate GROUP BY clauses for summaries
- **JOINs:** Minimize cross-table JOINs unless necessary for analysis

## 📋 Quick Reference

### Table Row Counts (Current)
- `costco_purchases`: 3,169 records
- `walmart_purchases`: 545 records
- `cvs_purchases`: 156 records
- `publix_purchases`: 522 records
- **Total**: 4,392 grocery purchase records

### Date Ranges
- **Earliest Purchase**: 2023-04-02 (Walmart)
- **Latest Purchase**: 2024-12-30 (Publix)
- **Most Active Period**: 2024 (all retailers)

### Key Insights Available
- Multi-retailer spending patterns
- Product price tracking over time
- Store location preferences
- Seasonal purchasing trends
- Savings and discount effectiveness
- Fuel consumption patterns (Costco)
- Health/pharmacy spending (CVS/Publix)

---

**This database provides comprehensive grocery purchase data suitable for financial analysis, spending optimization, product research, and consumer behavior insights.**
