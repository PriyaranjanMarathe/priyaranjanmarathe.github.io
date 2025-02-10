---
layout: "default"
title: "Best of Twitter (Social)."
comments: true
date: "2024-09-08"
categories: "bos"
---

I am collating list of "best of twitter, social really" for the week [here](https://priyaranjanmarathe.github.io/bot.html).

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
