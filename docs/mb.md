---
layout: default
title: "mbs"
---
<h1>{{ page.title }}</h1>
<p>Microblogging/link blogs can be fun and handy to record random thoughts. Inspired by the Scott and Simom again :)</p>
1. [Micro.blog and owning your words with Manton Reece
](https://hanselminutes.com/983/microblog-and-owning-your-words-with-manton-reece/RK=2/RS=6R_oNCTRzAclKt_yGmb8AexeTDw-)
2. [Simon Willison on linked blogs](https://kottke.org/25/01/0045988-simon-willison-shares-his/RK=2/RS=Ur9pOX29BHGF8F4_1w4HhizGq5c-)
<ul>
  {% for post in site.categories.mb %}
    <li>
      <a href="{{ post.url }}">{{ post.title }}</a>
      <span>{{ post.date | date: "%b %-d, %Y" }}</span>
    </li>
  {% endfor %}
</ul>

