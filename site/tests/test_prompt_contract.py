"""Contract regressions: reject broken cards and stale exports, accept valid v2."""
from pathlib import Path
import hashlib
import json
import sys
import tempfile
import unittest
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import check_prompt_contract as c
SPEC=json.loads((c.ROOT/'site/prompt-contract.json').read_text('utf-8-sig'))

def sample(kind='transfer', rendered=False):
    task='请阅读 {模型说明材料}，列出方程与未知量。'
    material='{模型说明材料}：上传文件名或粘贴的设定。'
    if kind=='exercise':
        task='请阅读已提供的无通勤两地区模型说明，复查人口守恒。'
        material='<a href="model.md">模型说明</a>'
    block=lambda text: '<pre><code>'+text+'</code></pre>' if rendered else '```text\n'+text+'\n```'
    roles={'materials':material,'scope':'适用于已有静态均衡设定；检查是否存在新增市场。','task':block(task),'checks':'核对未知量、单位与市场条件。'}
    if kind=='transfer':roles['example']=block('材料为我上传的模型说明；先列出未知量。')
    body=''.join(f'<div data-prompt-role="{role}">\n\n{text}\n\n</div>' for role,text in roles.items())
    return f'<details id="agent-test" data-prompt-kind="{kind}" class="agent-prompt"><summary>Agent · {SPEC["kinds"][kind]}：核对模型</summary><div class="agent-prompt-body">{body}</div></details>'

def css():
    values=[]
    for role,pair in SPEC['colors'].items():
        values.extend(f'--qsm-{role}-{suffix}:{pair[key]};' for suffix,key in [('fg','foreground'),('bg','background')])
    return ':root {'+''.join(values)+f'--qsm-focus:{SPEC["focus"]};'+'}'

class Cards(unittest.TestCase):
    def issues(self,text):return c.inspect_cards(text,SPEC)[0]
    def test_valid_two_kinds(self):
        for kind in SPEC['kinds']:self.assertEqual(self.issues(sample(kind)),[])
    def test_source_rendered_payload(self):
        self.assertEqual(c.inspect_cards(sample(),SPEC)[1],c.inspect_cards(sample(rendered=True),SPEC)[1])
    def test_untyped_card_rejected(self):
        self.assertTrue(self.issues(sample().replace('data-prompt-kind="transfer"','')))
    def test_open_rejected(self):
        self.assertTrue(self.issues(sample().replace('<details ','<details open ')))
    def test_duplicate_id_rejected(self):self.assertTrue(self.issues(sample()+sample()))
    def test_missing_scope_rejected(self):
        self.assertTrue(self.issues(sample().replace('data-prompt-role="scope"','data-unused="scope"')))
    def test_undocumented_field_rejected(self):
        self.assertTrue(self.issues(sample().replace('请阅读 {模型说明材料}','请阅读 {其他材料}')))
    def test_site_dependency_rejected(self):
        for term in ['本章','M2','model.md','本站']:
            self.assertTrue(self.issues(sample().replace('请阅读 {模型说明材料}',f'请阅读 {term} 和 {{模型说明材料}}')))
    def test_example_may_name_chapter(self):
        self.assertEqual(self.issues(sample().replace('材料为我上传的模型说明','材料为 M2 的 model.md')),[])
    def test_separate_example_required(self):
        self.assertTrue(self.issues(sample().replace('data-prompt-role="example"','data-unused="example"')))
    def test_copy_button_in_summary_rejected(self):
        self.assertTrue(self.issues(sample().replace('</summary>','<button>复制</button></summary>')))
    def test_exercise_resource_required(self):
        self.assertTrue(self.issues(sample('exercise').replace('<a href="model.md">模型说明</a>','模型说明')))
    def test_palette(self):self.assertEqual(c.check_palette(SPEC,css()),[])
    def test_conflicting_token_rejected(self):
        self.assertTrue(c.check_palette(SPEC,css()+' :root {--qsm-transfer-fg:#FFFFFF;}'))
    def test_low_contrast_rejected(self):
        spec=json.loads(json.dumps(SPEC));spec['colors']['transfer']['foreground']='#EFE8F6'
        self.assertTrue(any('contrast' in x for x in c.check_palette(spec,css())))

