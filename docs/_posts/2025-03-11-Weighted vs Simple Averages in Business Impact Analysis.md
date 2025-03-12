---
layout: "default"
title: "Weighted vs Simple Averages"
comments: true
date: "2025-03-11"
categories: tils
---

# TIL: Weighted vs Simple Averages

## 💡 TIL
Simple averages can be misleading when analyzing hospital mortality rates. Using sample sizes (patient counts) as weights provides a more statistically sound approach, especially when dealing with varying sample sizes.

## 🎯 Quick Example: Hospital Mortality Rate Analysis

```python
# Hospital Death Rates
# Format: Deaths/Total_Patients = Rate (Weight = Total_Patients)
City_Hospital_A:    15/1000 = 1.5%  (weight: 1000) # Each patient counts equally
City_Hospital_B:    25/1500 = 1.7%  (weight: 1500) # Larger sample = more influence
Rural_Clinic_A:     2/50   = 4.0%   (weight: 50)   # Smaller sample = less influence
Rural_Clinic_B:     1/30   = 3.3%   (weight: 30)   # Smallest sample = least influence

# Why using patient counts as weights makes sense:
# 1. Each patient contributes equally to the overall average
# 2. Automatically adjusts for sample size differences
# 3. Gives proper statistical weight to larger, more reliable samples

Simple Average:   (1.5% + 1.7% + 4.0% + 3.3%) / 4 = 2.63%
Weighted Average: (1.5×1000 + 1.7×1500 + 4.0×50 + 3.3×30) / (1000+1500+50+30) = 1.69%
```

## 🔑 Key Points
- Using patient counts as weights ensures each patient contributes equally
- Larger samples naturally get more weight, aligning with statistical principles
- Weights reflect the reliability of each data point
- Law of Large Numbers suggests larger samples are more reliable

## 📊 Formula and Explanation
```
Weighted_Avg = Σ(Rate × Count) / Σ(Count)

This is equivalent to:
Total_Deaths / Total_Patients = (15+25+2+1) / (1000+1500+50+30)
```

## 💭 Why Count-Based Weights Matter
1. Statistical Validity: 
   - Larger samples provide more reliable estimates
   - Each individual observation has equal influence
2. Intuitive Results:
   - The weighted average (1.69%) represents the true overall death rate
   - Simple average (2.63%) overrepresents small clinics
3. Practical Applications:
   - Population studies
   - Quality metrics
   - Resource allocation decisions

## 📈 Sample Size Impact
```python
Small Sample (Rural):  80 patients → Higher variance
Large Sample (City): 2500 patients → More stable rates
Total Coverage:     2580 patients → Weighted rate more reliable
```