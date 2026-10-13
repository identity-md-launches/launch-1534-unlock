# UNLOCK / UNLK — Sepolia two-stage release package

**Source and tests are delivered; public trading has not been activated.** Both stages have been rehearsed on the
real Sepolia factory at recorded block **11,904,506**. No transaction was broadcast. The current contributor job
has no assigned launch ID/number or deployment record yet. The public IMD interface does not expose the required
owner-signed post-launch operations. Stage 1 must remain unbroadcast until that execution path is secured.
See [deployment and required signatures](docs/DEPLOYMENT.md), [release status](RELEASE_STATUS.json), and
[review and measured manipulation risk](docs/SECURITY_REVIEW.md). Fork addresses are simulations, not deployments.

Recovered from the two requested, SHA-256-verified bundles, preserving all 429 starting files. This revision is
based on implementation `8bc47cb68deda948f5c2fb1e9a5182bb187d6759` plus only `launch.json` from
`7a5e1dc79d05ba7fbeb9166be036cb25b302079e`; it was not restarted from launch-1309. [Recovery record](docs/RECOVERY.md).

## Build and check

```sh
forge build
python3 scripts/generate_code_checks.py --check
forge test
forge fmt --check
python3 scripts/verify_network.py
```

Solidity **0.8.26**, Cancun, optimizer 200, `bytecode_hash = "none"`. All Solidity dependencies are ordinary
vendored files under `lib/`, pinned in `dependencies.lock.json`; no submodules, network downloads, FFI, filesystem
cheatcode access, environment-dependent tests, or compiler binaries are needed. `scripts/check.sh` runs the local
checks. [Validation evidence](docs/VALIDATION.md) distinguishes unit/invariant tests, protected checks, and the fork.

## Contracts and lifecycle

* `UnlkToken`: 1 billion UNLK, 18 decimals, minted once to its deploying factory. No subsequent mint, owner, tax,
  transfer quota, pause, blacklist or upgrade. Passive original-distribution receipts record factory transfers
  until its initial balance first reaches zero. Later transfers/donations cannot change those receipts.
* `UnlkHook`: constructor **`($poolManager, $token, $factory, $owner)`**, no companion arguments or constructor
  external calls. `$owner` is an immutable setup authority, never the factory or IMD signer.
* Stage 1: factory creates token/hook/distributor and initializes the native ETH pool with this hook already in
  its `PoolKey`. Only the manager can call callbacks; only the factory can initialize, exactly once. Factory
  seeding works while UNCONFIGURED. Swaps, quota credits and milestones revert; ordinary transfers and eligible
  native distributor claims work independently.
* Stage 2a: the setup authority calls `deployCompanions(number,feed,routerCode,evidenceCode,oracleCode)` on the
  hook. Each supplied **creation bytecode** must match its compiled constant hash. The hook derives constructor
  arguments from its stage-1 records and deploys all three companions by CREATE2 in one atomic call. This also
  proves their initial storage, unlike ABI or runtime matching alone. Staging first re-runs every stage-1
  precondition of activation (services, registry record, seed position, allocation receipts, distributor
  bindings, live seed capacity), so nothing is staged for a launch that cannot activate. Until activation the
  authority may stage again (a fresh identical bundle under a new salt; the abandoned one can never activate);
  after activation staging is closed permanently.
* Stage 2b: anyone certifies the complete unique-recipient round-0 tree in `MerkleClaimEvidence.certifyRound`
  (up to 1024 leaves in one call) or, for larger rounds, through the chunked `submitLeaves`/`reduce` session path.
  Then the setup authority calls `configureAndActivate(router,evidence,oracle,number)`. It validates stage-1
  records, token creation provenance, allocation receipts, pool/range, dependencies, code/settings and reciprocal
  bindings, binds the oracle, starts observation, and permanently seals. Failure rolls back all activation writes.
* `UnlkSwapRouter`: the sole official-pool swap route. It pulls only `msg.sender`'s input and delivers only to that
  caller. Per-operation context/nonce authenticate the trader; no `tx.origin`. Native outputs and unused ETH
  become caller-owned pull credits (`withdrawNative`). No arbitrary recipient, arbitrary payer or admin sweep.
* `MerkleClaimEvidence`: actual distributor claim flag **and** exact leaf proof, once per round/recipient. A full
  tree certificate proves recipient uniqueness before amounts can be attested, including claims made before
  activation. Native claims need no certificate, oracle, hook call or credit synchronization.
* `UnlkOracle`: explicit v4 tick accumulation. It does not assume that PoolManager has a built-in TWAP.

No upgrade, pause, reset, replacement, trading exemption, privileged withdrawal or post-activation owner operation
exists in these contracts. The setup authority's deployment and activation powers both expire after use.

## Economics and quota

Factory distribution: **10% native contributor distributor / 87% official pool / 3% actual remainder recipient**.
Seed integer rounding can leave dust with the recipient; only the fixed 30 million allocation is credited.
Activation requires the pool receipt within 10^12 minor units (0.000001 UNLK) of 870 million. Payer attribution is
historical and remains correct after transfers or `factory.setRequester`; a current balance is not evidence.

The official pool fee is **12500 = 1.25%**, split by the authentic factory **80/20**: 1% payer, 0.25% IMD. The hook
adds no fee, fee override, or return delta. Factory liquidity principal cannot be removed. Zero-liquidity fee
collection is permitted, including before activation. The factory supports pull recovery of failed fee payouts.
The factory's fee-share holder may assign future fees, and IMD's external fee settings may change its recipient;
these existing platform powers do not move UNLK credit or unlock principal.

