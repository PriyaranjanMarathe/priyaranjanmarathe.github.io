---
layout: default
title: "TILS"
---
<h1>{{ page.title }}</h1>
<p>These pages are inspired by:</p>
1. [Scott Hanselman on "Do they deserve the gift of your keystrokes?"](https://www.hanselman.com/blog/do-they-deserve-the-gift-of-your-keystrokes)
2. [Simon Willison on why he creates a new TIL if he had to open ten tabs to solve a problem](https://x.com/simonw/status/1855259241952727350)
<ul>
  {% for post in site.categories.tils %}
    <li>
      <a href="{{ post.url }}">{{ post.title }}</a>
      <span>{{ post.date | date: "%b %-d, %Y" }}</span>
    </li>
  {% endfor %}
</ul>

