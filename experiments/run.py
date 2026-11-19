"""Convenient experiment entry; dispatch the sealed paper reproduction unchanged."""
import argparse,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    subprocess.run([sys.executable,'-B',str(ROOT/'reproduction/offline/reproduce.py'),'--output',str(a.out.resolve())],check=True)
if __name__=='__main__':main()
