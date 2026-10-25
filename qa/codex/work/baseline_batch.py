import concurrent.futures,json,os,subprocess,time
from pathlib import Path
root=Path(__file__).resolve().parent.parent
names='duetest fabtest packtest gotest buytest cashtest sostest undotest sorttest janktest setuptest tourtest tftest placetest reviewtest fxtest nexttest hometest sostabtest voicetest sheettest'.split()
targets=[root/'work'/'run-tools'/'ft'/(n+'.py') for n in names]+[root/'work'/'run-tools'/'sweep.py',root/'work'/'run-tools'/'t5.py']
out=root/'outputs'/'baseline';out.mkdir(exist_ok=True)
env=os.environ.copy();env['PYTHONUTF8']='1';env['TEMP']=env['TMP']=str(root/'work'/'tmp')
def run(target):
    t=time.perf_counter()
    with (out/(target.stem+'.log')).open('wb') as f:
        try:r=subprocess.run([str(root/'work'/'python'/'python.exe'),'-X','utf8',str(root/'work'/'run_test.py'),str(target)],stdout=f,stderr=subprocess.STDOUT,env=env,timeout=240);code=r.returncode
        except subprocess.TimeoutExpired:code='timeout'
    result={'test':target.stem,'exit':code,'seconds':round(time.perf_counter()-t,2)}
    print(json.dumps(result),flush=True);return result
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(run,targets))
(out/'summary.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
