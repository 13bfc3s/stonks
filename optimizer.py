from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm

def random_search(bt, data, strat, bounds, samples=1000000):
    param_sets=[{k:random.uniform(lo,hi) for k,(lo,hi) in bounds.items()} for _ in range(samples)]
    results=[]
    with ProcessPoolExecutor() as exe:
        futures={exe.submit(bt.run,data,strat,ps):ps for ps in param_sets}
        for f in tqdm(as_completed(futures), total=samples):
            results.append((futures[f],f.result()))
    return results
