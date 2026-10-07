"""Read-only acceptance checks for the QSM website and synchronized downloads.

Uses the standard library so GitHub Actions does not need extra packages.
No imports from generation scripts, no network requests, no file writes.
"""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import json, re, zipfile, sys, ast, argparse
from check_prompt_contract import cards, check as check_prompt_contract

ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/'_site'
CHAPTERS=[('m1-baseline','p04-minimal-qsm','baseline','M1：无通勤基准模型'),('m2-commuting','p05-commuting-qsm','commuting','M2：加入跨地区通勤'),('m3-transport-policy','p06-transport-qsm','transport','M3：通勤成本变化')]
PAGES=['index.html']+['site/pages/'+s+'.html' for s in ['foundations','reading','m1-baseline','m2-commuting','m3-transport-policy','evidence','faq','updates','about','agent-guide']]
class Page(HTMLParser):
    def __init__(self,text):
        super().__init__();self.refs=[];self.ids=set();self.main=False;self.images=[];self.equations=0;self.eqids=set();self.figids=set();self.tblids=set();self.caption_count=0;self.tables=0;self.visible=[];self.mainrefs=[];self.python=0;self.open_code=0;self.agent_cards=[];self.open_agents=0;self.feed(text)
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='main':self.main=True
        if a.get('id'):self.ids.add(a['id'])
        for key in ['href','src']:
            if a.get(key):self.refs.append(a[key])
        if not self.main:return
        ident=a.get('id','')
        if ident.startswith('eq-'):self.eqids.add(ident)
        if ident.startswith('fig-') and '-caption-' not in ident:self.figids.add(ident)
        if ident.startswith('tbl-') and '-caption-' not in ident:self.tblids.add(ident)
        if tag=='img':self.images.append(a)
        if tag=='a' and 'lightbox' in a.get('class','').split():self.mainrefs.append(a.get('href',''))
        if 'math display' in a.get('class',''):self.equations+=1
        if tag=='table':self.tables+=1
        if tag=='figcaption' and 'quarto-float-tbl' in a.get('class',''):self.caption_count+=1
        if tag=='details' and 'agent-prompt' in a.get('class','').split():
            self.agent_cards.append(a.get('id',''))
            if 'open' in a:self.open_agents+=1
        if tag=='details' and 'code-fold' in a.get('class','') and 'open' in a:self.open_code+=1
    def handle_endtag(self,tag):
        if tag=='main':self.main=False
    def handle_data(self,data):
        if self.main:self.visible.append(data)

