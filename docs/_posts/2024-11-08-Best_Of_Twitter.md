---
layout: "default"
title: "Best of Twitter (Social)."
comments: true
date: "2024-09-08"
categories: "jekyll update"
---

I am collating list of "best of twitter, social really" for the week [here](https://priyaranjanmarathe.github.io/marathe/bot.html).

<ul>
  {% for post in site.bot %}
    <li>
      <a href="{{ site.baseurl }}{{ post.url }}">{{ post.title }}</a> - 
      <em>{{ post.date | date: "%B %d, %Y" }}</em>
    </li>
  {% endfor %}
</ul>
