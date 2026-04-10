# replacer.py
import os, sys, codecs

def replace_in_file(path, repl):
    try:
        s = codecs.open(path, 'r', 'utf-8').read()
    except:
        return
    for k,v in repl.items():
        s = s.replace(k, v)
    codecs.open(path, 'w', 'utf-8').write(s)

def walk_and_patch(root, exts, repl):
    for dp,_,fnames in os.walk(root):
        for f in fnames:
            if any(f.lower().endswith(e) for e in exts):
                replace_in_file(os.path.join(dp,f), repl)

if __name__ == "__main__":
    # usage: replacer.exe <install_dir> <APP_DIR> <PY_EXE> <CLI_EXE>
    if len(sys.argv) < 5:
        print("Usage: replacer <install_dir> <APP_DIR> <PY_EXE> <CLI_EXE>"); sys.exit(1)
    install_dir, APP_DIR, PY_EXE, CLI_EXE = sys.argv[1:5]
    repl = {
        "%APP_DIR%": APP_DIR.replace("\\","\\\\"), 
        "%PY_EXE%": PY_EXE.replace("\\","\\\\"),
        "%CLI_EXE%": CLI_EXE.replace("\\","\\\\"),
        "%TEMP%": os.environ.get("TEMP", APP_DIR).replace("\\","\\\\")
    }
    exts = [".can",".tse",".cfg",".ini",".capl",".txt",".py"]
    walk_and_patch(install_dir, exts, repl)
    # write final config.ini if template exists
    tpl = os.path.join(install_dir,"config.ini.template")
    if os.path.isfile(tpl):
        replace_in_file(tpl, repl)
        os.replace(tpl, os.path.join(install_dir,"config.ini"))
    print("patched")
