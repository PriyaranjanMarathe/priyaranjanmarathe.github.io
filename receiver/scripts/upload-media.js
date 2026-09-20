import { put, list } from '@vercel/blob';
import { createReadStream } from 'node:fs';
try {
  const [file, pathname, contentType] = process.argv.slice(2);
  if (file === '--usage') {
    let cursor, bytes = 0;
    do {
      const page = await list({token:process.env.BLOB_MEDIA_READ_WRITE_TOKEN, limit:1000, cursor});
      bytes += page.blobs.reduce((sum, blob) => sum + blob.size, 0);
      cursor = page.hasMore ? page.cursor : undefined;
    } while (cursor);
    process.stdout.write(JSON.stringify({bytes}));
  } else {
  if (!/^media\/[a-f0-9]{24}\.(jpg|png|webp|gif|pdf|mp4|ogg|mp3|m4a)$/.test(pathname)) throw new Error();
  const blob = await put(pathname, createReadStream(file), {access:'public', token:process.env.BLOB_MEDIA_READ_WRITE_TOKEN,
    addRandomSuffix:false, allowOverwrite:true, contentType, cacheControlMaxAge:31536000});
  process.stdout.write(JSON.stringify({url:blob.url}));
  }
} catch { process.stderr.write('Media upload failed'); process.exitCode=1; }
