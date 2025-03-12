---
layout: "default"
title: "Weighted vs Simple Averages in Business Impact Analysis"
comments: true
date: "2025-03-11"
categories: tils
---

# TIL: Weighted vs Simple Averages in Business Impact Analysis


## 💡 TIL
Simple averages can be misleading in business analysis. Weighted averages account for relative importance of factors, leading to better decision-making.

## 🎯 Quick Example: Project Impact Analysis

```python
# Performance Metrics
Code Quality:     4.2/5.0 (15% weight) # Automated checks
Architecture:     4.5/5.0 (25% weight) # Long-term maintainability
Business Impact:  4.0/5.0 (35% weight) # Revenue/cost effects
User Feedback:    4.3/5.0 (25% weight) # Adoption metrics

Simple:   (4.2 + 4.5 + 4.0 + 4.3) / 4 = 4.25
Weighted: (4.2×0.15 + 4.5×0.25 + 4.0×0.35 + 4.3×0.25) = 4.24
```

## 🔑 Key Points
- Higher weights for direct business impact (35%)
- User adoption weighted significantly (25%)
- Technical aspects weighted based on long-term value
- Automated checks weighted lower as they're early indicators

## 📊 Formula
```
Weighted_Avg = Σ(Value × Weight) / Σ(Weights)
```

## 💭 Why It Matters
Makes strategic decisions align better with business goals by considering relative importance of different factors.