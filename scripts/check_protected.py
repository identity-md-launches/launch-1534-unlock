#!/usr/bin/env python3
"""Run the unmodified supplied admission checks with isolated manifest-derived probe environment.
Usage: scripts/check_protected.py [directory containing Hook.protected.t.sol and Token.protected.t.sol]
The supplied checks intentionally use vm.env*; production tests do not. Copies live only in test/scratch.
"""
import json, os, pathlib, shutil, subprocess, sys
root=pathlib.Path(__file__).resolve().parent.parent
inputs=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else root/'.imd/reads/protected/univ4_hook')
target=root/'test/scratch/protected'
target.mkdir(parents=True,exist_ok=True)
for name in ['Hook.protected.t.sol','Token.protected.t.sol']:
    shutil.copyfile(inputs/name,target/name)
manifest=json.loads((root/'launch.json').read_text())
# Test-only probes, never deployment inputs. Derived from descriptive labels to avoid legacy launch identities.
def addr(label):
    return '0x'+subprocess.check_output(['cast','keccak',label],text=True).strip()[-40:]
manager=addr('UNLK protected manager');token=addr('UNLK protected token')
factory=addr('UNLK protected factory');owner=addr('UNLK protected owner')
def bytecode(c):
    return json.loads((root/'out'/f'{c}.sol'/f'{c}.json').read_text())['bytecode']['object']
args=subprocess.check_output(['cast','abi-encode','f(address,address,address,address)',manager,token,factory,owner],text=True).strip()
env=os.environ.copy()
env.update(IMD_EXPECTED_SUPPLY=str(10**27), IMD_TOKEN_DECIMALS=str(manifest["token"]["decimals"]), IMD_HOOK_CREATION_CODE=bytecode(manifest['hook']['contract'])+args[2:],IMD_HOOK_FLAGS=str(0x3fc0),
    IMD_POOL_MANAGER=manager,IMD_TOKEN_PROBE=token,IMD_TOKEN_CREATION_CODE=bytecode(manifest['token']['contract']),
    IMD_FACTORY_PROBE=factory,IMD_PAIRED_CURRENCY=manifest['pool']['pairedCurrency'],IMD_POOL_FEE=str(manifest['pool']['fee']),
    IMD_TICK_SPACING=str(manifest['pool']['tickSpacing']),IMD_SQRT_PRICE=manifest['pool']['initialPrice'])
try:
    result=subprocess.run(['forge','test','--match-path','test/scratch/protected/*.sol','-vv'],cwd=root,env=env)
finally:
    shutil.rmtree(target)
sys.exit(result.returncode)
