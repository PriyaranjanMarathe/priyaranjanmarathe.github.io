---
layout: "default"
title: "Today I learnt"
date: "2024-09-29"
comments: true
categories: "jekyll update"
---

I am collating list of "Today I learnt(TIL)" [here](https://priyaranjanmarathe.github.io/marathe/til.html).

<ul>
  {% for post in site.til %}
    <li>
      <a href="{{ site.baseurl }}{{ post.url }}">{{ post.title }}</a> - 
      <em>{{ post.date | date: "%B %d, %Y" }}</em>
    </li>
  {% endfor %}
</ul>
