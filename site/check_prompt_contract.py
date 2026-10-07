"""Read-only v2 prompt contract audit (standard library; no model execution).

Default is strict (nonzero on gaps). --audit inventories unfinished migration,
returns zero, and explicitly does NOT certify acceptance. Browser/manual review
is required separately. No imports from generation scripts, writes or network.
"""
from pathlib import Path
from html.parser import HTMLParser
import argparse
import hashlib
import json
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]
CHAPTERS = [('m1-baseline', 'p04-minimal-qsm', 'baseline'),
            ('m2-commuting', 'p05-commuting-qsm', 'commuting'),
            ('m3-transport-policy', 'p06-transport-qsm', 'transport')]
VOID = {'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}

class Node:
    def __init__(self, tag='', attrs=None):
        self.tag, self.attrs, self.children = tag, dict(attrs or []), []
    def text(self):
        return ''.join(c.text() if isinstance(c, Node) else c for c in self.children)
    def find(self, predicate):
        result = [self] if predicate(self) else []
        for child in self.children:
            if isinstance(child, Node): result.extend(child.find(predicate))
        return result

class Tree(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.root = Node(); self.stack = [self.root]; self.feed(text)
    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs); self.stack[-1].children.append(node)
        if tag not in VOID: self.stack.append(node)
    def handle_endtag(self, tag):
        for i in range(len(self.stack)-1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]; break
    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID: self.handle_endtag(tag)
    def handle_data(self, data): self.stack[-1].children.append(data)

def cards(text):
    return Tree(text).root.find(lambda n: n.tag == 'details' and 'agent-prompt' in n.attrs.get('class','').split())

def norm(text): return text.replace('\r\n','\n').strip()

def blocks(node):
    pres = node.find(lambda n: n.tag == 'pre')
    if pres: return [norm(n.text()) for n in pres]
    return [norm(x) for x in re.findall(r'```text\s*\n(.*?)\n```', node.text(), re.S)]

def inspect_cards(text, spec):
    errors = []; found = cards(text); payload = []; ids = set()
    for card in found:
        ident = card.attrs.get('id',''); prefix = ident or '(missing id)'
        if not ident or ident in ids: errors.append(prefix+': missing/duplicate card id')
        ids.add(ident)
        if 'open' in card.attrs: errors.append(prefix+': must be collapsed')
        if card.find(lambda n: n is not card and n.tag == 'details'):
            errors.append(prefix+': nested disclosure is not supported')
        kind = card.attrs.get('data-prompt-kind','')
        if kind not in spec['kinds']:
            errors.append(prefix+': missing/invalid data-prompt-kind'); continue
        summaries = [n for n in card.children if isinstance(n,Node) and n.tag=='summary']
        if len(summaries)!=1 or spec['kinds'][kind] not in summaries[0].text():
            errors.append(prefix+': summary must name its kind')
        if summaries and summaries[0].find(lambda n: n.tag in ('button','a')):
            errors.append(prefix+': summary must not contain links/copy buttons')
        roles = {}
        for node in card.find(lambda n: 'data-prompt-role' in n.attrs):
            role = node.attrs['data-prompt-role']
            if role in roles: errors.append(prefix+': duplicate role '+role)
            roles[role] = node
        required = spec['roles'] + (spec['transfer_roles'] if kind=='transfer' else [])
        for role in required:
            if role not in roles or not roles[role].text().strip():
                errors.append(prefix+': missing/empty '+role)
        task_blocks = blocks(roles['task']) if 'task' in roles else []
        if len(task_blocks)!=1 or not task_blocks[0]:
            errors.append(prefix+': task requires one nonempty text block'); continue
        task = task_blocks[0]
        if kind=='transfer':
            fields = re.findall(r'\{([^{}\n]+)\}', task)
            if not fields: errors.append(prefix+': transfer task needs {placeholders}')
            if re.search(r'本章|本站|本讲义|上一章|下一章|\b[MP][1-9]\d*\b|\bmodel\.md\b',task):
                errors.append(prefix+': transfer task contains site-specific dependency')
            material = roles.get('materials',Node()).text()
            for field in set(fields):
                if '{'+field+'}' not in material:
                    errors.append(prefix+': undocumented placeholder {'+field+'}')
            if 'example' in roles and (len(blocks(roles['example']))!=1 or not blocks(roles['example'])[0]):
                errors.append(prefix+': example requires one separate nonempty text block')
        else:
            material = roles.get('materials',Node())
            if not material.find(lambda n: n.tag=='a' and n.attrs.get('href')) and not re.search(r'\]\([^)]+\)',material.text()):
                errors.append(prefix+': exercise materials require an explicit resource link')
        example_blocks = blocks(roles['example']) if 'example' in roles else []
        payload.append((ident,kind,task,example_blocks[0] if len(example_blocks)==1 else ''))
    if not found: errors.append('no Agent cards')
    return errors,payload

def luminance(color):
    values=[int(color[i:i+2],16)/255 for i in (1,3,5)]
    values=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in values]
    return sum(a*b for a,b in zip(values,[.2126,.7152,.0722]))

def contrast(a,b):
    low,high=sorted([luminance(a),luminance(b)])
    return (high+.05)/(low+.05)

