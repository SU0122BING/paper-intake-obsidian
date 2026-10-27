import importlib.util,json,tempfile,unittest,hashlib,argparse
from pathlib import Path
import pymupdf
spec=importlib.util.spec_from_file_location('intake',Path(__file__).resolve().parents[1]/'skills/paper-intake/scripts/intake.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class IntakeTest(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.base=Path(self.tmp.name);self.root=self.base/'vault';self.root.mkdir()
  for d in [m.NOTE_DIR,m.PDF_DIR,'10 文献/AI辅助阅读/example/images','90 模板']:(self.root/d).mkdir(parents=True,exist_ok=True)
  (self.root/'90 模板/文献阅读模板.md').write_text('---\ntype: literature\ntags: []\n---\n# {{title}}\n\n- PDF：将库中的 PDF 拖到这里\n\n## AI 阅读参考\n\n<!-- academic-ai:slot -->\n\n## 我的理解与质疑\n\nPERSONAL NOTE KEEP\n')
  self.pdf=self.base/'source.pdf';doc=pymupdf.open();doc.new_page().insert_text((72,72),'Integration test only');doc.save(self.pdf);doc.close()
  self.note=self.root/'10 文献/AI辅助阅读/example/note.zh-CN.md'
  self.note.write_text('---\ntags: ["主题/测试"]\ndoi: "10.1000/test"\n---\n# Integration fixture\n\n## 一句话总结\n\nIntegration test, not a scholarly analysis.\n\n![test](images/figure.png)\n')
  (self.note.parent/'images/figure.png').write_bytes(b'test-image-path-fixture')
  self.source_hash=m.sha(self.pdf);self.note_hash=m.sha(self.note)
  self.sidecar=self.note.parent/'.deeppapernote.json';m.write_json(self.sidecar,{'schema_version':2,'sources':{self.source_hash:{'notes':{'zh-CN':{'filename':self.note.name,'note_sha256':self.note_hash}}}}})
  objects={'manifest':{'source_sha256':self.source_hash,'pdf':{'path':str(self.pdf)},'title':'Integration Test'},'save':{'status':'ok','script':'write_obsidian_note.py','output_mode':'obsidian','output_language':'zh-CN','note_path':str(self.note),'source_sha256':self.source_hash,'sidecar_path':str(self.sidecar)},'lint':{'note_sha256':self.note_hash,'output_language':'zh-CN','passes_basic_structure':True,'passes_style_gate':True,'passes_math_gate':True},'review':{'note_sha256':self.note_hash,'final_quality_review':True,'final_readability_review':True}}
  for k,v in objects.items():m.write_json(self.base/(k+'.json'),v)
  self.args=argparse.Namespace(source_manifest=str(self.base/'manifest.json'),save_result=str(self.base/'save.json'),lint_json=str(self.base/'lint.json'),review_json=str(self.base/'review.json'),doi='10.1000/test',title=None,tags=None)
 def tearDown(self):self.tmp.cleanup()
 def test_register_repeat_and_preservation(self):
  first=m.register(self.root,self.args);home=Path(first['source_note']);fm,body=m.split(home.read_text());fm['tags']=['主题/自定'];fm['status']='精读';home.write_text(m.compose(fm,body+'\nMY EXTRA THOUGHTS\n'))
  second=m.register(self.root,self.args);self.assertEqual(first['reference_id'],second['reference_id']);self.assertEqual(len(list((self.root/m.NOTE_DIR).glob('*.md'))),1);self.assertEqual(m.sha(self.note),self.note_hash)
  m.refresh(self.root);fm,body=m.split(home.read_text());self.assertEqual(fm['tags'],['主题/自定']);self.assertEqual(fm['status'],'精读');self.assertIn('MY EXTRA THOUGHTS',body);self.assertIn('note.zh-CN',body);self.assertEqual(m.sha(self.note),self.note_hash)
  self.assertIn('主题/自定 · 1 篇',(self.root/'10 文献/标签索引.md').read_text())
 def test_changed_note_rejected_without_registering(self):
  self.note.write_text(self.note.read_text()+'changed')
  with self.assertRaisesRegex(ValueError,'lint'):m.register(self.root,self.args)
  self.assertFalse((self.root/m.REGISTRY).exists())
 def test_missing_image_rejected(self):
  (self.note.parent/'images/figure.png').unlink()
  with self.assertRaisesRegex(ValueError,'Missing'):m.register(self.root,self.args)
  self.assertFalse((self.root/m.REGISTRY).exists())
 def test_existing_hash_reused_without_copy(self):
  existing_pdf=self.root/m.PDF_DIR/'old.pdf';existing_pdf.write_bytes(self.pdf.read_bytes())
  home=self.root/m.NOTE_DIR/'existing.md';home.write_text('---\nreference_id: lit-existing\npdf: "[[10 文献/PDF/old.pdf]]"\ntags: ["主题/原有"]\nstatus: 已读\n---\nEXCERPT KEEP\n')
  result=m.register(self.root,self.args);self.assertEqual(result['reference_id'],'lit-existing');self.assertEqual(Path(result['pdf']),existing_pdf);self.assertEqual(len(list((self.root/m.PDF_DIR).glob('*.pdf'))),1);m.refresh(self.root);self.assertIn('EXCERPT KEEP',home.read_text())
 def test_ambiguous_doi_rejected(self):
  for name in ['a','b']:(self.root/m.NOTE_DIR/(name+'.md')).write_text('---\ndoi: "10.1000/test"\n---\nUser notes\n')
  with self.assertRaisesRegex(ValueError,'Multiple'):m.register(self.root,self.args)
  self.assertFalse((self.root/m.REGISTRY).exists())
 def test_versions_one_paper(self):
  first=m.register(self.root,self.args)
  self.note=self.note.parent/'second.zh-CN.md';self.note.write_text('---\ntags: []\n---\n# Second analysis\n')
  save=m.load(self.base/'save.json');save['note_path']=str(self.note);digest=m.sha(self.note)
  side=m.load(self.sidecar);side['sources'][self.source_hash]['notes']['zh-CN']={'filename':self.note.name,'note_sha256':digest};m.write_json(self.sidecar,side)
  for name in ['lint','review']:
   data=m.load(self.base/(name+'.json'));data['note_sha256']=digest;m.write_json(self.base/(name+'.json'),data)
  m.write_json(self.base/'save.json',save);m.register(self.root,self.args);m.refresh(self.root)
  self.assertEqual(len(m.registry(self.root)['papers']),1)
  self.assertIn('主题/测试 · 1 篇',(self.root/'10 文献/标签索引.md').read_text())
class ReadingOnlyTest(IntakeTest):
 def setUp(self):
  super().setUp()
  self.layout={'registry':'10 文献/阅读工具/论文入库登记.json','template':'10 文献/阅读工具/模板/文献阅读模板.md','reading_only':True}
  m.write_json(self.root/'.obsidian/academic-workbench.json',self.layout)
  target=self.root/self.layout['template'];target.parent.mkdir(parents=True,exist_ok=True)
  (self.root/'90 模板/文献阅读模板.md').replace(target)
  (self.root/'90 模板').rmdir()
 def test_layout(self):
  result=m.register(self.root,self.args);m.refresh(self.root)
  self.assertTrue((self.root/self.layout['registry']).is_file())
  self.assertFalse((self.root/'99 系统与附件').exists())
  self.assertFalse((self.root/'90 模板').exists())
  self.assertNotIn('关联项目',(self.root/'10 文献/文献目录.md').read_text())
  self.assertNotIn('topics',m.split(Path(result['source_note']).read_text())[0])

class NumberDisplayTest(unittest.TestCase):
 def test_prefix(self):
  self.assertEqual(m.display_title({'title':'Title','paper_number':3},'fallback'),'003 Title')
  self.assertEqual(m.display_title({'title':'003 Title','paper_number':3},'fallback'),'003 Title')
  self.assertEqual(m.display_title({'title':'Title'},'fallback'),'Title')

if __name__=='__main__':unittest.main(verbosity=2)
