---
layout: default
title: "TIL"
---

<!-- <h1>{{ page.title }}</h1>
<p>These pages are inspired by:</p>
1. [Scott Hanselman on "Do they deserve the gift of your keystrokes?"](https://www.hanselman.com/blog/do-they-deserve-the-gift-of-your-keystrokes)
2. [Simon Willison on why he creates a new TIL if he had to open ten tabs to solve a problem](https://x.com/simonw/status/1855259241952727350)

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

</ul> -->
<!-- ---
layout: default
title: "Tils Posts"
--- -->

<h1>Posts in the "tils" Category</h1>
<ul>
  {% for post in site.categories.tils %}
    <li>
      <a href="{{ post.url }}">{{ post.title }}</a>
      <span>{{ post.date | date: "%b %-d, %Y" }}</span>
    </li>
  {% endfor %}
</ul>

