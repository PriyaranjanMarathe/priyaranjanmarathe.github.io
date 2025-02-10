---
layout: default
title: "BOT"
---

<h1>Best of Twitter</h1>
Thanks [Alexy Guzey](https://guzey.com/best-of-twitter/) for the inspiration for these pages.
<ul>
  {% for post in site.categories.bos %}
    <li>
      <a href="{{ post.url }}">{{ post.title }}</a>
      <span>{{ post.date | date: "%b %-d, %Y" }}</span>
    </li>
  {% endfor %}
</ul>