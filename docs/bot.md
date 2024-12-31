---
layout: default
title: "BOT"
---

<h1>Best of Twitter</h1>
Thanks [Alexy Guzey](https://guzey.com/best-of-twitter/) for the inspiration for these pages.
<ul>
  {% if site.bot and site.bot.size > 0 %}
  {% assign sorted_posts = site.bot | sort: 'date' | reverse %}
  {% for post in sorted_posts %}
    <li>
      <a href="{{ site.baseurl }}{{ post.url }}">{{ post.title }}</a> - 
      <em>{{ post.date | date: "%B %d, %Y" }}</em>
    </li>
  {% endfor %}
{% else %}
  <p>No Best of Twitter posts available yet.</p>
{% endif %}

</ul>
