from pathlib import Path
import shutil
root=Path(__file__).resolve().parent.parent
src=root/'test-tools'; dst=root/'work'/'run-tools'
shutil.copytree(src,dst,ignore=shutil.ignore_patterns('.git'),dirs_exist_ok=True)
for p in dst.rglob('*'):
    if p.suffix in ('.py','.js'):
        s=p.read_text(encoding='utf-8').replace('/home/claude/nagoya-trip',(root/'app-source').as_posix()).replace('/home/claude/build',dst.as_posix()).replace('/tmp/',(root/'work'/'tmp').as_posix()+'/')
        p.write_text(s,encoding='utf-8')
(dst/'mock').mkdir(exist_ok=True)
for name in ('app.js','fs.js'):shutil.copyfile(dst/'ft'/name,dst/'mock'/name)
print('Prepared test copies:',dst)
