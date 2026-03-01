# Ranjan's Blog

Minimal static blog. Each post is a single HTML file.

## Structure

```
/
├── index.html          # Homepage with search + tags
├── about.html          # About page
├── feed.xml            # RSS feed
├── posts/
│   ├── _template.html  # Copy this for new posts
│   └── *.html          # Your posts
└── README.md           # This file
```

## Posting from iPhone

### Method 1: Claude + GitHub App (Recommended)

1. **In Claude app**, say:
   ```
   Write me a blog post about [YOUR TOPIC].
   Use my blog template format with these tags: [tag1, tag2]
   ```

2. **Copy the HTML** Claude generates

3. **Open GitHub app**:
   - Go to this repo
   - Navigate to `posts/`
   - Tap "+" to create new file
   - Name it: `your-post-slug.html`
   - Paste the HTML
   - Commit

4. **Update index.html**:
   - Open `index.html` in GitHub app
   - Add new post entry (copy existing format)
   - Commit

5. **Done!** GitHub Pages deploys automatically.

### Method 2: Working Copy App

If you post frequently, the Working Copy app ($25) gives you:
- Full Git client on iPhone
- Edit files with syntax highlighting
- Easier multi-file commits

## Adding a New Post Manually

1. Copy `posts/_template.html`
2. Replace these placeholders:
   - `POST_TITLE` - Your post title
   - `POST_DATE` - e.g., "January 21, 2026"
   - `POST_SLUG` - URL-friendly name (e.g., "my-first-post")
   - `POST_EXCERPT` - One sentence summary
   - `TAG1`, `TAG2` - Your tags

3. Add entry to `index.html`:
   ```html
   <li class="post-item" data-tags="tag1,tag2" data-title="your title lowercase" data-content="searchable content">
       <div class="post-date">January 21, 2026</div>
       <h2 class="post-title"><a href="/posts/your-slug.html">Your Title</a></h2>
       <p class="post-excerpt">One sentence description.</p>
       <div class="post-tags">
           <span class="tag">tag1</span>
           <span class="tag">tag2</span>
       </div>
   </li>
   ```

4. (Optional) Add to `feed.xml` for RSS subscribers

## Claude Prompt for New Posts

Copy this prompt and customize:

```
Write me a complete HTML blog post for my static blog.

Topic: [YOUR TOPIC HERE]
Tags: [tag1, tag2]

Use this exact structure:
- Embedded CSS (dark mode support)
- Header with: site link, date, title, tags
- Article with my content
- Footer navigation back to index

Style: conversational, clear, no fluff
Length: [short/medium/long]

Output the complete HTML file I can save directly.
```

## Features

- **Search**: Filters posts by title and content
- **Tags**: Click to filter by tag
- **Dark mode**: Automatic based on system preference
- **RSS**: `feed.xml` for subscribers
- **Fast**: No JavaScript frameworks, ~5KB per page
- **Mobile-first**: Readable on any device

## Customization

Edit the CSS in `index.html` to change:
- `--accent`: Link color
- `--text`: Body text color
- `font-family`: Change the font
- `max-width`: Content width (640px default)

## Deployment

This repo is configured for GitHub Pages:
- Push to `main` branch
- Site updates automatically
- URL: https://ranjanmarathe.github.io/
