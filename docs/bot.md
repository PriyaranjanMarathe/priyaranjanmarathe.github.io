---
layout: default
title: "BOT"
---

<h1>Best of Twitter</h1>
Thanks [Alexy Guzey](https://guzey.com/best-of-twitter/) for the inspiration for these pages.
<ul>
  {% for post in site.bot %}
    <li>
      <a href="{{ site.baseurl }}{{ post.url }}">{{ post.title }}</a> - 
      <em>{{ post.date | date: "%B %d, %Y" }}</em>
    </li>
  {% endfor %}
</ul>
