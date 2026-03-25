# EDA Report — Sample-test-project
_Generated 2026-03-24 16:53_

## Dataset Overview
| | |
|---|---|
| Rows | 5,000 |
| Columns | 13 |
| Duplicate rows | 0 |
| Mode | segmentation |

## Column Profiles
| Column | Type | Nulls | Unique | Min | Max | Mean | Samples |
|--------|------|-------|--------|-----|-----|------|---------|
| customer_id | VARCHAR | 0.0% | 993 | — | — | — | C00792, C00063, C00872 |
| order_id | VARCHAR | 0.0% | 5,000 | — | — | — | ORD000022, ORD000027, ORD000063 |
| order_date | DATE | 0.0% | 365 | — | — | — | 2023-04-13, 2023-07-14, 2023-08-04 |
| product_category | VARCHAR | 0.0% | 7 | — | — | — | beauty, electronics, clothing |
| product_price | DOUBLE | 0.0% | 4,746 | 5.03 | 499.99 | 250.0388 | 9.79, 336.6, 234.95 |
| quantity | BIGINT | 0.0% | 5 | 1 | 5 | 2.9982 | 1, 3, 2 |
| discount_pct | DOUBLE | 0.0% | 41 | 0.0 | 0.4 | 0.1995 | 0.15, 0.07, 0.0 |
| channel | VARCHAR | 0.0% | 6 | — | — | — | organic_search, direct, referral |
| country | VARCHAR | 0.0% | 6 | — | — | — | AU, CA, UK |
| days_since_last_order | BIGINT | 0.0% | 366 | 0 | 365 | 184.0426 | 16, 122, 310 |
| total_orders | BIGINT | 0.0% | 50 | 1 | 50 | 25.4604 | 17, 27, 1 |
| total_revenue | DOUBLE | 0.0% | 4,971 | 11.61 | 4999.65 | 2523.0895 | 3254.22, 2835.94, 3180.14 |
| converted | BIGINT | 0.0% | 2 | 0 | 1 | 0.4818 | 0, 1 |