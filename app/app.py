import json, os, sqlite3, urllib.request, urllib.error, shutil, time
from pathlib import Path
from datetime import datetime, timezone
from flask import Flask, jsonify, request, send_from_directory, Response

APP_VERSION="1"
DATA=Path('/app/data')
DB=DATA/'app.sqlite'
BACKUPS=DATA/'backups'
SPOOLMAN_URL=os.getenv('SPOOLMAN_URL','').rstrip('/')
SPOOLMAN_PUBLIC_URL=os.getenv('SPOOLMAN_PUBLIC_URL',SPOOLMAN_URL).rstrip('/')
APP_URL=os.getenv('APP_URL','').rstrip('/')
ALLOWED_ORIGIN=os.getenv('PWA_ALLOWED_ORIGIN','').rstrip('/')
BACKUP_KEEP=max(1,int(os.getenv('BACKUP_KEEP','50')))
PROXY_TIMEOUT=max(2,float(os.getenv('SPOOLMAN_TIMEOUT','8')))
SPOOLMAN_CF_ID=os.getenv('SPOOLMAN_CF_CLIENT_ID','')
SPOOLMAN_CF_SECRET=os.getenv('SPOOLMAN_CF_CLIENT_SECRET','')

app=Flask(__name__, static_folder='static', static_url_path='')

def now(): return datetime.now(timezone.utc).isoformat()
def conn():
    DATA.mkdir(parents=True,exist_ok=True); BACKUPS.mkdir(parents=True,exist_ok=True)
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row
    c.execute('PRAGMA journal_mode=WAL'); c.execute('PRAGMA synchronous=FULL'); c.execute('PRAGMA foreign_keys=ON')
    return c

def migrate():
    with conn() as c:
        c.executescript('''
        CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS templates(
          id TEXT PRIMARY KEY,name TEXT NOT NULL,format TEXT NOT NULL DEFAULT '40x40',
          line1 TEXT NOT NULL DEFAULT '',line2 TEXT NOT NULL DEFAULT '',line3 TEXT NOT NULL DEFAULT '',
          qr_mode TEXT NOT NULL DEFAULT 'url',qr_template TEXT NOT NULL DEFAULT '{{spool.url}}',
          created_at TEXT NOT NULL,updated_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS history(
          id TEXT PRIMARY KEY,spool_id INTEGER,title TEXT NOT NULL DEFAULT '',format TEXT NOT NULL,
          template TEXT NOT NULL DEFAULT '',created_at TEXT NOT NULL);
        ''')
        c.execute("INSERT INTO meta(key,value) VALUES('schema_version','1') ON CONFLICT(key) DO UPDATE SET value='1'")

def backup_db(prefix='auto'):
    if not DB.exists(): return None
    BACKUPS.mkdir(parents=True,exist_ok=True)
    path=BACKUPS/f"{prefix}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.sqlite"
    src=sqlite3.connect(DB); dst=sqlite3.connect(path)
    with dst: src.backup(dst)
    src.close(); dst.close()
    files=sorted(BACKUPS.glob('*.sqlite'),key=lambda p:p.stat().st_mtime,reverse=True)
    for old in files[BACKUP_KEEP:]: old.unlink(missing_ok=True)
    return path

def proxy(path):
    if not SPOOLMAN_URL: return jsonify(error='SPOOLMAN_URL ist nicht konfiguriert'),503
    url=f"{SPOOLMAN_URL}/api/v1{path}"
    headers={'Accept':'application/json','User-Agent':f'spoolman-niimbot/{APP_VERSION}'}
    if SPOOLMAN_CF_ID and SPOOLMAN_CF_SECRET:
        headers['CF-Access-Client-Id']=SPOOLMAN_CF_ID
        headers['CF-Access-Client-Secret']=SPOOLMAN_CF_SECRET
    req=urllib.request.Request(url,headers=headers)
    try:
        with urllib.request.urlopen(req,timeout=PROXY_TIMEOUT) as r:
            body=r.read(8*1024*1024+1)
            if len(body)>8*1024*1024: return jsonify(error='Spoolman-Antwort zu gross'),502
            return Response(body,status=r.status,content_type=r.headers.get('Content-Type','application/json'))
    except urllib.error.HTTPError as e:
        return Response(e.read(1024*1024),status=e.code,content_type=e.headers.get('Content-Type','application/json'))
    except Exception as e:
        return jsonify(error='Spoolman nicht erreichbar',detail=str(e)),502

@app.after_request
def cors(resp):
    origin=request.headers.get('Origin','')
    if ALLOWED_ORIGIN and origin==ALLOWED_ORIGIN:
        resp.headers['Access-Control-Allow-Origin']=origin
        resp.headers['Vary']='Origin'
        resp.headers['Access-Control-Allow-Methods']='GET,POST,PUT,PATCH,DELETE,OPTIONS'
        resp.headers['Access-Control-Allow-Headers']='Content-Type,CF-Access-Client-Id,CF-Access-Client-Secret'
    return resp

@app.route('/health')
def health(): return jsonify(status='ok',version=APP_VERSION,spoolman_configured=bool(SPOOLMAN_URL))

@app.route('/api/config')
def config(): return jsonify(version=APP_VERSION,app_url=APP_URL,spoolman_public_url=SPOOLMAN_PUBLIC_URL,spoolman_configured=bool(SPOOLMAN_URL))

@app.route('/api/spoolman/<path:path>',methods=['GET','OPTIONS'])
def spoolman_proxy(path):
    if request.method=='OPTIONS': return ('',204)
    qs=request.query_string.decode()
    return proxy('/'+path+('?' + qs if qs else ''))

