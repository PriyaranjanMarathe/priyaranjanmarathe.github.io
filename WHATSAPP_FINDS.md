# Saved Finds — Meta WhatsApp setup

Forward a single item to the connected Meta WhatsApp number, then use WhatsApp **Reply** on that item and send `save #science #history`. Reply context is required: an unquoted `save` deliberately publishes nothing. This selects the exact message even when webhooks arrive out of order. Send the reply within 24 hours; use the same configured owner phone. Groups are never read automatically.

Explicit tags win. Bare `save` suggests tags with English keyword rules; unmatched items become `untagged`. Marathi and other languages are preserved; use your own hashtags for reliable tagging. Images are not OCRed and audio/video are not transcribed. Public text is escaped, and embedded URLs are linked but never fetched. Source authorship and factual claims are not verified.

## Architecture

Meta sends signed webhooks to `https://saved-finds-receiver.vercel.app/api/webhook`. The Node receiver verifies the raw-body HMAC, account, phone ID, capture cutoff and owner number, and stores normalized message records in a **private** Vercel Blob store. Delivery retries use deterministic hashed names. No raw message bodies or credentials are logged by the application. The private `/api/inbox` endpoint requires a random bearer token and sends no cacheable responses.

GitHub Actions polls hourly, applies explicit reply selection with a two-minute settling interval, and commits only selected items to `gh-pages` under `docs/finds`. Existing public IDs deduplicate publications. A failed run makes no commit. Inbox reads remove entries older than 24 hours; outages or a paused importer delay cleanup. Delayed imports may miss expired entries. Media downloads use the Meta token, verify checksums when supplied, and allow JPEG, PNG, GIF, WebP, PDF, MP4, MP3, Ogg and M4A up to 20 MB each. Unsupported media fails safely for investigation.

Only select material intended for public sharing. Text or attachments may themselves contain personal information. Deletion from the page does not erase Git history. See `/finds/privacy/`.

## Configuration

Vercel production environment: `META_APP_SECRET`, `META_VERIFY_TOKEN`, `INBOX_READ_TOKEN`, `WHATSAPP_OWNER` (digits only), `META_WABA_ID`, `META_PHONE_ID`, `CAPTURE_START`; connected private Blob store with OIDC supplies `BLOB_STORE_ID`. The Meta access token is not needed in Vercel.

GitHub encrypted Actions secrets: `INBOX_READ_TOKEN` and `META_ACCESS_TOKEN` (used only for selected media). Variables: `WHATSAPP_INBOX_URL`, `META_GRAPH_VERSION`, `WHATSAPP_CAPTURE_START`, `WHATSAPP_ENABLED=true`. Keep `WHATSAPP_AUTOPUBLISH=false` until a real publishing test passes. Temporary Meta access tokens expire; configure a suitable system-user token before relying on media automation.

Configure Meta webhook callback URL and matching verify token, subscribe to `messages`, and ensure the app is subscribed to the WABA. Complete Meta’s publishing requirements. No paid Vercel plan or outgoing WhatsApp messaging is required by this code. Provider quotas still apply; Hobby storage can pause at its free limits. Hourly polling uses fewer list operations than the earlier 15-minute Twilio design.

The workflow must exist on default branch `main` for the schedule and uses checkout `gh-pages` for the site. It requests a Pages build explicitly after publication. Public repo schedules may stop after prolonged inactivity. GitHub may delay scheduled runs.

## Validation

`python3 -m unittest discover -s tests -v`

`cd receiver && npm ci && npm test`

Start with a manual workflow preview, then publish a deliberately selected test item and verify the rendered page. The old Twilio importer remains for reference but is not invoked by the workflow.

Sources: [Vercel private Blob](https://vercel.com/docs/vercel-blob/private-storage), [Vercel Blob limits](https://vercel.com/docs/vercel-blob/usage-and-pricing), [Meta Cloud API](https://developers.facebook.com/docs/whatsapp/cloud-api), [Simon Willison’s link blog](https://simonwillison.net/2024/Dec/22/link-blog/).
