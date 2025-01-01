---
layout: "default"
title: NULLIF in SQL Server
comments: true
date: "2025-01-01"
categories: jekyll update
---

# TIL: Handling Division by Zero with NULLIF in SQL Server  

## The Problem  
Dividing by zero in SQL Server raises an error, potentially breaking queries.  

## Solution: `NULLIF`  
`NULLIF(expression1, expression2)` returns:  
- `NULL` if `expression1` equals `expression2`  
- `expression1` if they differ  

**Example:**  
```sql
SELECT 100 / NULLIF(0, 0)  -- Returns NULL (no error)
