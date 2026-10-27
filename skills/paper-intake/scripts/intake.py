#!/usr/bin/env python3
"""Associate a formally saved DeepPaperNote with the user's Obsidian workbench."""
from __future__ import annotations
import argparse,contextlib,datetime,fcntl,hashlib,json,os,re,shutil,tempfile,uuid
from pathlib import Path
from urllib.parse import unquote
import yaml

PDF_DIR='10 文献/PDF'; NOTE_DIR='10 文献/阅读笔记'
REGISTRY='99 系统与附件/论文入库登记.json'

def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
 return h.hexdigest()
def load(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def relative(root,path):return Path(path).resolve().relative_to(root.resolve()).as_posix()
def safe(root,path):
 p=(root/str(path)).resolve();relative(root,p);return p
def split(text):
 m=re.match(r'^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)',text)
 if not m:return {},text
 fm=yaml.safe_load(m.group(1)) or {}
 if not isinstance(fm,dict):raise ValueError('frontmatter must be an object')
 return fm,text[m.end():]
def compose(fm,body):return '---\n'+yaml.safe_dump(fm,allow_unicode=True,sort_keys=False).rstrip()+'\n---\n'+body
def atomic(path,content):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 fd,tmp=tempfile.mkstemp(prefix='.intake-',dir=path.parent)
 try:
  with os.fdopen(fd,'w',encoding='utf-8') as f:f.write(content);f.flush();os.fsync(f.fileno())
  os.replace(tmp,path)
 finally:
  if os.path.exists(tmp):os.unlink(tmp)
def write_json(path,obj):atomic(path,json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def layout(root):
 p=root/'.obsidian/academic-workbench.json'
 return load(p) if p.exists() else {}
def registry_path(root):return safe(root,layout(root).get('registry',REGISTRY))
def registry(root):
 p=registry_path(root)
 data=load(p) if p.exists() else {'schema_version':1,'papers':{}}
 if data.get('schema_version')!=1 or not isinstance(data.get('papers'),dict):raise ValueError('Unsupported intake registry')
 return data
def doi(v):return re.sub(r'^https?://(?:dx\.)?doi\.org/','',str(v or '').strip(),flags=re.I).lower()
def wikivalue(v):return str(v or '').removeprefix('[[').removesuffix(']]').split('|')[0].split('#')[0]
def resolve(root,value):
 p=safe(root,wikivalue(value))
 if p.is_file():return p
 if p.with_suffix('.md').is_file():return p.with_suffix('.md')
 hits=[q for q in root.rglob(Path(wikivalue(value)).name) if q.is_file()]
 return hits[0] if len(hits)==1 else None
def existing(root,pdf,d):
 digest=sha(pdf);reg=registry(root);matches={}
 for p in (root/NOTE_DIR).rglob('*.md'):
  fm,_=split(p.read_text(encoding='utf-8'));linked=resolve(root,fm.get('pdf','')) if fm.get('pdf') else None
  hashmatch=linked and linked.is_file() and linked.stat().st_size==pdf.stat().st_size and sha(linked)==digest
  if hashmatch or (d and doi(fm.get('doi'))==d):matches[relative(root,p)]={'path':relative(root,p),'reference_id':fm.get('reference_id',''),'fm':fm}
 for key,item in reg['papers'].items():
  if (d and doi(item.get('doi'))==d) or any(s.get('sha256')==digest for s in item.get('pdfs',[])):
   p=safe(root,item['source_note'])
   if not p.is_file():raise ValueError('Registered reading homepage missing: '+str(p))
   fm,_=split(p.read_text(encoding='utf-8'));matches[relative(root,p)]={'path':relative(root,p),'reference_id':key,'fm':fm}
 if len(matches)>1:raise ValueError('Multiple reading homepages match this PDF/DOI: '+', '.join(matches))
 return next(iter(matches.values()),None)
def find_pdf(root,pdf,digest):
 hits=[]
 for p in root.rglob('*'):
  if p.is_file() and p.suffix.lower()=='.pdf' and '.obsidian' not in p.parts and p.stat().st_size==pdf.stat().st_size and sha(p)==digest:hits.append(p)
 hits.sort(key=lambda p:(not relative(root,p).startswith(PDF_DIR+'/'),relative(root,p)))
 return hits[0] if hits else None
def check_images(root,note):
 text=note.read_text(encoding='utf-8')
 targets=re.findall(r'!\[[^\]]*\]\(([^)]+)\)',text)
 targets+=re.findall(r'!\[\[([^\]]+)\]\]',text)
 for t in targets:
  t=t.strip().strip('<>').split('|')[0].split('#')[0]
  if not t:continue
  if re.match(r'^(https?|data):',t):continue
  t=unquote(t);p=(note.parent/t).resolve()
  try:relative(root,p)
  except ValueError:raise ValueError('Image/embed is outside Vault: '+t)
  if not p.is_file():
   p=resolve(root,t)
   if p is None:raise ValueError('Missing or ambiguous local image/embed: '+t)
 return len(targets)
@contextlib.contextmanager
def lock(root):
 p=registry_path(root).parent/'.paper-intake.lock';p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('a') as f:
  fcntl.flock(f,fcntl.LOCK_EX)
  try:yield
  finally:fcntl.flock(f,fcntl.LOCK_UN)
def clean_name(s):return re.sub(r'[\\/:*?"<>|#\[\]^]','-',s).strip()[:150] or '未命名论文'
def unique(root,base,suffix):
 p=root/(base+suffix);i=2
 while p.exists():p=root/(base+' ('+str(i)+')'+suffix);i+=1
 return p
def register(root,args):
 manifest=load(args.source_manifest);save=load(args.save_result);lint=load(args.lint_json);review=load(args.review_json)
 if save.get('status')!='ok' or save.get('script')!='write_obsidian_note.py' or save.get('output_mode')!='obsidian':raise ValueError('Require successful native Obsidian Formal Save')
 note=Path(save['note_path']).resolve();relative(root,note)
 if relative(root,note).startswith(NOTE_DIR+'/'):raise ValueError('AI output cannot replace a personal reading homepage')
 digest=sha(note);language=save.get('output_language')
 if lint.get('note_sha256')!=digest or language!=lint.get('output_language'):raise ValueError('Saved AI note no longer matches final lint')
 for required in ['passes_basic_structure','passes_style_gate','passes_math_gate']:
  if lint.get(required) is not True:raise ValueError('Final lint did not pass: '+required)
 if any(v is not True for k,v in lint.items() if k.startswith('passes_')):raise ValueError('A final lint gate is not passed')
 if review.get('note_sha256')!=digest or review.get('final_quality_review') is not True or review.get('final_readability_review') is not True:raise ValueError('Require completed quality and readability reviews for final note bytes')
 pdf=Path(manifest['pdf']['path']).expanduser().resolve();source_hash=sha(pdf)
 if manifest.get('source_sha256')!=source_hash or save.get('source_sha256')!=source_hash:raise ValueError('PDF source hash mismatch')
 sidecar=Path(save['sidecar_path']).resolve();relative(root,sidecar)
 if sidecar.parent!=note.parent:raise ValueError('Archive sidecar does not belong to AI note')
 archive=load(sidecar);binding=archive.get('sources',{}).get(source_hash,{}).get('notes',{}).get(language,{})
 if binding.get('filename')!=note.name or binding.get('note_sha256')!=digest:raise ValueError('Formal Save archive binding mismatch')
 image_count=check_images(root,note)
 afm,_=split(note.read_text(encoding='utf-8'));d=doi(args.doi or afm.get('doi',''));title=args.title or manifest.get('title') or save.get('title') or note.stem
 with lock(root):
  old=existing(root,pdf,d);reg=registry(root)
  ref=(old or {}).get('reference_id') or 'lit-'+uuid.uuid4().hex[:12]
  copied=find_pdf(root,pdf,source_hash)
  if copied is None:
   copied=unique(root,PDF_DIR+'/'+clean_name(title)+'-'+source_hash[:8],'.pdf');copied.parent.mkdir(parents=True,exist_ok=True)
   # Do not overwrite another file, including a concurrent Obsidian import.
   with copied.open('xb') as output,pdf.open('rb') as source:shutil.copyfileobj(source,output)
   if sha(copied)!=source_hash:raise ValueError('Imported PDF hash mismatch')
  home=safe(root,old['path']) if old else unique(root,NOTE_DIR+'/'+clean_name(title),'.md')
  if old:
   if not old['fm'].get('reference_id'):
    original=home.read_text(encoding='utf-8');fm,body=split(original);fm['reference_id']=ref
    if home.read_text(encoding='utf-8')!=original:raise ValueError('Reading homepage changed during import')
    atomic(home,compose(fm,body))
  else:
   template=safe(root,layout(root).get('template','90 模板/文献阅读模板.md'))
   text=template.read_text(encoding='utf-8') if template.exists() else '---\ntype: literature\n---\n# {{title}}\n\n## 我的理解与质疑\n'
   today=datetime.date.today().isoformat();text=text.replace('{{title}}',title).replace('{{date:YYYY-MM-DD}}',today).replace('{{date}}',today)
   fm,body=split(text);fm.update(type='literature',reference_id=ref,title=title,doi=d,pdf='[['+relative(root,copied)+']]',status='待读',tags=args.tags or afm.get('tags',[]) or [],topics=[],projects=[])
   if layout(root).get('reading_only'):
    fm.pop('topics',None);fm.pop('projects',None)
   body=body.replace('- PDF：将库中的 PDF 拖到这里','- PDF：[['+relative(root,copied)+']]')
   home.parent.mkdir(parents=True,exist_ok=True)
   with home.open('x',encoding='utf-8') as f:f.write(compose(fm,body))
  entry=reg['papers'].setdefault(ref,{'reference_id':ref,'title':title,'doi':d,'source_note':relative(root,home),'pdfs':[],'ai_notes':[]})
  entry['source_note']=relative(root,home)
  if not any(x['sha256']==source_hash for x in entry['pdfs']):entry['pdfs'].append({'path':relative(root,copied),'sha256':source_hash})
  ai={'path':relative(root,note),'sha256':digest,'source_sha256':source_hash,'output_language':language,'review_status':'待核对'}
  found=next((i for i,v in enumerate(entry['ai_notes']) if v['path']==ai['path']),None)
  if found is None:entry['ai_notes'].append(ai)
  else:ai['review_status']=entry['ai_notes'][found].get('review_status','待核对');entry['ai_notes'][found]=ai
  write_json(registry_path(root),reg)
  if sha(note)!=digest:raise ValueError('AI note changed during association')
 return {'status':'registered','reference_id':ref,'source_note':str(home),'pdf':str(copied),'ai_note':str(note),'ai_sha256_unchanged':True,'image_embeds_checked':image_count}

def merge_block(text,marker,body):
 start='<!-- '+marker+':start -->';end='<!-- '+marker+':end -->';block=start+'\n\n'+body+'\n\n'+end
 a=text.find(start);b=text.find(end)
 if (a>=0)!=(b>=0) or (b>=0 and b<a):raise ValueError('Incomplete generated markers: '+marker)
 if a>=0:return text[:a]+block+text[b+len(end):]
 slot='<!-- '+marker+':slot -->'
 return text.replace(slot,block,1) if slot in text else text.rstrip()+'\n\n'+block+'\n'
def write_block(path,marker,body,title=''):
 before=path.read_text(encoding='utf-8') if path.exists() else title+'\n\n'
 after=merge_block(before,marker,body)
 if after!=before:
  if path.exists() and path.read_text(encoding='utf-8')!=before:raise ValueError('Note edited during refresh: '+str(path))
  atomic(path,after)
def cell(v):return str(v or '').replace('\n',' ').replace('|','\\|')
def link(path,title,table=True):return '[['+str(path).removesuffix('.md')+('\\|' if table else '|')+str(title).replace('|','-').replace('[','').replace(']','')+']]'
def display_title(fm,fallback):
 title=str(fm.get('title') or fallback)
 number=fm.get('paper_number')
 if isinstance(number,int) and not isinstance(number,bool) and number>0:
  prefix=re.match(r'^(\d+)[ _-]',title)
  if not prefix or int(prefix.group(1))!=number:title=f'{number:03d} '+title
 return title
def refresh(root):
 with lock(root):
  reg=registry(root);by_ai={ai['path']:(ref,ai) for ref,p in reg['papers'].items() for ai in p['ai_notes']}
  all_ai=[]
  paths=set((root/'10 文献/AI辅助阅读').rglob('*.md'))|{safe(root,p) for p in by_ai}
  for path in sorted(paths):
   if not path.is_file():continue
   fm,body=split(path.read_text(encoding='utf-8'));rel=relative(root,path)
   if rel in by_ai:
    ref,record=by_ai[rel]
    # A modified saved note is kept for the user, but it is no longer reported as verified.
    status=record.get('review_status','待核对') if sha(path)==record['sha256'] else '保存后有改动，待复核'
   else:ref=fm.get('reference_id','');status=fm.get('review_status','待核对')
   all_ai.append((ref,path,status,body,fm))
  rows=[];groups={};ids=set()
  for path in sorted((root/NOTE_DIR).rglob('*.md')):
   fm,_=split(path.read_text(encoding='utf-8'));ref=fm.get('reference_id') or relative(root,path)
   if ref in ids:continue
   ids.add(ref);title=display_title(fm,path.stem)
   ais=[a for a in all_ai if a[0]==ref]
   ai_lines=[ '- '+link(relative(root,a[1]),a[1].stem,False)+'（'+a[2]+'）' for a in ais]
   summary=next((a for a in ais if re.search(r'^## 一句话总结\s*$',a[3],re.M)),None)
   ai_section='\n'.join(ai_lines) or '尚无关联的 AI 笔记。AI 输出带上相同 reference_id 或 source_note 后会自动出现在这里。'
   if summary:ai_section+='\n\n> 以下摘要来自 AI 笔记，供阅读参考。\n\n![['+relative(root,summary[1]).removesuffix('.md')+'#一句话总结]]'
   write_block(path,'academic-ai',ai_section)
   raw=fm.get('tags',[]);raw=raw if isinstance(raw,list) else re.split(r'[\s,，]+',str(raw))
   tags=sorted(set(str(t).lstrip('#').strip() for t in raw if str(t).strip()))
   for tag in tags:groups.setdefault(tag.casefold(),{'tag':tag,'papers':[]})['papers'].append((relative(root,path),title))
   pdf=wikivalue(fm.get('pdf',''));pdf_link=link(pdf,'原文') if pdf and safe(root,pdf).is_file() else '未关联或已移走'
   ai_links='<br>'.join(link(relative(root,a[1]),a[1].stem+' · '+a[2]) for a in ais) or '尚无'
   display=lambda v:'、'.join(map(str,v)) if isinstance(v,list) else cell(v)
   values=[link(relative(root,path),title),ai_links,pdf_link,cell(fm.get('status','待读')),' '.join('#'+t for t in tags),display(fm.get('topics',[])),display(fm.get('projects',[]))]
   rows.append('| '+' | '.join(values[:5] if layout(root).get('reading_only') else values)+' |')
  table='| 论文 / 阅读主页 | AI 精读 | PDF | 阅读状态 | 标签 | 主题笔记 | 关联项目 |\n| --- | --- | --- | --- | --- | --- | --- |\n'+'\n'.join(rows)
  if layout(root).get('reading_only'):
   table='| 论文 / 阅读主页 | AI 精读 | PDF | 阅读状态 | 标签 |\n| --- | --- | --- | --- | --- |\n'+'\n'.join(rows)
  write_block(root/'10 文献/文献目录.md','academic-library','共 **'+str(len(ids))+'** 篇论文\n\n'+table+'\n\n[[10 文献/标签索引|按标签浏览论文]]','# 文献目录')
  groups=sorted(groups.values(),key=lambda g:g['tag'])
  overview='| 标签 | 论文数 |\n| --- | --- |\n'+'\n'.join('| #'+g['tag']+' | '+str(len(g['papers']))+' |' for g in groups)
  detail='\n\n'.join('## '+g['tag']+' · '+str(len(g['papers']))+' 篇\n\n'+'\n'.join('- '+link(p,t,False) for p,t in g['papers']) for g in groups)
  write_block(root/'10 文献/标签索引.md','academic-tags',overview+'\n\n'+detail,'# 标签索引')
 return {'status':'refreshed','papers':len(ids),'tags':len(groups)}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vault')
 sub=p.add_subparsers(dest='command',required=True)
 sub.add_parser('status');sub.add_parser('refresh')
 look=sub.add_parser('lookup');look.add_argument('--pdf',required=True);look.add_argument('--doi',default='')
 add=sub.add_parser('register')
 for field in ['source-manifest','save-result','lint-json','review-json']:add.add_argument('--'+field,required=True)
 add.add_argument('--title');add.add_argument('--doi',default='');add.add_argument('--tags',nargs='*')
 args=p.parse_args();configpath=Path(os.environ.get('DEEPPAPERNOTE_CONFIG_PATH') or Path.home()/'.deeppapernote/config.json').expanduser()
 config=load(configpath) if configpath.exists() else {}
 for field in ['output_language','save_mode','obsidian_vault','papers_dir']:
  value=os.environ.get('DEEPPAPERNOTE_'+field.upper())
  if value:config[field]=value
 root=Path(args.vault or config.get('obsidian_vault','')).expanduser().resolve()
 if not args.vault and not config.get('obsidian_vault'):raise ValueError('No configured Obsidian Vault')
 if not root.is_dir():raise ValueError('Vault does not exist')
 if args.command=='status':result={'status':'ready','vault':str(root),'output_language':config.get('output_language'),'save_mode':config.get('save_mode'),'papers_dir':config.get('papers_dir'),'registered_papers':len(registry(root)['papers'])}
 elif args.command=='lookup':
  pdf=Path(args.pdf).expanduser().resolve();match=existing(root,pdf,doi(args.doi));result={'status':'existing' if match else 'new','source_sha256':sha(pdf),'match':{k:v for k,v in match.items() if k!='fm'} if match else None}
 elif args.command=='register':result=register(root,args)
 else:result=refresh(root)
 print(json.dumps(result,ensure_ascii=False,indent=2,default=str))
if __name__=='__main__':
 try:main()
 except (ValueError,KeyError,OSError) as exc:raise SystemExit(str(exc))
