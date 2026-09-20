export default {
  async fetch(request, env) {
    if (!['GET', 'HEAD'].includes(request.method)) return new Response('Method not allowed', {status:405, headers:{Allow:'GET, HEAD'}});
    const key = new URL(request.url).pathname.slice(1);
    if (!/^media\/[a-f0-9]{24}\.(jpg|png|webp|gif|pdf|mp4|ogg|mp3|m4a)$/.test(key)) return new Response('Not found', {status:404});
    const object = await env.MEDIA.head(key);
    if (!object) return new Response('Not found', {status:404});
    const headers = new Headers();
    object.writeHttpMetadata(headers);
    headers.set('ETag', object.httpEtag);
    headers.set('X-Content-Type-Options', 'nosniff');
    headers.set('Accept-Ranges', 'bytes');
    headers.set('Cache-Control', 'public, max-age=31536000, immutable');
    if (request.headers.get('If-None-Match') === object.httpEtag) return new Response(null, {status:304, headers});
    let start = 0, end = object.size - 1, status = 200;
    const range = request.headers.get('Range');
    if (range && request.method === 'GET' && (!request.headers.has('If-Range') || request.headers.get('If-Range') === object.httpEtag)) {
      const match = /^bytes=(\d*)-(\d*)$/.exec(range);
      if (match && (match[1] || match[2])) {
        start = match[1] ? Number(match[1]) : Math.max(0, object.size - Number(match[2]));
        end = match[1] && match[2] ? Math.min(Number(match[2]), end) : end;
      } else start = object.size;
      if (start > end || start >= object.size) return new Response(null, {status:416, headers:{'Content-Range':`bytes */${object.size}`}});
      status = 206;
      headers.set('Content-Range', `bytes ${start}-${end}/${object.size}`);
    }
    headers.set('Content-Length', String(end - start + 1));
    if (request.method === 'HEAD') return new Response(null, {headers});
    const result = await env.MEDIA.get(key, status === 206 ? {range:{offset:start, length:end-start+1}} : undefined);
    if (!result) return new Response('Not found', {status:404});
    return new Response(result.body, {status, headers});
  }
};
