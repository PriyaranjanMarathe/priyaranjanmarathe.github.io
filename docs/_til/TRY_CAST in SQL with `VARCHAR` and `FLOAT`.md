---
layout: "default"
title: TRY_CAST in SQL with `VARCHAR` and `FLOAT`
comments: true
date: "2025-01-11"
categories: jekyll update
---

### TIL: TRY_CAST in SQL with `BIGINT` and `VARCHAR`

**Problem**: A column contains inconsistent data, mixing numeric and non-numeric values. Direct `CAST` fails for invalid values.

**Fix**: Use `TRY_CAST` to handle conversions gracefully.

#### Example:
**Scenario**: A column `data_column` contains mixed data:
| data_column   |
|---------------|
| `12345`       |
| `67890`       |
| `INVALID123`  |
| `NULL`        |

**Query**:
```sql
SELECT 
    TRY_CAST(data_column AS BIGINT) AS converted_bigint,
    TRY_CAST(data_column AS VARCHAR(10)) AS converted_varchar
FROM sample_table;

