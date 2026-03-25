## Segmentation Results (KMeans)
**Clusters:** 2  |  **Silhouette Score:** 0.1514

### Cluster Sizes
| Cluster | Count | % |
|---------|-------|---|
| 0 | 2,409 | 48.2% |
| 1 | 2,591 | 51.8% |

### Cluster Profiles (feature means)
| Cluster | product_price | quantity | discount_pct | days_since_last_order | total_orders | total_revenue | converted |
|---------|------|------|------|------|------|------|------|
| 0 | 250.9029 | 2.956 | 0.2108 | 183.2648 | 27.3346 | 2519.5979 | 1.0 |
| 1 | 249.2354 | 3.0374 | 0.189 | 184.7657 | 23.7179 | 2526.3358 | 0.0 |

### Notes
- Optimal k selected automatically: 2 (elbow method, max_k=10)