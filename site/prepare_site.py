"""Synchronize notebook presentation, the M1 QMD, and self-contained workbooks.

Does not execute model code. Run after editing or executing the master notebooks.
HTML captions are derived from stable qsm_tables metadata; numeric cells untouched.
"""
from pathlib import Path
import json, re, shutil, subprocess, zipfile, html, copy, hashlib
from check_prompt_contract import cards, offline_guide_text
ROOT = Path(__file__).resolve().parents[1]
CHAPTERS = [('m1-baseline','p04-minimal-qsm','baseline'),('m2-commuting','p05-commuting-qsm','commuting'),('m3-transport-policy','p06-transport-qsm','transport')]

def present(nb):
    for cell in nb['cells']:
        labels = iter(cell.get('metadata',{}).get('qsm_tables',[]))
        for output in cell.get('outputs',[]):
            data=output.get('data',{})
            markup=''.join(data.get('text/html',[]))
            if '<table' not in markup:
                continue
            label=next(labels)
            markup=re.sub(r'<caption\b[^>]*>.*?</caption>', '',markup,flags=re.S)
            markup=re.sub(r'(<table\b[^>]*?)(?:\s+id="[^"]*")?\s*>',lambda m: re.sub(r'\s+id="[^"]*"','',m[1])+f' id="{label["id"]}"><caption data-qsm-caption="true">{html.escape(label["caption"])}</caption>',markup,count=1)
            data['text/html']=markup.splitlines(keepends=True)
    return nb