def check():
    errors=[];parsed={}
    for rel in PAGES:
        path=SITE/rel
        if not path.exists():errors.append(f'Missing page: {rel}');continue
        text=path.read_text('utf-8');p=Page(text);parsed[path.resolve()]=p
        visible=' '.join(p.visible)
        if re.search(r'\bP0[1-9]\b|dml050|Windows 沙箱|Codex CLI 0\.144',visible):errors.append(f'{rel}: internal prose leaked')
        if re.search(r'\?@(?:eq|fig|tbl)-',text):errors.append(f'{rel}: unresolved cross-reference')
        if p.open_agents:errors.append(f'{rel}: Agent cards opened by default')
        if p.open_code:errors.append(f'{rel}: Python code opened by default')
        if p.equations!=len(p.eqids):errors.append(f'{rel}: {p.equations} display math / {len(p.eqids)} equation labels')
        if p.tables!=len(p.tblids):errors.append(f'{rel}: {p.tables} tables / {len(p.tblids)} stable table labels')
        for image in p.images:
            if not image.get('alt'):errors.append(f'{rel}: image without alt')
            if image.get('src') not in p.mainrefs:errors.append(f'{rel}: image without in-page lightbox: {image.get("src")}')
        if 'https://www.lianxh.cn/qsm.html' not in text:errors.append(f'{rel}: missing course link')
        if re.search(r'(?:作者|邮箱)[：:]|\*\*Title\*\*|\*\*Keywords\*\*',visible):errors.append(f'{rel}: publication header leaked')
    # Resolve both relative and same-site absolute paths, including deep links.
    for path,p in parsed.items():
        for ref in p.refs:
            u=urlsplit(ref)
            if u.scheme in ['mailto','data','javascript','tel']:continue
            if u.netloc and u.netloc!='lianxhcn.github.io':continue
            name=unquote(u.path)
            if u.netloc:
                if not name.startswith('/qsm101/'):continue
                name=name[len('/qsm101'):]
            target=(SITE/name.lstrip('/') if name.startswith('/') else path.parent/name).resolve() if name else path
            if target.is_dir():target/= 'index.html'
            if not target.exists():errors.append(f'{path.relative_to(SITE)}: missing {ref}');continue
            if target.suffix=='.html' and u.fragment:
                q=parsed.get(target)
                if q is None:q=Page(target.read_text('utf-8'));parsed_target=q
                if unquote(u.fragment) not in q.ids:errors.append(f'{path.relative_to(SITE)}: missing anchor {ref}')
    for old in ['laboratory','commuting','transport','counterfactual']:
        if (SITE/f'site/pages/{old}.html').exists():errors.append(f'Obsolete page still present: {old}')
    for slug,article,base,title in CHAPTERS:
        src=ROOT/f'site/pages/{slug}.ipynb';nb=json.loads(src.read_text('utf-8'))
        joined='\n'.join(''.join(c['source']) for c in nb['cells'] if c['cell_type']=='markdown')
        expected_cards=[c.attrs.get('id','') for c in cards(joined)]
        rendered=parsed.get((SITE/f'site/pages/{slug}.html').resolve())
        if not expected_cards or rendered is None or expected_cards!=rendered.agent_cards:
            errors.append(f'{slug}: inline Agent cards missing or out of sync')
        guided=ROOT/f'articles/{article}/prompts/guided-prompts.md'
        if not guided.exists():errors.append(f'{slug}: guided prompt download missing')
        for required in [title,'开始之前','离线运行','下载本章 Notebook','下载离线练习包']:
            if required not in joined:errors.append(f'{slug}: missing {required}')
        for cell in nb['cells']:
            if cell['cell_type']=='code':
                if cell.get('execution_count') is None:errors.append(f'{slug}: unexecuted code')
                if any(o.get('output_type')=='error' for o in cell.get('outputs',[])):errors.append(f'{slug}: error output')
        dl=ROOT/f'articles/{article}/downloads/{base}.ipynb'
        if not dl.exists():errors.append(f'{slug}: missing download');continue
        dnb=json.loads(dl.read_text('utf-8'))
        source_code=[c for c in nb['cells'] if c['cell_type']=='code'];download_code=[c for c in dnb['cells'] if c['cell_type']=='code']
        if source_code!=download_code:errors.append(f'{slug}: code/output differs in download')
        source_math=re.findall(r'\$\$.*?\$\$',joined,re.S)
        download_math=re.findall(r'\$\$.*?\$\$','\n'.join(''.join(c['source']) for c in dnb['cells'] if c['cell_type']=='markdown'),re.S)
        if source_math!=download_math:errors.append(f'{slug}: math differs in download')
        with zipfile.ZipFile(dl.with_name(base+'-workbook.zip')) as z:
            if z.read(base+'.ipynb')!=dl.read_bytes():errors.append(f'{slug}: stale zip notebook')
            for required in ['README.md','requirements.txt','model.md']:
                if required not in z.namelist():errors.append(f'{slug}: workbook missing {required}')
            # Offline prose must not point at missing local figures or attachments.
            for cell in dnb['cells']:
                if cell['cell_type']!='markdown':continue
                for match in re.finditer(r'\]\((<[^>]+>|[^)]+)\)', ''.join(cell['source'])):
                    link=urlsplit(match[1].strip('<>'))
                    if not link.scheme and link.path and link.path not in z.namelist():
                        errors.append(f'{slug}: workbook link missing {link.path}')
            if not any(x.startswith('data/') and x.endswith('.csv') for x in z.namelist()):errors.append(f'{slug}: workbook lacks data')
        built=SITE/dl.relative_to(ROOT)
        if not built.exists() or built.read_bytes()!=dl.read_bytes():errors.append(f'{slug}: rendered download stale')
    return errors

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prompt-contract',choices=['current','audit','strict'],default='current',
                        help='current: existing site checks only; audit: inventory v2 gaps; strict: require v2.')
    args=parser.parse_args()
    failures=check()
    if args.prompt_contract!='current':
        gaps=check_prompt_contract()
        print(f'Prompt v2 {args.prompt_contract}: {len(gaps)} gap(s).')
        for gap in gaps: print('- '+gap)
        if args.prompt_contract=='strict': failures.extend(gaps)
        elif gaps: print('PENDING: audit is not v2 acceptance.')
    else:
        print('Scope: current checks only; prompt v2 not checked. Use --prompt-contract strict for migration acceptance.')
    if failures:
        print('\n'.join(failures),file=sys.stderr);raise SystemExit(1)
    print('PASS within selected scope: pages, links, labels, folding and synchronized workbooks. Browser and manual review remain separate.')
