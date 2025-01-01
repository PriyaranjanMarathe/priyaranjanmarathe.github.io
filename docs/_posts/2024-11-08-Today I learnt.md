---
layout: "default"
title: "Today I learnt"
date: "2024-09-29"
comments: true
categories: "jekyll update"
---

I am collating list of "Today I learnt(TIL)" [here](https://priyaranjanmarathe.github.io/til.html).

<ul>
  {% if site.til and site.til.size > 0 %}
  {% assign sorted_posts = site.til | sort: 'date' | reverse %}
  {% for post in sorted_posts %}
    <li>
      <a href="{{ site.baseurl }}{{ post.url }}">{{ post.title }}</a> - 
      <em>{{ post.date | date: "%B %d, %Y" }}</em>
    </li>
  {% endfor %}
{% else %}
  <p>No TIL posts available yet.</p>
{% endif %}
</ul>