@app.route('/api/templates',methods=['GET','POST','OPTIONS'])
def templates():
    if request.method=='OPTIONS': return ('',204)
    if request.method=='GET':
        with conn() as c: return jsonify([dict(r) for r in c.execute('SELECT * FROM templates ORDER BY name')])
    d=request.get_json(force=True) or {}; t=now(); tid=str(d.get('id') or f"tpl-{int(time.time()*1000)}")
    row={'id':tid,'name':str(d.get('name') or 'Vorlage')[:120],'format':str(d.get('format') or '40x40')[:20],'line1':str(d.get('line1') or '')[:500],'line2':str(d.get('line2') or '')[:500],'line3':str(d.get('line3') or '')[:500],'qr_mode':str(d.get('qrMode') or d.get('qr_mode') or 'url')[:30],'qr_template':str(d.get('qrTemplate') or d.get('qr_template') or '{{spool.url}}')[:1000],'created_at':d.get('created_at') or t,'updated_at':t}
    with conn() as c:
        c.execute('''INSERT INTO templates(id,name,format,line1,line2,line3,qr_mode,qr_template,created_at,updated_at)
        VALUES(:id,:name,:format,:line1,:line2,:line3,:qr_mode,:qr_template,:created_at,:updated_at)
        ON CONFLICT(id) DO UPDATE SET name=excluded.name,format=excluded.format,line1=excluded.line1,line2=excluded.line2,line3=excluded.line3,qr_mode=excluded.qr_mode,qr_template=excluded.qr_template,updated_at=excluded.updated_at''',row)
    return jsonify(row)

@app.route('/api/templates/<tid>',methods=['DELETE','OPTIONS'])
def template_delete(tid):
    if request.method=='OPTIONS': return ('',204)
    with conn() as c: c.execute('DELETE FROM templates WHERE id=?',(tid,))
    return jsonify(ok=True)

@app.route('/api/history',methods=['GET','POST','DELETE','OPTIONS'])
def history():
    if request.method=='OPTIONS': return ('',204)
    if request.method=='GET':
        with conn() as c:return jsonify([dict(r) for r in c.execute('SELECT * FROM history ORDER BY created_at DESC LIMIT 100')])
    if request.method=='DELETE':
        with conn() as c:c.execute('DELETE FROM history')
        return jsonify(ok=True)
    d=request.get_json(force=True) or {}; row={'id':str(d.get('id') or f"hist-{int(time.time()*1000)}"),'spool_id':int(d.get('spool_id') or 0),'title':str(d.get('title') or '')[:300],'format':str(d.get('format') or '40x40')[:20],'template':str(d.get('template') or '')[:200],'created_at':d.get('created_at') or now()}
    with conn() as c:c.execute('INSERT OR REPLACE INTO history(id,spool_id,title,format,template,created_at) VALUES(:id,:spool_id,:title,:format,:template,:created_at)',row)
    return jsonify(row)

@app.route('/api/export')
def export():
    with conn() as c:
        return jsonify(format='spoolman-niimbot-backup',version=1,exported_at=now(),templates=[dict(r) for r in c.execute('SELECT * FROM templates')],history=[dict(r) for r in c.execute('SELECT * FROM history')])

@app.route('/api/import',methods=['POST','OPTIONS'])
def import_backup():
    if request.method=='OPTIONS':return ('',204)
    d=request.get_json(force=True) or {}
    if d.get('format')!='spoolman-niimbot-backup' or int(d.get('version',0))!=1:return jsonify(error='Ungültiges Backupformat'),400
    backup_db('pre-restore')
    with conn() as c:
        c.execute('DELETE FROM templates'); c.execute('DELETE FROM history')
        for raw in d.get('templates',[]):
            t=now(); row={'id':str(raw.get('id') or f"tpl-{int(time.time()*1000)}"),'name':str(raw.get('name') or 'Vorlage')[:120],'format':str(raw.get('format') or '40x40')[:20],'line1':str(raw.get('line1') or '')[:500],'line2':str(raw.get('line2') or '')[:500],'line3':str(raw.get('line3') or '')[:500],'qr_mode':str(raw.get('qr_mode') or raw.get('qrMode') or 'url')[:30],'qr_template':str(raw.get('qr_template') or raw.get('qrTemplate') or '{{spool.url}}')[:1000],'created_at':raw.get('created_at') or t,'updated_at':raw.get('updated_at') or t}
            c.execute('INSERT INTO templates VALUES(:id,:name,:format,:line1,:line2,:line3,:qr_mode,:qr_template,:created_at,:updated_at)',row)
        for raw in d.get('history',[]):
            row={'id':str(raw.get('id') or f"hist-{int(time.time()*1000)}"),'spool_id':int(raw.get('spool_id') or 0),'title':str(raw.get('title') or '')[:300],'format':str(raw.get('format') or '40x40')[:20],'template':str(raw.get('template') or '')[:200],'created_at':raw.get('created_at') or now()}
            c.execute('INSERT INTO history VALUES(:id,:spool_id,:title,:format,:template,:created_at)',row)
    return jsonify(ok=True)

@app.route('/')
def index(): return send_from_directory(app.static_folder,'index.html')
@app.route('/<path:path>')
def static_files(path):
    p=Path(app.static_folder)/path
    return send_from_directory(app.static_folder,path if p.exists() and p.is_file() else 'index.html')

migrate()
if __name__=='__main__': app.run(host='0.0.0.0',port=8080)