class CompleteFixture(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        def write(rel,text):
            p=self.root/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text,encoding='utf-8',newline='\n');return p
        self.write=write
        write('site/prompt-contract.json',json.dumps(SPEC));write('site/styles.css',css())
        write(SPEC['guide_source'],'Guide');write('_site/'+SPEC['guide'],'Guide')
        for slug,article,base in c.CHAPTERS:
            src=sample()+'\n[使用指南](agent-guide.html)'
            nb=json.dumps({'cells':[{'cell_type':'markdown','source':src.splitlines(keepends=True)}]},ensure_ascii=False)
            write(f'site/pages/{slug}.ipynb',nb)
            write(f'_site/site/pages/{slug}.html',sample(rendered=True))
            write(f'articles/{article}/downloads/{base}.ipynb',nb)
            item=c.inspect_cards(sample(),SPEC)[1][0]
            task=item[2]+'\n'+item[3]
            self.resources={'prompts/guided-prompts.md':task.encode('utf-8'),SPEC['offline_guide']:b'Guide'}
            for name,data in self.resources.items():
                write(f'articles/{article}/{name}',data.decode('utf-8'))
                write(f'_site/articles/{article}/{name}',data.decode('utf-8'))
            for name in [base+'-workbook.zip',base+'-agent-inputs.zip']:
                archive=self.root/f'articles/{article}/downloads/{name}'
                with zipfile.ZipFile(archive,'w') as z:
                    for rel,data in self.resources.items():z.writestr(rel,data)
                    if name.endswith('agent-inputs.zip'):
                        z.writestr('input-manifest.json',json.dumps({k:hashlib.sha256(v).hexdigest() for k,v in self.resources.items()}))
                built=self.root/f'_site/articles/{article}/downloads/{name}'
                built.parent.mkdir(parents=True,exist_ok=True);built.write_bytes(archive.read_bytes())
    def tearDown(self):self.tmp.cleanup()
    def test_complete_v2_passes(self):self.assertEqual(c.check(self.root),[])
    def test_rendered_task_drift_rejected(self):
        self.write('_site/site/pages/m1-baseline.html',sample(rendered=True).replace('列出方程与未知量','直接编造答案'))
        self.assertTrue(any('source/rendered' in x for x in c.check(self.root)))
    def test_stale_archive_rejected(self):
        path=self.root/'articles/p05-commuting-qsm/downloads/commuting-workbook.zip'
        with zipfile.ZipFile(path,'w') as z:z.writestr('prompts/guided-prompts.md','stale')
        self.assertTrue(any('archive mismatch' in x for x in c.check(self.root)))
    def test_input_package_cannot_include_answers(self):
        path=self.root/'articles/p06-transport-qsm/downloads/transport-agent-inputs.zip'
        with zipfile.ZipFile(path,'a') as z:z.writestr('code/reference.py','answer=42')
        self.assertTrue(any('forbidden implementation' in x for x in c.check(self.root)))
    def test_rendered_example_drift_rejected(self):
        self.write('_site/site/pages/m1-baseline.html',sample(rendered=True).replace('材料为我上传的模型说明','另一个不匹配的示例'))
        self.assertTrue(any('source/rendered' in x for x in c.check(self.root)))
    def test_stale_guide_source_rejected(self):
        self.write(SPEC['guide_source'],'New authored guide')
        self.assertTrue(any('offline guide differs' in x for x in c.check(self.root)))
    def test_missing_guide_rejected(self):
        (self.root/SPEC['guide_source']).unlink()
        self.assertTrue(any('guide missing' in x for x in c.check(self.root)))
    def test_manifest_drift_rejected(self):
        path=self.root/'articles/p06-transport-qsm/downloads/transport-agent-inputs.zip'
        with zipfile.ZipFile(path,'w') as z:
            for rel,data in self.resources.items():z.writestr(rel,data)
            z.writestr('input-manifest.json','{}')
        self.assertTrue(any('manifest mismatch' in x for x in c.check(self.root)))

if __name__=='__main__':unittest.main()

