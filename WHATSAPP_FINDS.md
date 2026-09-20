# Save selected WhatsApp forwards

Forward one item to the Twilio sandbox, then send `save #science #history` within ten minutes. Each save selects exactly the immediately preceding incoming message from your configured number. Repeat for each item. To save plain text or a URL you can also paste it into the sandbox chat, followed by `save`. This does not read your groups or recover the original author's identity.

Explicit tags win. Bare `save` uses a small English keyword taxonomy; unmatched text is `untagged`. Suggested tags are visibly labeled and are not guaranteed correct. Marathi and other languages are preserved; supply your own hashtags for reliable categorization. Images are not OCRed, and audio/video are not transcribed. Edit `docs/finds/finds.json` and call `render` to correct saved tags.

The public `/finds/` page supports text search, tag filters, source links contained in the forward, stable item anchors and common attachments. The original text is preserved as quoted material, with no claim that its authorship or factual assertions are verified. Sender numbers and Twilio account identifiers are not written to the public records; personal details present inside the forwarded content itself are preserved. Only select items you intend to make public. Git history retains published content even if later removed from the page.

## Activate after a real preview test

1. Merge the feature into `gh-pages`, the site's existing publishing branch. Also install `.github/workflows/whatsapp-finds.yml` on `main`, because GitHub only schedules workflows from the default branch. Keep `WHATSAPP_ENABLED` unset until configuration is ready.
2. In repository Actions secrets, set `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `WHATSAPP_OWNER` (your phone, `whatsapp:+countrycode...`) and `WHATSAPP_SANDBOX` (the console's sandbox number in the same format). Enter credentials directly into GitHub, not into source code or chat.
For a restricted API key, use US1 and grant Read/List on `messages` and `messages.media` only. Store `TWILIO_API_KEY_SID` and `TWILIO_API_KEY_SECRET` in Actions secrets; these take precedence over the Auth Token. The account SID is still required.

3. Set Actions variable `WHATSAPP_CAPTURE_START` to the UTC instant at which you want capture to begin, e.g. `2026-09-20T18:00:00Z`. No historical items before this instant are eligible. Set `WHATSAPP_ENABLED=true` to allow manual tests. Keep `WHATSAPP_AUTOPUBLISH` unset during testing.
4. Sign in to Twilio, confirm the correct account and sandbox, join it from your phone, and send a harmless test URL followed by `save #test`. Rejoin every three days. Twilio documents the sandbox as testing-only and charges standard messaging rates; use a registered sender for ongoing production use.
5. Run “Save WhatsApp finds” manually with `publish=false` first. This retrieves messages but reports only selected counts and makes no files/commits. After confirming the count, run with `publish=true` and verify the item and any attachments at `/finds/` after the Pages build finishes.
6. Set `WHATSAPP_AUTOPUBLISH=true` once the real publishing test passes and public automation is desired. The schedule requests a run every 15 minutes, but GitHub can delay runs. A public repository's schedule can be disabled after 60 days without activity. Disable capture at any time by setting `WHATSAPP_ENABLED=false`.

The importer reads Twilio's Messages API; no new webhook/server is required, and the existing sandbox webhook is not modified. If the old health tracker is active, it may still receive/reply to these messages. Check its routing before regular use. The sandbox cannot automatically access your existing WhatsApp groups.

## Reliability and limits

Messages are paginated from the capture date, with repeated message IDs deduplicated using a hash. A failed import does not commit any part of that run. Media downloads require complete API results and are limited to 20 MB per attachment; unsupported types fail the run for investigation. Supported formats: JPEG, PNG, WebP, GIF, PDF, MP4 video, Ogg, MP3 and M4A audio. Content URLs supplied inside forwards are displayed, never fetched by the importer.

The workflow explicitly requests a legacy Pages rebuild because commits made by GITHUB_TOKEN do not themselves start a Pages build. That API step and actual Twilio access must be verified on the first live run. Git push conflicts fail safely for a later retry. The pipeline stores only selected material publicly and does not send any WhatsApp replies.

## Validation

`python -m pip install requests==2.32.5`

`python -m unittest discover -s tests -v`

Sources: [Twilio Sandbox](https://www.twilio.com/docs/whatsapp/sandbox), [Messages API](https://www.twilio.com/docs/messaging/api/message-resource), [Media API](https://www.twilio.com/docs/messaging/api/media-resource), [GitHub scheduling](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule), [Simon Willison's link blog](https://simonwillison.net/2024/Dec/22/link-blog/).
