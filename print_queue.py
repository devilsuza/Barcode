import os,sqlite3,secrets
from pathlib import Path
from datetime import datetime,timezone
DB=Path(os.getenv('PRINT_DB',Path(__file__).resolve().parent/'data'/'print_jobs.db'))
def now():return datetime.now(timezone.utc).isoformat()
def con():
 c=sqlite3.connect(DB,timeout=20);c.row_factory=sqlite3.Row;c.execute('PRAGMA journal_mode=WAL');return c
def init_db():
 with con() as c:c.execute('CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY,bridge_id TEXT,zpl TEXT,product_id TEXT,ean TEXT,qty INT,status TEXT,message TEXT,created_at TEXT,claimed_at TEXT,completed_at TEXT)')
def enqueue(b,z,p,e,q):
 i=secrets.token_hex(12)
 with con() as c:c.execute('INSERT INTO jobs VALUES(?,?,?,?,?,?,?,?,?,?,?)',(i,b,z,p,e,q,'pending','',now(),None,None))
 return i
def claim(b):
 with con() as c:
  c.execute('BEGIN IMMEDIATE');r=c.execute("SELECT * FROM jobs WHERE bridge_id=? AND status='pending' ORDER BY created_at LIMIT 1",(b,)).fetchone()
  if not r:return None
  c.execute("UPDATE jobs SET status='printing',claimed_at=? WHERE id=?",(now(),r['id']));return dict(c.execute('SELECT * FROM jobs WHERE id=?',(r['id'],)).fetchone())
def finish(i,b,ok,m):
 with con() as c:return c.execute("UPDATE jobs SET status=?,message=?,completed_at=? WHERE id=? AND bridge_id=? AND status='printing'",('printed' if ok else 'failed',m[:500],now(),i,b)).rowcount==1
def get_job(i):
 with con() as c:
  r=c.execute('SELECT id,bridge_id,product_id,ean,qty,status,message,created_at,claimed_at,completed_at FROM jobs WHERE id=?',(i,)).fetchone();return dict(r) if r else None
