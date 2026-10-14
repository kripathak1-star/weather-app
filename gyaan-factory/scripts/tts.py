"""Voice for every scene of a plan.
Usage: python tts.py plan.json workdir
Uses ElevenLabs (ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID) when set and reachable, else the free offline Hindi voice (Piper 'pratham').
Writes workdir/l{i}.wav, workdir/durs.json, workdir/words.json (per-scene word timings of the spoken Hindi text)."""
import json, os, sys, base64, re, io, subprocess, numpy as np, soundfile as sf
plan=json.load(open(sys.argv[1])); W=sys.argv[2]; os.makedirs(W,exist_ok=True)
KEY=os.environ.get('ELEVENLABS_API_KEY'); VOICE=os.environ.get('ELEVENLABS_VOICE_ID')
MODEL=os.environ.get('ELEVENLABS_MODEL','eleven_multilingual_v2')
HERE=os.path.dirname(os.path.abspath(__file__))
def words_from_chars(text,chars,starts,ends):
    out=[];cur='';t0=None;t1=None
    for c,s,e in zip(chars,starts,ends):
        if c.isspace():
            if cur: out.append({'w':cur,'t':t0,'e':t1}); cur=''
            continue
        if not cur: t0=s
        cur+=c; t1=e
    if cur: out.append({'w':cur,'t':t0,'e':t1})
    return out
def eleven(text):
    import requests
    r=requests.post(f'https://api.elevenlabs.io/v1/text-to-speech/{VOICE}/with-timestamps?output_format=mp3_44100_128',
        headers={'xi-api-key':KEY,'Content-Type':'application/json'},
        json={'text':text,'model_id':MODEL,'voice_settings':{'stability':0.4,'similarity_boost':0.75,'style':0.4,'use_speaker_boost':True}},timeout=180)
    r.raise_for_status(); j=r.json()
    mp3=base64.b64decode(j['audio_base64'])
    wav=subprocess.run(['ffmpeg','-loglevel','error','-i','-','-ac','1','-ar','44100','-f','wav','-'],input=mp3,capture_output=True,check=True).stdout
    a,sr=sf.read(io.BytesIO(wav)); al=j.get('alignment') or j.get('normalized_alignment')
    return a,sr,words_from_chars(text,al['characters'],al['character_start_times_seconds'],al['character_end_times_seconds'])
_piper=None
def piper(text):
    global _piper
    import sherpa_onnx
    if _piper is None:
        d=os.path.join(HERE,'..','models','vits-piper-hi_IN-pratham-medium')
        _piper=sherpa_onnx.OfflineTts(sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(vits=sherpa_onnx.OfflineTtsVitsModelConfig(model=f'{d}/hi_IN-pratham-medium.onnx',tokens=f'{d}/tokens.txt',data_dir=f'{d}/espeak-ng-data'),num_threads=4)))
    g=_piper.generate(text,sid=0,speed=1.1); return np.array(g.samples),g.sample_rate,None
use_eleven=bool(KEY and VOICE); engine='elevenlabs' if use_eleven else 'piper'
durs=[];words=[]
for i,sc in enumerate(plan['scenes']):
    text=sc['voice']
    try:
        a,sr,wd=eleven(text) if use_eleven else piper(text)
    except Exception as e:
        print('ElevenLabs failed, falling back to free voice:',e,file=sys.stderr); use_eleven=False; engine='piper(fallback)'; a,sr,wd=piper(text)
    th=np.abs(a).max()*.02; idx=np.where(np.abs(a)>th)[0]; s0=max(0,idx[0]-int(.03*sr)); a=a[s0:min(len(a),idx[-1]+int(.1*sr))]
    if wd: wd=[{'w':w['w'],'t':round(w['t']-s0/sr,3),'e':round(w['e']-s0/sr,3)} for w in wd]
    sf.write(f'{W}/l{i}.wav',a,sr); durs.append(len(a)/sr); words.append(wd)
json.dump(durs,open(f'{W}/durs.json','w')); json.dump(words,open(f'{W}/words.json','w'),ensure_ascii=False)
json.dump({'engine':engine},open(f'{W}/tts_info.json','w'))
print('voice:',engine,'total',round(sum(durs),1),'s')
