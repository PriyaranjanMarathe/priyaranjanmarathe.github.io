---
layout: "default"
title: "WhatsApp Chat Analysis"
comments: true
date: "2025-07-08"
categories: tils
---

# WhatsApp Chat Analysis

## 1️⃣ Source of the Idea

Inspired by:

- [Marginal Revolution: “Analyzing my text messages with my ex-boyfriend”](https://marginalrevolution.com/marginalrevolution/2024/06/analyzing-my-text-messages-with-my-ex-boyfriend.html)

Idea: systematically analyze personal/group chats for:

- Message activity patterns
- Sentiment over time
- Keyword and emoji usage
- Visual insights on group dynamics

## 2️⃣ Work Done to Create & Share on Colab

✅ Parsed WhatsApp export (`_chat.txt`) using robust regex supporting multi-line messages.  
✅ Anonymized participant names for privacy while retaining analysis.  
✅ Performed sentiment analysis using VADER (NLTK).  
✅ Generated visualizations:

- Activity heatmap (hour vs. weekday)
- Average sentiment by user
- Top emojis used
- Word cloud of most frequent words

✅ Packaged these analyses into a clean, reusable Python notebook.  
✅ Uploaded and shared via Google Colab for ease of:

- Running without local setup
- Visual exploration
- Sharing with collaborators

🔗 **[Open WhatsApp Chat Analysis on Colab](https://colab.research.google.com/drive/1B4IAJsA8f8BJyF4VRrJNmZPXgj1UVeO6?usp=sharing)**
