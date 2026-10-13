# Deployment status and executable handoff

**No public-network transaction has been signed or broadcast. UNLK is not live.** The deliverable is the recovered,
repaired source/package and a successful rehearsal of both stages on a recorded Sepolia fork. No simulated address
is presented as a public deployment. `RELEASE_STATUS.json` makes the remaining release gate explicit.

## Verified identities and services

At Sepolia block **11,904,506**, identified from [IMD's public contract table](https://imd.fun/docs/) and checked
by RPC, compiled bytecode comparison where available, and the fork:

| Role | Actual Sepolia address / authority |
|---|---|
| Hook LaunchFactory | [0x315752fEE5cBcAA00333E0d4d91E0cD69429E908](https://sepolia.etherscan.io/address/0x315752fEE5cBcAA00333E0d4d91E0cD69429E908) |
| Its LaunchRegistry | [0x78BA7bDcC66715D0f6E425b4700207A0b75aD5a4](https://sepolia.etherscan.io/address/0x78BA7bDcC66715D0f6E425b4700207A0b75aD5a4) |
| LaunchFees | [0x428Ff16D1bb25d6674463881ed6a62BD09e30584](https://sepolia.etherscan.io/address/0x428Ff16D1bb25d6674463881ed6a62BD09e30584) |
| PoolManager | [0xE03A1074c86CFeDd5C142C4F04F1a1536e203543](https://sepolia.etherscan.io/address/0xE03A1074c86CFeDd5C142C4F04F1a1536e203543) |
| ETH/USD proxy | [0x694AA1769357215DE4FAC081bf1f309aDC325306](https://sepolia.etherscan.io/address/0x694AA1769357215DE4FAC081bf1f309aDC325306) |
| Authorized factory signer | `0xcECc29B037f5064fCdF45a5C318F132ef76aA551` (`factory.deployer()`) |
| New job's payer / setup authority | `0x48E4E74fE1d0c14404cEB57B9fec5b21329C6ec9` |
| Network fee recipient and treasury at snapshot | `0x047F606fD5b2BaA5f5C6c4aB8958E45CB6B054B7` |

The new job's payer was verified through `GET /jobs/672489ef-8304-403f-855c-b9dce583bc31`, which reports a requested
`univ4_hook` launch on 11155111 and **no assigned launch ID**. The setup authority remains `$owner`, not an address
hardcoded into contracts. There is no legacy payer or launch-number constant in production code.

The current public [policy](https://api.imd.fun/launch/policies) is version **32**, `univ4_hook`, chain 11155111:
fee tier 12500, 1 billion supply, 10% contributor share, native ETH allowlist, 20 ETH opening FDV, 3600-second
contributor lock. This request selects poolBps **8700** above the policy's base floor. The default `owners` fields
in a general policy row do not override the explicit `$owner` constructor substitution for this paid job.
`LaunchFees.REQUESTER_BPS()` is 8000; `poolFee()` is 12500. The actual new launch's sweep timing and frozen tree
are platform outputs and must be checked before broadcast; the fork's one-year sweep and synthetic leaf are not
production values.

`docs/network/` contains saved block/code hashes, source compiler inputs, reference outputs, and public service
facts. `python3 scripts/verify_network.py` reproduces the saved comparisons offline; append `--rpc URL` to reread
the same block. The factory, registry and fee settings match verified source builds, including consistent immutable
words. The factory's distributor creation hash is
`0xf1c21108732a73286b1030e87fbba14c806905275dde6fce012f2c0ca19e30b9`, also matched to the compiled distributor.
The feed's executable bytes match the verified proxy (Sourcify reports a metadata-only difference).
The manager is Uniswap's [published Sepolia deployment](https://developers.uniswap.org/docs/protocols/v4/deployments),
pinned by full runtime hash and exercised on the fork; its compiler output was not independently reproduced.

`GET /services` reported verifier `0.1.0+327e1e9f`, deployer `0.1.0+bdb0621d`, publisher `0.1.0+04d3c6da`, all up.
That establishes service presence, **not authorization to sign as the owner**. The public docs/capabilities provide
launch admission and publication, but no callable post-launch owner-signature service. No private key is requested.

## Stage 0 — release gate

The missing operation is an executable, authorized sequence for the owner wallet to deploy the reviewed companions,
certify the actual frozen tree, and seal activation after IMD's factory transaction. The source contains this exact
operation and it works on the fork. The live service route/signatures are not available in this assignment.
Therefore stage 1 remains unbroadcast. This is the brief's authorized **source/package fallback**, not a request
for future addresses or another paid launch.

Before any broadcast, the platform must also record independent review of this revision and address the sustained
manipulation economics in `SECURITY_REVIEW.md`. Delays cannot certify independent market value. The current artifact
must not be described as independently audited or manipulation-safe.

## Stage 1 — IMD signer through the authenticated LaunchFactory

Use the actual **new** assigned launch number, attestation, frozen reward root and policy; never 1309, 1401, the
fork's synthetic number, or a fabricated allocation tree. Mine the hook salt against the factory and exact
creation code with constructor arguments `(manager, predictedToken, factory, owner)`; required flags **0x3fc0**.
`HookDeployer` provides init-code/mining helpers. The supplied manifest has the four supported placeholders.

Factory `launch` creates the token/hook/native distributor, splits the supply, initializes the official native ETH
pool with this hook, and seeds its token-only position in one transaction. No hook is attached later. Record:

* Real transaction hash/block and `Launched`/registry records.
* Token, hook, distributor, actual remainder recipient, seed range/liquidity and opening price.
* `PoolKey = (address(0), token, 12500, 60, hook)` and `PoolId = keccak256(abi.encode(PoolKey))`.

The manifest's required initialPrice string is `79228162514264337593543950336`; the deployer derives the actual
opening price from the 20 ETH policy cap, token ordering and tick spacing. It must not seed at 1:1.
After this transaction alone: **pool deployed, trading inactive**. Native transfers/eligible claims already work.

## Stage 2 — three owner-wallet transactions

1. Call `hook.deployCompanions(newNumber, publishedFeed, routerCreationCode, evidenceCreationCode,
   oracleCreationCode)`. Exact compiled creation bodies (without arguments) are inputs; the hook validates hashes,
   appends authenticated arguments and CREATE2-deploys the bundle atomically. Read `CompanionsDeployed` and
   `stagedRouter/stagedRewards/stagedOracle`. No ordinary external deployment can substitute for this provenance.
2. Certify the **complete frozen** round-0 tree on the staged evidence adapter. Any wallet may submit the certificate;
   the owner script includes it. Maximum **1024 unique recipients** per round, bounded by transaction gas. Run
   `scripts/prepare_claim_tree.py` against the API's actual `claims` JSON first. It checks every recipient and root,
   returning arrays in the exact heap leaf order. If a root has duplicates or exceeds this limit, do not broadcast
   stage 1 with this package. Native claim eligibility itself is never altered by certificate requirements.
3. The immutable setup authority calls `configureAndActivate(stagedRouter, stagedRewards, stagedOracle, newNumber)`.
   This is the atomic sealing call. A failure changes no activation state; corrected external conditions can be
   retried with the same bundle. A successful call permanently removes all setup powers.

`script/Stage2.s.sol` executes those calls from `hook.setupAuthority()`, with explicit function arguments:

```sh
# Fill these with actual recorded outputs and certificate arrays; no example stand-in addresses are usable.
forge script script/Stage2.s.sol:Stage2 \
  --sig 'run(address,uint64,address[],uint256[])' \
  "$UNLK_HOOK" "$UNLK_NUMBER" "$CERTIFIED_ACCOUNTS" "$CERTIFIED_AMOUNTS" \
  --rpc-url "$SEPOLIA_RPC" --account "$OWNER_KEYSTORE" --broadcast
```

The owner supplies wallet signatures/keystore locally; no secret is supplied to a contributor. `deploymentCall`
returns the exact first transaction data for hardware/multisig tooling; `readCompanions` resolves its outputs.
The three steps can also be separate wallet transactions. Anyone may later certify valid additional rounds.
There is no owner-settable oracle, manager, router, payer or exception list after staging/sealing.

## Recorded-block rehearsal and postflight

```sh
scripts/rehearse-sepolia.sh https://ethereum-sepolia-rpc.publicnode.com
```

This selects only `rehearsal/Sepolia.t.sol`, forks block 11904506, impersonates the **actual authorized** factory
signer and owner **inside Foundry**, launches a fresh test instance on the real services, makes a native claim
before activation, deploys/certifies/seals, buys, sells to the quota, rejects an excess sale, synchronizes credits,
withdraws native proceeds, collects the real factory fee split and checks unchanged LP principal. It contains no
broadcast and no private/test key. Its synthetic claim tree/number and simulated addresses are explicitly local.
The default offline test suite never attempts an RPC connection. `docs/FORK_RESULTS.txt` records the final run.

After a real release, run `CheckReleaseConfig.run(hook,11155111,managerCodeHash,feedCodeHash)`, verify all creation
transactions, code/settings and reciprocal bindings, and verify sources on Sepolia Etherscan. Record real explorer
links, ABI checksums, PoolKey/PoolId, signatures/transactions and `Activated` event before saying trading is active.
No such real receipt, token address, pool ID or explorer verification exists yet; none is fabricated here.

## Publication

The requested recovered GitHub repository/commits are recorded in `RECOVERY.md`. The current source resides in this
submission; its **new publication repository/commit must be returned by IMD's publisher** after acceptance. The
workspace Git metadata is protected by this task, so it was neither rewritten nor used to invent a release commit.
The ordinary source package, ABI files, evidence and `launch.json` are ready for that publisher. Do not overwrite
the parent launch's repository or advertise a parent commit as the repaired revision.
