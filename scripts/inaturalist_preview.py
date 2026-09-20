"""Observation previews reference external photos; never copy image bytes."""
import re
from urllib.parse import urlsplit, urlunsplit
import requests

LICENSES = {'cc0', 'cc-by', 'cc-by-sa', 'cc-by-nd', 'cc-by-nc', 'cc-by-nc-sa', 'cc-by-nc-nd'}
PHOTO_HOSTS = {'static.inaturalist.org', 'inaturalist-open-data.s3.amazonaws.com'}


def observation_ids(body):
    ids = []
    for url in re.findall(r'https?://[^\s<>]+', body):
        parsed = urlsplit(url.rstrip(').,;]'))
        if parsed.hostname not in {'inaturalist.org', 'www.inaturalist.org', 'm.inaturalist.org'} or parsed.username or parsed.password:
            continue
        match = re.fullmatch(r'/observations/(\d+)/?', parsed.path)
        if match and match[1] not in ids:
            ids.append(match[1])
    return ids[:3]


def fetch_preview(observation_id):
    response = requests.get(f'https://api.inaturalist.org/v1/observations/{observation_id}',
                            headers={'User-Agent':'SavedFinds/1.0 (+https://priyaranjanmarathe.github.io/finds/)'},
                            timeout=20, allow_redirects=False)
    if response.status_code == 404: return None
    response.raise_for_status()
    observations = response.json().get('results', [])
    if not observations: return None
    observation = observations[0]
    if str(observation.get('id')) != observation_id: raise ValueError('Observation mismatch')
    taxon = observation.get('taxon') or {}
    title = taxon.get('preferred_common_name') or taxon.get('name') or observation.get('species_guess') or 'iNaturalist observation'
    for photo in observation.get('photos', []):
        license_code = photo.get('license_code')
        if photo.get('hidden') or license_code not in LICENSES: continue
        parsed = urlsplit(photo.get('url', ''))
        if parsed.scheme != 'https' or parsed.hostname not in PHOTO_HOSTS or parsed.username or parsed.password: continue
        if not re.fullmatch(r'/photos/\d+/square\.(jpg|jpeg|png)', parsed.path): continue
        image_url = urlunsplit((parsed.scheme, parsed.netloc, parsed.path.replace('/square.', '/large.'), '', ''))
        return {'source':'inaturalist', 'url':f'https://www.inaturalist.org/observations/{observation_id}',
                'image_url':image_url, 'title':str(title)[:200], 'attribution':str(photo.get('attribution') or '')[:500],
                'observer':str((observation.get('user') or {}).get('login') or '')[:100], 'license':license_code,
                'photo_url':f'https://www.inaturalist.org/photos/{photo["id"]}'}
    return None


def enrich(records):
    budget = 20
    for record in records:
        if 'link_previews' in record: continue
        ids = observation_ids(record.get('body', '') + '\n' + record.get('note', ''))
        if not ids: continue
        if budget < len(ids): break
        budget -= len(ids)
        try:
            record['link_previews'] = [preview for identifier in ids if (preview := fetch_preview(identifier))]
        except (requests.RequestException, ValueError, KeyError, TypeError):
            # The original post still publishes. A later scheduled run retries enrichment.
            print('::warning::iNaturalist preview unavailable; original link retained and preview will retry.')
