import sys
import subprocess
import json
import os
import re
import codecs

# Fix windows console encoding issue
sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'replace')

notebooks = [
    "https://notebooklm.google.com/notebook/bcf73eee-8d13-4c2f-a894-12b8e21989c4",
    "https://notebooklm.google.com/notebook/ac1f7d7a-9b91-4e1b-855c-c3693dab2e11",
    "https://notebooklm.google.com/notebook/4f627d7c-396c-4a5d-9ed4-264260cf19d0",
    "https://notebooklm.google.com/notebook/b88d32e1-cdba-455c-a791-dee90052e8ae"
]

def run_cmd(cmd):
    try:
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

with open("auto_add_log.txt", "w", encoding="utf-8") as f:
    for i, url in enumerate(notebooks):
        f.write(f"\n\n--- Processing {url} ---\n")
        f.flush()
        
        output = run_cmd(f'python scripts/run.py ask_question.py --question "What is the content of this notebook? What topics are covered? Provide a brief summary." --notebook-url "{url}"')
        
        f.write("Output length: " + str(len(output)) + "\n")
        f.write("Raw output snippet:\n" + output[:300] + "...\n" + output[-300:] + "\n")
        f.flush()
        
        # very basic name
        id_part = url.split('/')[-1]
        name = f"Notebook {i+1} ({id_part[:6]})"
        
        # parse answer
        desc = "Notebook content"
        topics = "notebook"
        
        ans_start = output.find("✅ Answer:")
        if ans_start != -1:
            ans_text = output[ans_start + 10:].split('\n\n')[0]
            ans_text = re.sub(r'[*_#]', '', ans_text).replace('\n', ' ').strip()
            desc = ans_text[:120] + "..." if len(ans_text) > 120 else ans_text
            topics = "ai, research, documents"
        elif "Error" not in output:
             desc = "Notebook content retrieved successfully"
             topics = "ai, research, documents"
        
        add_cmd = f'python scripts/run.py notebook_manager.py add --url "{url}" --name "{name}" --description "{desc}" --topics "{topics}"'
        f.write(f"Add cmd: {add_cmd}\n")
        
        add_result = run_cmd(add_cmd)
        f.write(f"Add result:\n{add_result}\n")
        f.flush()

    f.write("\nDone.\n")