For each wallet, `E` is authenticated official-pool buy output + original allocation credit + proven native claims.
`S` is **executed** token input sold, including the input-side LP fee. `Q = max(0, floor(E*p/10000) - S)`.
Exact-input/output swaps and partial fills enforce Q atomically. Transfers, donations and liquidity create no E.

| Confirmed USD FDV | p | Confirmation after preceding tier |
|---|---:|---:|
| Initial | 2500 | immediate activation |
| $100,000 | 3500 | 6 hours |
| $250,000 | 4500 | 6 hours |
| $500,000 | 5500 | 6 hours |
| $1 million | 7000 | 6 hours |
| $2.5 million | 8500 | 6 hours |
| $5 million | permanent quota bypass | 24 hours |

At the final tier every holder, including transfer-only recipients, can sell without quota. Authentication and
fees remain. Prices falling or oracle outages never reduce a reached tier.

## Oracle parameters and their limits

* **2-hour token/ETH geometric TWAP**, minimum full-window warm-up; same-timestamp changes add no past weight.
* Chainlink Sepolia ETH/USD, exactly 8 decimals, positive bounded answer, nonzero/coherent timestamps and round,
  no future update, `answeredInRound >= roundId`, **90-minute maximum feed age** (hourly heartbeat plus grace).
* Latest pool checkpoint no older than **5 minutes** when read. Every swap and liquidity operation checkpoints
  before/after state changes. Anyone may checkpoint or call `updateMilestone`.
* Confirmation samples at least **4 minutes** apart, at most **10 minutes** apart. No parallel tier accumulation.
  An invalid value (stale or incoherent feed, illiquid or stale pool reading) is not a sample: it never confirms a
  tier and never advances the cadence clock, and earned rights remain. Whether a run restarts is decided only by
  the gap between **valid** samples, so an invalid interval has the same effect whether or not somebody called
  during it: shorter than the 10-minute gap it is simply skipped, longer and the next valid sample restarts the
  run. A genuine below-threshold value also restarts. Repeated same-block calls provide no progress.
* **17 ETH minimum opening-value capacity of the locked factory seed**, plus in-range price and minimum seed
  liquidity `1e18`, continuously over the TWAP window. This is a price-independent capital-quality check:
  870M tokens at 20 ETH/billion provide approximately 17.4 ETH capacity. It is explicitly **not** a claim of 17 ETH
  cash reserves. There is no additional actual-ETH-reserve threshold hiding behind the $100K tier.
* The test seed conservatively rounds the 20 ETH cap to the native token-only boundary tick 177300, giving
  19.968425 ETH FDV and about 17.37253 ETH seed capacity. Tests also prove the first tier below 10 ETH cash reserves.
* **The floor is enforced three times, never assumed.** `beforeAddLiquidity` computes the seed's principal and
  opening-value capacity (`SeedDepth`, the oracle's own formula) when the factory seeds and reverts the launch
  transaction if the capacity is below 17 ETH or the principal is outside the pool-share band; `deployCompanions`
  and `configureAndActivate` recompute both from the live factory position. The minimum opening FDV that passes
  is 17 / 0.87 = 19.54 ETH, 2.3% under the 20 ETH policy cap (under four tick spacings of rounding). A seed that
  would leave the oracle permanently illiquid therefore cannot launch, let alone seal.
* **Allocation receipts are checked against bands, not a dust tolerance.** The pool must have received between
  99% and 100% of its 870M share (`MIN_POOL_ALLOCATION` = 861.3M), the remainder wallet at least its 30M, the
  distributor exactly 100M, and the three must sum to the supply. The remainder wallet is credited exactly 30M
  whatever rounding it received. Deployer liquidity rounding is about 1e-14 relative, so the band is generous
  without changing the economics measurably.

A high sustained price can still force all tiers. At a fixed test feed of $2,000/ETH, raising the token-only pool
to $5.1M and waiting **56 hours** costs about **181.21 ETH gross**, **2.47 ETH net exit loss** without counter-selling;
a payer attacker recovers native fees and loses only about **0.65 ETH** (excluding gas/financing and token fees).
Counter-selling all initial non-pool allocations raises the modeled gross to **404.49 ETH**, net loss to
**264.82 ETH**. These are reproducible scenarios, **not lower bounds or proof of manipulation safety**.
[Method, exact results and residual release concerns](docs/SECURITY_REVIEW.md).

Other pools can trade the freely transferable token without this hook's quota. The official pool cannot prevent
that. External manager governance and Chainlink administration remain dependencies. No independent auditor has
approved this revised artifact; the recovered reviews plus this implementation's adversarial pass are not a new
independent audit.

## After launch

The only setup calls are `deployCompanions`, tree certification, and `configureAndActivate` described above; all
inputs come from the new launch's actual records and frozen claims. There are no later setters. Any funded wallet
may operate a keeper every 5 minutes to call `updateMilestone` during confirmations. There is no keeper reward or
privileged keeper role; missed calls delay tiers. Claims retain the distributor's own unlock/sweep timing regardless
of keeper/oracle state. Users may call `attest` then `syncRewards`, and anyone may call `syncPayer` and `claimFees`.

Twenty ABIs are in `docs/abi/`; reproducible creation/template hashes and sizes are in `docs/ARTIFACTS.json`. [Deployment package](docs/DEPLOYMENT.md) names verified services, responsible actors,
required wallet transactions, recorded fork evidence, and the missing public execution operation.
