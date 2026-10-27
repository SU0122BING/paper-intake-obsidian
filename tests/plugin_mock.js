const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert'),cp=require('child_process');
const root=path.resolve(process.argv[2]);
const parseYaml=s=>JSON.parse(cp.execFileSync(process.env.TEST_PYTHON||'python3',['-c','import sys,json,yaml; print(json.dumps(yaml.safe_load(sys.stdin.read()),default=str))'],{input:s,encoding:'utf8'}));
const stringifyYaml=o=>Object.entries(o).map(([k,v])=>k+': '+JSON.stringify(v)).join('\n')+'\n';
function getFrontMatterInfo(t){const m=/^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/.exec(t);return m?{exists:true,frontmatter:m[1],contentStart:m[0].length}:{exists:false,contentStart:0};}
class TFile{constructor(p){this.path=p;this.extension=path.extname(p).slice(1);this.basename=path.basename(p,path.extname(p));this.parent={path:path.dirname(p)};}}
const file=p=>fs.existsSync(path.join(root,p))?(fs.statSync(path.join(root,p)).isFile()?new TFile(p):{path:p}):null;
function all(dir=root){return fs.readdirSync(dir,{withFileTypes:true}).flatMap(e=>e.isDirectory()?(e.name==='.obsidian'?[]:all(path.join(dir,e.name))):[new TFile(path.relative(root,path.join(dir,e.name)))]);}
const vault={getAbstractFileByPath:file,getFiles:()=>all(),getMarkdownFiles:()=>all().filter(x=>x.extension==='md'),read:async f=>fs.readFileSync(path.join(root,f.path),'utf8'),createFolder:async p=>fs.mkdirSync(path.join(root,p),{recursive:true}),create:async(p,s)=>{fs.writeFileSync(path.join(root,p),s,{flag:'wx'});return file(p);},process:async(f,fn)=>{const p=path.join(root,f.path),before=fs.readFileSync(p,'utf8'),after=fn(before);if(before!==after)fs.writeFileSync(p,after);},on:()=>({})};
const notices=[];
class Plugin{async loadData(){return {};}async saveData(d){this.saved=JSON.parse(JSON.stringify(d));}registerEvent(){}addCommand(){}addRibbonIcon(){}}
const api={Plugin,TFile,Notice:class{constructor(s){notices.push(s)}},normalizePath:p=>p.replace(/\\/g,'/').replace(/^\.\//,''),parseYaml,stringifyYaml,getFrontMatterInfo};
const sandbox={module:{exports:{}},require:n=>n==='obsidian'?api:require(n),console,setTimeout,clearTimeout};
vm.runInNewContext(fs.readFileSync(path.join(root,'.obsidian/plugins/academic-library-helper/main.js'),'utf8'),sandbox);
const instance=new sandbox.module.exports();
instance.app={vault,workspace:{onLayoutReady:()=>{}},metadataCache:{getFirstLinkpathDest:(target,source)=>file(target)||all().find(f=>f.path.endsWith('/'+target)||f.path===target)},fileManager:{processFrontMatter:async(f,fn)=>{const p=path.join(root,f.path),t=fs.readFileSync(p,'utf8'),info=getFrontMatterInfo(t),fm=info.exists?(parseYaml(info.frontmatter)||{}):{};fn(fm);fs.writeFileSync(p,'---\n'+stringifyYaml(fm)+'---\n'+t.slice(info.contentStart));}}};
(async()=>{
 await instance.onload();await instance.sync();
 const pdf='10 文献/PDF/001 测试.pdf';fs.writeFileSync(path.join(root,pdf),'%PDF-1.4 fixture');
 await instance.sync();
 const home=instance.data.records[pdf];assert(home);
 fs.appendFileSync(path.join(root,home),'\nPERSONAL KEEP\n');
 await instance.app.fileManager.processFrontMatter(file(home),fm=>{fm.tags=['主题/测试'];fm.status='在读';fm.title='测试';fm.paper_number=1;});
 const fm=metadataLocal(fs.readFileSync(path.join(root,home),'utf8'));
 const ai='10 文献/AI辅助阅读/001 AI.md';
 fs.writeFileSync(path.join(root,ai),'---\nreference_id: '+fm.reference_id+'\n---\n## 一句话总结\n\nTest summary\n');
 await instance.sync();await instance.sync();
 assert.equal(all().filter(f=>f.path.startsWith('10 文献/阅读笔记/')).length,1);
 assert(fs.readFileSync(path.join(root,home),'utf8').includes('PERSONAL KEEP'));
 assert(fs.readFileSync(path.join(root,home),'utf8').includes('#一句话总结]]'));
 const index=fs.readFileSync(path.join(root,'10 文献/文献目录.md'),'utf8');
 assert(index.includes('001 测试'));
 assert(index.includes('001 AI')&&index.includes('在读')&&!index.includes('关联项目'));
 assert(fs.readFileSync(path.join(root,'10 文献/标签索引.md'),'utf8').includes('主题/测试 · 1 篇'));
 assert(!fs.existsSync(path.join(root,'99 系统与附件')));assert(!notices.length);
 console.log('PASS: PDF auto-homepage, repeat scan, personal prose, AI linking/summary, tags and reading-only columns');
})().catch(e=>{console.error(e);process.exitCode=1;});
function metadataLocal(text){return parseYaml(getFrontMatterInfo(text).frontmatter);}
