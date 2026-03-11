import sys
import subprocess
import codecs

sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'replace')

def run_cmd(cmd):
    try:
        import os
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            env=env
        )
        return result.stdout + result.stderr
    except Exception as e:
        return str(e)

with open("out_api.txt", "w", encoding="utf-8") as f:
    output = run_cmd('python scripts/run.py ask_question.py --question "Google NotebookLM 是否有公开的 API 可以调用？如果有，如何获取和使用？如果没有，有什么替代方案？" --notebook-url "https://notebooklm.google.com/notebook/bcf73eee-8d13-4c2f-a894-12b8e21989c4"')
    f.write(output)
