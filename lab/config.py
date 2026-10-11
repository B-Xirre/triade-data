import os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DATA=Path(os.environ.get('TRIADE_LAB_DATA',str(ROOT/'.lab-data')))
DOC_ID=os.environ.get('TRIADE_GRIST_DOC_ID','3TwLJyu7fythPjAj1e1424')
GRIST_URL=os.environ.get('TRIADE_GRIST_URL','http://localhost:8484').rstrip('/')
WORKER_URL=os.environ.get('TRIADE_WORKER_URL','http://127.0.0.1:8766').rstrip('/')
def initialize():
    for name in ['snapshots','warehouse','lake','runs','drafts']: (DATA/name).mkdir(parents=True,exist_ok=True)