def save(nb,path):
    path.write_text(json.dumps(nb,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')

def offline(nb,article):
    nb=copy.deepcopy(nb)
    for cell in nb['cells']:
        if cell['cell_type']!='markdown':continue
        text=''.join(cell['source'])
        text=text.replace(f'../../articles/{article}/downloads/','').replace(f'../../articles/{article}/','')
        text=text.replace('../../docs/setup.md','README.md')
        text=text.replace('](agent-guide.qmd)','](prompts/usage-guide.md)').replace('](agent-guide.html)','](prompts/usage-guide.md)')
        # Existing local originals are included in the workbook; no media download.
        def local_image(match):
            url=match[1];name=url.rsplit('/',1)[-1]
            local=ROOT/'figs/raw'/name
            if not local.exists():local=ROOT/'articles'/article/'figures'/name
            return ']('+('figures/'+name if local.exists() else url)+')'
        text=re.sub(r'\]\((https://fig-lianxh[^)]+)\)',local_image,text)
        # The workbook cannot contain itself; keep its download link public.
        text=re.sub(r'\]\(([^)]+-workbook\.zip)\)',lambda m:'](https://lianxhcn.github.io/qsm101/articles/'+article+'/downloads/'+m[1]+')',text)
        # Other chapters remain links to the final public site, not missing local notebooks.
        text=re.sub(r'(?<=\()((?:m[123]-[\w-]+|faq|reading|foundations|evidence)\.(?:html|ipynb|qmd))',lambda m:'https://lianxhcn.github.io/qsm101/site/pages/'+re.sub(r'\.(?:ipynb|qmd)$','.html',m[1]),text)
        cell['source']=text.splitlines(keepends=True)
    return nb

def main():
    for slug,article,download in CHAPTERS:
        src=ROOT/f'site/pages/{slug}.ipynb';nb=present(json.loads(src.read_text('utf-8')));save(nb,src)
        folder=ROOT/'articles'/article;downloads=folder/'downloads';downloads.mkdir(exist_ok=True)
        # Export structured roles from the authored Notebook; keep task and example separate.
        sections=[]
        for cell in nb['cells']:
            if cell['cell_type']!='markdown':continue
            for block in cards(''.join(cell['source'])):
                title=block.find(lambda n:n.tag=='summary')[0].text().strip()
                roles=block.find(lambda n:'data-prompt-role' in n.attrs)
                body='\n\n'.join(n.text().strip() for n in roles)
                body=body.replace(f'../../articles/{article}/','../')
                body=re.sub(r'../../articles/([^ )]+)',r'https://lianxhcn.github.io/qsm101/articles/\1',body)
                sections.append('## '+title+'\n\n'+body)
        guided='# '+slug+'：随读 Agent 提示词\n\n讲义练习使用给定材料；迁移任务需替换占位符。模板与填写示例分别使用，不要一起复制。先阅读[使用指南](usage-guide.md)。\n\n'+'\n\n'.join(sections)+'\n'
        guide=offline_guide_text((ROOT/'site/pages/agent-guide.qmd').read_text('utf-8-sig'))
        prompts=folder/'prompts';prompts.mkdir(exist_ok=True)
        exports={'prompts/guided-prompts.md':guided.encode('utf-8'),'prompts/usage-guide.md':guide.encode('utf-8')}
        if article=='p05-commuting-qsm':
            exports['models/no-commuting-model.md']=(ROOT/'articles/p04-minimal-qsm/model.md').read_bytes()
        for name,data in exports.items():
            target=folder/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
        # Input-only archives retain their model/data; no reference code or answers added.
        for archive in downloads.glob('*-agent-inputs.zip'):
            with zipfile.ZipFile(archive) as z:
                entries=[(info,z.read(info.filename)) for info in z.infolist() if info.filename not in exports]
            with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
                for info,data in entries:
                    if info.filename=='input-manifest.json':
                        manifest=json.loads(data)
                        for name,payload in exports.items():manifest[name]=hashlib.sha256(payload).hexdigest()
                        data=(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
                    z.writestr(info,data)
                for name,data in exports.items():z.writestr(name,data)
        save(offline(nb,article),downloads/f'{download}.ipynb')
        # Use complete chapter material except the publication article and workbook itself.
        files={f'{download}.ipynb':downloads/f'{download}.ipynb'}
        for dirname in ['data','code','prompts','models','figures','results/reference']:
            for p in (folder/dirname).rglob('*'):
                if p.is_file() and '__pycache__' not in p.parts:files[p.relative_to(folder).as_posix()]=p
        for cell in nb['cells']:
            if cell['cell_type']=='markdown':
                for url in re.findall(r'https://fig-lianxh[^)\s]+', ''.join(cell['source'])):
                    name=url.rsplit('/',1)[-1];image=ROOT/'figs/raw'/name
                    if image.is_file():files['figures/'+name]=image
        for archive in downloads.glob('*-agent-inputs.zip'):
            files[archive.name]=archive
        for filename in ['model.md'  ,'requirements.txt','LICENSE']:
            p=folder/filename
            if p.is_file():files[filename]=p
        if (ROOT/'LICENSE').exists():files.setdefault('LICENSE',ROOT/'LICENSE')
        readme=f'''# {slug} 离线练习包

1. 在已有 Python 环境安装依赖：`python -X utf8 -m pip install -r requirements.txt`。
2. 如环境尚无 Jupyter，安装 `jupyterlab`，然后执行 `jupyter lab`。
3. 打开 `{download}.ipynb`，重启内核并从头执行。保留 Notebook 与 data/ 的相对位置。

代码包含全部模型函数；模型计算不需要联网。课程与文献外链需要网络。
数据为教学构造。参考结果用于对照，不作为计算输入。
网页中的公式和图形编号由 Quarto 生成；Jupyter 主要用于运行与修改参数。
'''
        with zipfile.ZipFile(downloads/f'{download}-workbook.zip','w',zipfile.ZIP_DEFLATED) as z:
            for name,path in sorted(files.items()):
                if name=='requirements.txt':
                    requirements=path.read_text('utf-8-sig')
                    if 'jupyterlab' not in requirements:requirements+='\njupyterlab>=4,<5\n'
                    z.writestr(name,requirements)
                else:z.write(path,name)
            z.writestr('README.md',readme)
        # Keep dependency addition out of numerical reference files; a separate install command is documented.
    quarto=shutil.which('quarto') or r'C:\Program Files\Quarto\bin\quarto.exe'
    subprocess.run([quarto,'convert','site/pages/m1-baseline.ipynb','--output','site/pages/m1-baseline.qmd'],cwd=ROOT,check=True)
    qmd=ROOT/'site/pages/m1-baseline.qmd';text=qmd.read_text('utf-8')
    text=re.sub(r'^#\| execution:.*(?:\n#\|.*)*\n','',text,flags=re.M)
    qmd.write_text(text,'utf-8')

if __name__=='__main__':main()

