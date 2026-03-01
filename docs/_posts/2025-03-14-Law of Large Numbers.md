---
layout: "default"
title: "The Law of Large Numbers"
comments: true
date: "2025-03-14"
categories: tils

---

# TIL: Law of Large Numbers

## 💡 TIL
The Law of Large Numbers states that as the sample size increases, the sample mean tends to get closer to the true population mean. This fundamental principle explains why larger datasets generally provide more reliable statistical insights.

## 🎯 Quick Example: Coin Flip Probability

```python
import random

# Simulated coin flips at different sample sizes
small_sample  = 10    # Highly variable
medium_sample = 1000  # More stable
large_sample  = 10000 # Very stable

# Results (Heads Percentage)
# Small Sample (10 flips):
heads = 7
print(f"10 flips: {(heads/small_sample)*100:.1f}% heads")    # 70.0% (far from 50%)

# Medium Sample (1000 flips):
heads = 487
print(f"1000 flips: {(heads/medium_sample)*100:.1f}% heads") # 48.7% (closer to 50%)

# Large Sample (10000 flips):
heads = 5024
print(f"10000 flips: {(heads/large_sample)*100:.1f}% heads") # 50.2% (very close to 50%)

# Expected probability: 50%
```

## 🔑 Key Points
1. Sample Size Effect:
   - Small samples: High variance, unreliable estimates
   - Large samples: Lower variance, more reliable estimates
   - Very large samples: Converge toward true probability

2. Real-world Applications:
   - Insurance risk assessment
   - Quality control in manufacturing
   - Medical trial outcomes
   - Survey accuracy estimation

## 📊 Formula
```
P(|X̄ₙ - μ| < ε) → 1 as n → ∞

Where:
- X̄ₙ is the sample mean
- μ is the true population mean
- ε is any small positive number
- n is the sample size
```

## 💭 Why It Matters
1. Research Design:
   - Helps determine appropriate sample sizes
   - Guides statistical power calculations
   - Informs confidence level estimations

2. Business Applications:
   - A/B testing sample size requirements
   - Customer satisfaction survey design
   - Risk assessment in financial models

## 📈 Visual Example: Convergence

```python
# Convergence of dice rolls to expected value (3.5)
sample_sizes = [10, 100, 1000, 10000]
results = {
    10:    3.9,  # High variance
    100:   3.58, # Getting closer
    1000:  3.52, # Very close
    10000: 3.51  # Almost exact
}

# Expected value of a fair die: (1+2+3+4+5+6)/6 = 3.5
```

## 🏥 Healthcare Example
Consider mortality rates in hospitals:

```python
# Small Rural Hospital
cases = 50
deaths = 2
mortality_rate = 4.0%  # High variance!

# Large City Hospital
cases = 5000
deaths = 175
mortality_rate = 3.5%  # More reliable estimate

# Key Insight: The larger hospital's rate is more likely 
# to reflect the true mortality rate for similar cases
```

## 📚 Best Practices
1. Sample Size Planning:
   - Calculate minimum required sample sizes
   - Account for expected effect sizes
   - Consider practical constraints

2. Interpretation Guidelines:
   - Always report sample sizes
   - Include confidence intervals
   - Acknowledge limitations of small samples

3. Common Pitfalls to Avoid:
   - Overconfidence in small sample results
   - Ignoring population variability
   - Neglecting practical significance

## 🔍 Related Concepts
- Central Limit Theorem
- Standard Error of the Mean
- Confidence Intervals
- Statistical Power

## 📝 Note
While larger samples are generally better, practical constraints often limit sample sizes. The key is finding the balance between statistical reliability and resource constraints.