"""Upload a finished video to YouTube.
Usage: python upload_youtube.py out/<name>  [--privacy public|unlisted|private] [--publish-at 2026-10-13T18:30:00Z]
Reads out/<name>/meta.json  {"title","description","tags":[...],"categoryId":"28"} plus video.mp4 and thumbnail.jpg.
Needs env YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN (scope youtube.upload) and network access to
oauth2.googleapis.com + www.googleapis.com. Writes out/<name>/upload.json with the video id/url."""
import json, os, sys, argparse, requests
ap=argparse.ArgumentParser();ap.add_argument('dir');ap.add_argument('--privacy',default=os.environ.get('YT_PRIVACY','public'));ap.add_argument('--publish-at')
A=ap.parse_args();D=A.dir;meta=json.load(open(f'{D}/meta.json'))
for k in ('YT_CLIENT_ID','YT_CLIENT_SECRET','YT_REFRESH_TOKEN'):
    if not os.environ.get(k): sys.exit(f'missing env {k}: add it in the environment settings')
tok=requests.post('https://oauth2.googleapis.com/token',data={'client_id':os.environ['YT_CLIENT_ID'],'client_secret':os.environ['YT_CLIENT_SECRET'],
    'refresh_token':os.environ['YT_REFRESH_TOKEN'],'grant_type':'refresh_token'},timeout=60)
tok.raise_for_status();H={'Authorization':'Bearer '+tok.json()['access_token']}
status={'privacyStatus':'private' if A.publish_at else A.privacy,'selfDeclaredMadeForKids':False,'containsSyntheticMedia':True}
if A.publish_at: status['publishAt']=A.publish_at
body={'snippet':{'title':meta['title'][:100],'description':meta['description'][:4900],'tags':meta.get('tags',[])[:30],
      'categoryId':meta.get('categoryId','25'),'defaultLanguage':'hi','defaultAudioLanguage':'hi'},'status':status}
size=os.path.getsize(f'{D}/video.mp4')
r=requests.post('https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status',
    headers={**H,'Content-Type':'application/json; charset=UTF-8','X-Upload-Content-Type':'video/mp4','X-Upload-Content-Length':str(size)},json=body,timeout=60)
r.raise_for_status();url=r.headers['Location']
with open(f'{D}/video.mp4','rb') as f:
    up=requests.put(url,headers={**H,'Content-Type':'video/mp4','Content-Length':str(size)},data=f,timeout=3600)
up.raise_for_status();vid=up.json()['id'];res={'id':vid,'url':f'https://youtu.be/{vid}','status':up.json().get('status',{})}
try:
    with open(f'{D}/thumbnail.jpg','rb') as f:
        t=requests.post(f'https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={vid}',headers={**H,'Content-Type':'image/jpeg'},data=f,timeout=120)
    res['thumbnail']='ok' if t.ok else f'failed {t.status_code}: {t.text[:200]} (custom thumbnails need a phone-verified channel)'
except Exception as e: res['thumbnail']=f'failed: {e}'
json.dump(res,open(f'{D}/upload.json','w'),indent=1);print(json.dumps(res,indent=1))
