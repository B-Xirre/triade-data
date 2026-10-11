import argparse,json,time
import httpx
def main():
    parser=argparse.ArgumentParser(prog='triade-lab');parser.add_argument('command',choices=['sync','validate','subjects','run','compare','report','cancel','save']);parser.add_argument('--url',default='http://127.0.0.1:8765');parser.add_argument('--revision');parser.add_argument('--run-id');parser.add_argument('--file');parser.add_argument('--suite',default='combat-contracts');parser.add_argument('--seed',default='0');parser.add_argument('--workers',type=int,default=1);args=parser.parse_args()
    base=args.url+'/api/v1';payload=None;method='GET'
    if args.command=='sync':path='/sync';method='POST';payload={}
    elif args.command=='validate':path='/coverage'
    elif args.command=='subjects':path='/subjects'
    elif args.command=='run':path='/runs';method='POST';payload={'revision_id':args.revision,'suite_id':args.suite,'root_seed':args.seed,'workers':args.workers}
    elif args.command=='cancel':path='/runs/'+args.run_id+'/cancel';method='POST';payload={}
    elif args.command=='save':path='/experiments/revisions';method='POST';payload=json.load(open(args.file,encoding='utf-8'))
    else:path='/runs/'+args.run_id+'/report'
    response=httpx.request(method,base+path,json=payload,timeout=120);response.raise_for_status();print(json.dumps(response.json(),indent=2,ensure_ascii=False))
if __name__=='__main__':main()
