import importlib.util, sys, os, time, traceback
def run(path):
    spec = importlib.util.spec_from_file_location("m_under_test", path)
    m = importlib.util.module_from_spec(spec)
    t0=time.time()
    try: spec.loader.exec_module(m)
    except Exception as e:
        print(f"{path}|IMPORT_FAIL|{type(e).__name__}: {e}"); return
    fns = sorted([(n,f) for n,f in vars(m).items() if n.startswith("t_") and callable(f)])
    passed=failed=0; fails=[]
    for n,f in fns:
        try: f(); passed+=1
        except Exception as e:
            failed+=1; fails.append(f"{n}: {type(e).__name__}: {str(e)[:80]}")
    print(f"{path}|ran={passed+failed}|passed={passed}|failed={failed}|dur={time.time()-t0:.1f}s")
    for x in fails: print("  FAIL "+x)
if __name__=="__main__":
    run(sys.argv[1])
