'use strict';
const {Plugin,TFile,Notice,normalizePath,parseYaml,stringifyYaml,getFrontMatterInfo}=require('obsidian');
const {randomBytes}=require('crypto');
const PDF_DIR='10 文献/PDF', NOTE_DIR='10 文献/阅读笔记';
const REGISTRY='10 文献/阅读工具/论文入库登记.json';
const AI_DIR='10 文献/AI辅助阅读', TAG_INDEX='10 文献/标签索引.md';
const INDEX='10 文献/文献目录.md', TEMPLATE='10 文献/阅读工具/模板/文献阅读模板.md';
const START='<!-- academic-library:start -->', END='<!-- academic-library:end -->';
const inside=(path,dir)=>path.startsWith(dir+'/');
const date=()=>{const d=new Date();return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;};
const cell=v=>(Array.isArray(v)?v.join('、'):String(v??'')).replace(/\r?\n/g,' ').replace(/\|/g,'\\|');
const label=v=>cell(v).replace(/[\[\]]/g,'');
const link=(path,text)=>`[[${path}\\|${label(text)}]]`;
function displayTitle(fm,fallback){const title=String(fm.title||fallback),n=fm.paper_number,m=/^(\d+)[ _-]/.exec(title);return Number.isInteger(n)&&n>0&&(!m||Number(m[1])!==n)?String(n).padStart(3,'0')+' '+title:title;}
function metadata(text){const info=getFrontMatterInfo(text);return info.exists?(parseYaml(info.frontmatter)||{}):{};}
function pdfPath(value){return typeof value==='string'?normalizePath(value.replace(/^\[\[/,'').replace(/\]\]$/,'').split('|')[0].split('#')[0]):'';}
module.exports=class AcademicLibrary extends Plugin{
 async onload(){
  this.stopped=false;this.data=(await this.loadData())||{};this.data.records=this.data.records||{};
  const changed=file=>{if(file instanceof TFile&&(inside(file.path,PDF_DIR)||inside(file.path,NOTE_DIR)||inside(file.path,AI_DIR)||file.path===REGISTRY||Boolean(this.intakeAI?.has(file.path))))this.schedule();};
  for(const event of ['create','modify','delete'])this.registerEvent(this.app.vault.on(event,changed));
  this.registerEvent(this.app.vault.on('rename',(file,old)=>{this.renameQueue=this.renameQueue||[];this.renameQueue.push({file,old});this.schedule();}));
  this.addCommand({id:'refresh',name:'刷新文献目录并补建阅读笔记',callback:()=>this.run(true)});
  this.addCommand({id:'open-catalog',name:'打开文献目录',callback:async()=>{await this.run();await this.app.workspace.openLinkText(INDEX,'',false);}});
  this.addRibbonIcon('library-big','打开文献目录',async()=>{await this.run();await this.app.workspace.openLinkText(INDEX,'',false);});
  this.app.workspace.onLayoutReady(()=>this.schedule());
 }
 onunload(){this.stopped=true;clearTimeout(this.timer);}
 schedule(){if(this.stopped)return;clearTimeout(this.timer);this.timer=setTimeout(()=>{this.timer=null;this.run();},800);}
 async run(notify=false){
  if(this.running){this.again=true;return this.running;}
  this.running=(async()=>{try{do{this.again=false;if(this.stopped)return;await this.sync();}while(this.again&&!this.stopped);if(notify)new Notice('文献目录已更新');}
  catch(e){console.error('[学术文献助手]',e);new Notice('文献目录更新失败：'+e.message,10000);}})();
  try{await this.running;}finally{this.running=null;}
 }
 async folder(path){if(!this.app.vault.getAbstractFileByPath(path))await this.app.vault.createFolder(path);}
 async setProperties(note,values){await this.app.fileManager.processFrontMatter(note,fm=>{for(const [k,v]of Object.entries(values))fm[k]=v;});}
 async sync(){
  const vault=this.app.vault;await this.folder(NOTE_DIR);
  const registryFile=vault.getAbstractFileByPath(REGISTRY);
  this.intakeRegistry=registryFile instanceof TFile?JSON.parse(await vault.read(registryFile)):{schema_version:1,papers:{}};
  if(this.intakeRegistry.schema_version!==1)throw new Error('不支持的论文入库登记格式');
  this.intakeAI=new Map();
  for(const [ref,p]of Object.entries(this.intakeRegistry.papers||{}))for(const ai of p.ai_notes||[])this.intakeAI.set(ai.path,{...ai,reference_id:ref,source_note:p.source_note});

  for(const {file,old}of this.renameQueue||[]){
   for(const [path,notePath]of Object.entries(this.data.records)){
    if(notePath===old)this.data.records[path]=file.path;
    if(path===old&&file instanceof TFile&&file.extension.toLowerCase()==='pdf'){
     const note=vault.getAbstractFileByPath(notePath);
     if(note instanceof TFile)await this.setProperties(note,{pdf:`[[${file.path}]]`});
     this.data.records[file.path]=notePath;delete this.data.records[old];
    }
   }
  }
  this.renameQueue=[];
  const rows=[];const assigned=new Map();
  const pdfs=vault.getFiles().filter(f=>f.extension.toLowerCase()==='pdf'&&inside(f.path,PDF_DIR));
  const noteFiles=vault.getMarkdownFiles().filter(f=>inside(f.path,NOTE_DIR));
  for(const note of noteFiles){
   const text=await vault.read(note);const fm=metadata(text);let path=pdfPath(fm.pdf);
   // Adopt an existing handwritten note only when it points unambiguously to one PDF.
   if(!path){
    const candidates=new Set();
    for(const match of text.matchAll(/\[\[([^\]]+)\]\]/g)){
     const target=match[1].split('|')[0].split('#')[0];
     if(!/\.pdf$/i.test(target))continue;
     const dest=this.app.metadataCache.getFirstLinkpathDest(target,note.path);
     if(dest&&inside(dest.path,PDF_DIR))candidates.add(dest.path);
    }
    if(candidates.size===1)path=[...candidates][0];
   }
   if(path&&inside(path,PDF_DIR)){
    const values={};
    if(!fm.pdf)values.pdf=`[[${path}]]`;
    if(!fm.type)values.type='literature';if(!fm.status)values.status='待读';
    if(!fm.created)values.created=date();if(!fm.reference_id)values.reference_id='lit-'+randomBytes(6).toString('hex');
    if(fm.tags===undefined)values.tags=[];
    if(Object.keys(values).length){await this.setProperties(note,values);Object.assign(fm,values);}
    if(!assigned.has(path))assigned.set(path,note.path);
    this.data.records[path]=assigned.get(path);
   }
   rows.push({note,fm,path});
  }
  for(const p of Object.values(this.intakeRegistry.papers||{})){
   const home=vault.getAbstractFileByPath(p.source_note);
   if(!(home instanceof TFile))continue;
   for(const source of p.pdfs||[]){
    if(!vault.getAbstractFileByPath(source.path))continue;
    assigned.set(source.path,home.path);this.data.records[source.path]=home.path;
    if(!pdfs.some(f=>f.path===source.path))pdfs.push(vault.getAbstractFileByPath(source.path));
   }
  }
  for(const pdf of pdfs){
   if(assigned.has(pdf.path))continue;
   const remembered=this.data.records[pdf.path];
   // A mapping may survive a note moved outside the default notes folder.
   if(remembered){const n=vault.getAbstractFileByPath(remembered);if(n instanceof TFile){const fm=metadata(await vault.read(n));if(pdfPath(fm.pdf)===pdf.path){rows.push({note:n,fm,path:pdf.path});continue;}}}
   let name=pdf.basename.replace(/[\\/:*?"<>|#\[\]^]/g,'-').trim()||'未命名论文';
   let path=`${NOTE_DIR}/${name}.md`,i=2;
   while(vault.getAbstractFileByPath(path))path=`${NOTE_DIR}/${name} (${i++}).md`;
   const template=vault.getAbstractFileByPath(TEMPLATE);
   let text=template instanceof TFile?await vault.read(template):'---\ntype: literature\n---\n# {{title}}\n\n## 阅读记录\n';
   text=text.replace(/\{\{title\}\}/g,pdf.basename).replace(/\{\{date(?::YYYY-MM-DD)?\}\}/g,date());
   const info=getFrontMatterInfo(text),fm=metadata(text);
   Object.assign(fm,{type:'literature',created:date(),status:'待读',reference_id:'lit-'+randomBytes(6).toString('hex'),pdf:`[[${pdf.path}]]`});
   let body=info.exists?text.slice(info.contentStart):text;
   body=body.replace('- PDF：将库中的 PDF 拖到这里',`- PDF：[[${pdf.path}]]`);
   if(!body.includes(`[[${pdf.path}]]`))body=`\n原文：[[${pdf.path}]]\n${body}`;
   const note=await vault.create(path,`---\n${stringifyYaml(fm).trimEnd()}\n---\n${body}`);
   assigned.set(pdf.path,path);this.data.records[pdf.path]=path;rows.push({note,fm,path:pdf.path});
  }
  await this.renderLibrary(rows,pdfs);
  await this.saveData(this.data);
 }
 async writeSection(path,title,marker,section){
  const vault=this.app.vault,start=`<!-- ${marker}:start -->`,end=`<!-- ${marker}:end -->`;
  const block=`${start}\n\n${section}\n\n${end}`;
  const merge=old=>{
   const a=old.indexOf(start),b=old.indexOf(end);
   if((a>=0)!==(b>=0)||(b>=0&&b<a))throw new Error(path+' 的自动区域标记不完整');
   if(a>=0)return old.slice(0,a)+block+old.slice(b+end.length);
   const slot=`<!-- ${marker}:slot -->`;
   return old.includes(slot)?old.replace(slot,block):old.trimEnd()+'\n\n'+block+'\n';
  };
  const file=vault.getAbstractFileByPath(path);
  if(file instanceof TFile){if(merge(await vault.read(file))!==await vault.read(file))await vault.process(file,merge);}
  else await vault.create(path,title+'\n\n'+block+'\n\n[[10 文献/文献入口|返回阅读工作台]]\n');
 }
 resolveNote(value,from){
  if(typeof value!=='string'||!value)return null;
  const target=pdfPath(value);
  return this.app.vault.getAbstractFileByPath(target)||this.app.vault.getAbstractFileByPath(target+'.md')||this.app.metadataCache.getFirstLinkpathDest(target,from);
 }
 async renderLibrary(rows,pdfs){
  const vault=this.app.vault;
  rows.sort((a,b)=>a.note.path.localeCompare(b.note.path,'zh-CN'));
  // One bibliography entry per stable paper identifier. Multiple notes remain linked.
  const papers=new Map();
  for(const row of rows){
   const id=row.fm.reference_id||row.path||row.note.path;
   if(papers.has(id))papers.get(id).extra.push(row.note);
   else papers.set(id,{...row,id,extra:[],ais:[]});
  }
  const doi=v=>String(v||'').trim().replace(/^https?:\/\/(dx\.)?doi\.org\//i,'').toLowerCase();
  for(const ai of vault.getMarkdownFiles().filter(f=>inside(f.path,AI_DIR)||this.intakeAI?.has(f.path))){
   const text=await vault.read(ai),fm=metadata(text);
   const intake=this.intakeAI?.get(ai.path);
   if(intake){
    fm.reference_id=intake.reference_id;fm.source_note=`[[${intake.source_note}]]`;
    fm.review_status=intake.review_status||'待核对';
    const digest=require('crypto').createHash('sha256').update(text,'utf8').digest('hex');
    if(digest!==intake.sha256)fm.review_status='保存后有改动，待复核';
   }

   const source=this.resolveNote(fm.source_note,ai.path);
   let matches=[...papers.values()].filter(p=>{
    if(fm.reference_id)return fm.reference_id===p.id;
    if(source)return p.note.path===source.path||p.extra.some(n=>n.path===source.path);
    return fm.doi&&p.fm.doi&&doi(fm.doi)===doi(p.fm.doi);
   });
   // Never guess from filenames or tag overlap. Ambiguous files remain unlinked.
   if(matches.length!==1)continue;
   const p=matches[0],values={};
   if(!fm.reference_id)values.reference_id=p.id;
   if(!fm.source_note)values.source_note=`[[${p.note.path.replace(/\.md$/,'')}]]`;
   if(!fm.source_pdf&&p.path)values.source_pdf=`[[${p.path}]]`;
   if(!fm.type)values.type='ai-reading';if(!fm.review_status)values.review_status='待核对';
   const archiveSidecar=vault.getAbstractFileByPath(ai.parent?.path+'/.deeppapernote.json');
   // A formally saved note is immutable for association purposes; metadata stays in the registry.
   if(!intake&&!archiveSidecar&&Object.keys(values).length)await this.setProperties(ai,values);
   Object.assign(fm,values);
   p.ais.push({note:ai,fm,summary:/^## 一句话总结\s*$/m.test(text)});
  }
  const cleanTags=value=>{
   const input=Array.isArray(value)?value:typeof value==='string'?value.split(/[\s,，]+/):[];
   const unique=new Map();
   for(const x of input){const t=String(x).trim().replace(/^#+/,'').normalize('NFC');if(t&&!/\s|[\[\]|]/.test(t))unique.set(t.toLowerCase(),t);}
   return [...unique.values()].sort((a,b)=>a.localeCompare(b,'zh-CN'));
  };
  const tagGroups=new Map(),table=['| 论文 / 阅读主页 | AI 精读 | PDF | 阅读状态 | 标签 |','| --- | --- | --- | --- | --- |'];
  for(const p of papers.values()){
   p.ais.sort((a,b)=>a.note.path.localeCompare(b.note.path,'zh-CN'));
   const home=p.note.path.replace(/\.md$/,''),title=displayTitle(p.fm,p.note.basename);
   const aiLinks=p.ais.map(a=>link(a.note.path.replace(/\.md$/,''),`${a.note.basename} · ${a.fm.review_status||'待核对'}`)).join('<br>')||'尚无';
   const tags=cleanTags(p.fm.tags);
   for(const tag of tags){const key=tag.toLowerCase();if(!tagGroups.has(key))tagGroups.set(key,{tag,papers:[]});tagGroups.get(key).papers.push(p);}
   const extra=p.extra.map(n=>link(n.path.replace(/\.md$/,''),'补充笔记')).join(' ');
   table.push(`| ${link(home,title)} ${extra} | ${aiLinks} | ${p.path&&vault.getAbstractFileByPath(p.path)?link(p.path,'原文'):(p.path?'原文已移走':'未关联')} | ${cell(p.fm.status||'待读')} | ${tags.map(t=>'#'+t).join(' ')} |`);
   const aiRefs=p.ais.map(a=>`- [[${a.note.path.replace(/\.md$/,'')}|${label(a.note.basename).replace(/\\\|/g,'-')}]]（${cell(a.fm.review_status||'待核对')}）`);
   const summary=p.ais.find(a=>a.summary);
   const section=(aiRefs.length?aiRefs.join('\n'):'尚无关联的 AI 笔记。AI 输出带上相同 reference_id 或 source_note 后会自动出现在这里。')+(summary?`\n\n> 以下摘要来自 AI 笔记，供阅读参考。\n\n![[${summary.note.path.replace(/\.md$/,'')}#一句话总结]]`:'');
   await this.writeSection(p.note.path,'','academic-ai',section);
  }
  if(!papers.size)table.push('| 尚未导入论文 | — | — | — | — |');
  const section=`共 **${papers.size}** 篇论文 · **${rows.length}** 份阅读笔记 · **${pdfs.length}** 个 PDF\n\n${table.join('\n')}\n\n[[10 文献/标签索引|按标签浏览论文]]`;
  await this.writeSection(INDEX,'# 文献目录','academic-library',section);
  const sorted=[...tagGroups.values()].sort((a,b)=>a.tag.localeCompare(b.tag,'zh-CN'));
  const overview=['| 标签 | 论文数 |','| --- | --- |',...sorted.map(g=>`| #${g.tag} | ${g.papers.length} |`)];
  const groups=sorted.map(g=>`## ${g.tag} · ${g.papers.length} 篇\n\n`+g.papers.map(p=>`- [[${p.note.path.replace(/\.md$/,'')}|${label(displayTitle(p.fm,p.note.basename)).replace(/\\\|/g,'-')}]]`).join('\n'));
  await this.writeSection(TAG_INDEX,'# 标签索引\n\n按阅读主页的 tags 汇总，以 reference_id 去重。同一篇论文的多份 AI 笔记不会增加论文计数。\n\n[[10 文献/文献目录|全部论文]]','academic-tags',sorted.length?overview.join('\n')+'\n\n'+groups.join('\n\n'):'还没有论文标签。在阅读主页顶部的 tags 属性中添加标签即可。');
 }

};