def check_palette(spec, css):
    errors=[]
    for role, pair in spec['colors'].items():
        if contrast(pair['foreground'],pair['background'])<4.5:
            errors.append('palette: insufficient text contrast: '+role)
        for suffix,key in [('fg','foreground'),('bg','background')]:
            token='--qsm-'+role+'-'+suffix
            matches=re.findall(re.escape(token)+r'\s*:\s*(#[0-9a-fA-F]{6})\s*[;}]',css)
            if not matches or any(m.lower()!=pair[key].lower() for m in matches):
                errors.append('CSS: missing/conflicting token '+token)
    matches=re.findall(r'--qsm-focus\s*:\s*(#[0-9a-fA-F]{6})\s*[;}]',css)
    if not matches or any(x.lower()!=spec['focus'].lower() for x in matches):
        errors.append('CSS: missing/conflicting --qsm-focus')
    return errors

def offline_guide_text(source):
    """Canonical path conversion for the single authored usage guide."""
    guide=re.sub(r'^---\n.*?\n---\n','# 怎样使用 Agent 提示词？\n',source,flags=re.S)
    return re.sub(r'(?<=\()([\w-]+)\.(?:qmd|ipynb)(?=[)#])',r'https://lianxhcn.github.io/qsm101/site/pages/\1.html',guide)

def markdown(nb): return '\n'.join(''.join(c['source']) for c in nb['cells'] if c['cell_type']=='markdown')

def check(root=ROOT):
    spec=json.loads((root/'site/prompt-contract.json').read_text('utf-8-sig'))
    errors=check_palette(spec,(root/'site/styles.css').read_text('utf-8-sig'))
    for rel in [spec['guide_source'],'_site/'+spec['guide']]:
        if not (root/rel).is_file(): errors.append('guide missing: '+rel)
    for slug,article,base in CHAPTERS:
        try:
            nb=json.loads((root/f'site/pages/{slug}.ipynb').read_text('utf-8-sig'))
            source=markdown(nb)
            issues,payload=inspect_cards(source,spec)
            errors.extend(slug+': '+e for e in issues)
            if 'agent-guide.' not in source: errors.append(slug+': missing shared usage guide link')
            rendered=(root/f'_site/site/pages/{slug}.html').read_text('utf-8-sig')
            issues,built_payload=inspect_cards(rendered,spec)
            errors.extend(slug+' HTML: '+e for e in issues)
            if payload!=built_payload: errors.append(slug+': source/rendered task content differs')
            folder=root/'articles'/article
            dl=folder/'downloads'/f'{base}.ipynb'
            issues,offline_payload=inspect_cards(markdown(json.loads(dl.read_text('utf-8-sig'))),spec)
            errors.extend(slug+' download: '+e for e in issues)
            if payload!=offline_payload: errors.append(slug+': source/download task content differs')
            guided=(folder/'prompts/guided-prompts.md').read_bytes()
            for ident,kind,task,example in payload:
                for label,text in [('task',task),('example',example)]:
                    if text and norm(text) not in norm(guided.decode('utf-8-sig')):
                        errors.append(slug+': guided export missing '+label+' '+ident)
            guide=folder/spec['offline_guide']
            if not guide.is_file(): errors.append(slug+': missing offline usage guide')
            elif (root/spec['guide_source']).is_file():
                expected_guide=offline_guide_text((root/spec['guide_source']).read_text('utf-8-sig')).encode('utf-8')
                if guide.read_bytes()!=expected_guide: errors.append(slug+': offline guide differs from authored source')
            expected={'prompts/guided-prompts.md':guided}
            if guide.is_file():expected[spec['offline_guide']]=guide.read_bytes()
            for name,data in expected.items():
                built=root/'_site/articles'/article/name
                if not built.is_file() or built.read_bytes()!=data:
                    errors.append(slug+': stale/missing rendered resource '+name)
            archives=[folder/'downloads'/f'{base}-workbook.zip']+list((folder/'downloads').glob('*-agent-inputs.zip'))
            for archive in archives:
                with zipfile.ZipFile(archive) as z:
                    if archive.name.endswith('-agent-inputs.zip'):
                        for member in z.namelist():
                            if Path(member).suffix.lower() in ('.py','.ipynb') or member.startswith(('code/','results/')):
                                errors.append(slug+': forbidden implementation/output in input-only archive: '+member)
                    for name,data in expected.items():
                        if name not in z.namelist() or z.read(name)!=data:
                            errors.append(slug+': archive mismatch '+archive.name+' / '+name)
                    if 'input-manifest.json' in z.namelist():
                        manifest=json.loads(z.read('input-manifest.json'))
                        for name,data in expected.items():
                            if manifest.get(name)!=hashlib.sha256(data).hexdigest():
                                errors.append(slug+': manifest mismatch '+name)
                built=root/'_site'/archive.relative_to(root)
                if not built.is_file() or built.read_bytes()!=archive.read_bytes():
                    errors.append(slug+': rendered archive stale '+archive.name)
        except (OSError,ValueError,KeyError,zipfile.BadZipFile) as exc:
            errors.append(slug+': input failure: '+str(exc))
    return errors

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audit',action='store_true',help='Inventory gaps only; NOT acceptance; exit 0 on gaps.')
    parser.add_argument('--json',action='store_true',help='Emit result to stdout; does not write a report.')
    args=parser.parse_args();errors=check()
    status='PENDING' if errors else 'STATIC_PASS'
    if args.json: print(json.dumps({'mode':'audit' if args.audit else 'strict','status':status,'gaps':errors,'manual_review_required':True},ensure_ascii=False,indent=2))
    else:
        print(f'{status}: {len(errors)} gap(s); '+('AUDIT ONLY, not acceptance.' if args.audit else 'strict v2 static check.'))
        for e in errors:print('- '+e)
        print('Browser checks and economic/standalone-context review remain separate.')
    return 0 if args.audit or not errors else 1

if __name__=='__main__':raise SystemExit(main())
