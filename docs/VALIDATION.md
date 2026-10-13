# Validation record — 2026-10-13

These are implementation-author results, not an independent audit or deployment attestation. **No public
transaction was broadcast.** Release status and outstanding wallet operations are in `../RELEASE_STATUS.json`
and `DEPLOYMENT.md`.

## Reproduction

Run from the repository root. All contract dependencies are ordinary vendored files; the compiler is the
worker-installed **Solidity 0.8.26+commit.8a97fa7a**, not a repository binary. Foundry used here was **1.8.3**, commit
`cae51ad458f6abb64852b7709eb784352429825d`. Recovered `foundry.toml` and `remappings.txt` are retained: Cancun,
optimizer 200, metadata hash none, FFI disabled, no filesystem cheatcode permissions, local `lib/` only.

```sh
forge build
python3 scripts/generate_code_checks.py --check
forge test
forge fmt --check
forge lint src --severity high med
python3 scripts/verify_network.py
python3 scripts/export_abis.py
python3 scripts/release_artifacts.py
sha256sum -c docs/SOURCE_SHA256SUMS
```

`scripts/check.sh` performs build, creation-hash checks, tests, formatting, source lint and saved-network checks.
The hashes in `ReviewedCode.sol` must match the four reviewed compiler creation bodies. A deliberate companion
or token source change requires review, rebuilding and regeneration; it cannot silently become an activation
candidate. There are no unresolved library links. `ARTIFACTS.json` distinguishes compiler runtime templates
from actual deployed runtime hashes, and records ABI digests and the digest of `SOURCE_SHA256SUMS`.

## Final results

| Check | Result | Raw evidence |
|---|---|---|
| `forge build --force` | PASS; all 124 compilation units rebuilt with pinned compiler | `BUILD_RESULTS.txt` |
| `forge test` | **142 passed, 0 failed, 0 skipped**, 28 suites | `TEST_RESULTS.txt` |
| Alternate seed, four threads, environment containing only PATH | **142 passed, 0 failed, 0 skipped** | `MINIMAL_ENV_TEST_RESULTS.txt` |
| `forge fmt --check` | PASS, exit 0, no output | `FMT_RESULTS.txt` |
| Supplied unmodified protected tests | **11 passed, 0 failed, 0 skipped** | `PROTECTED_TEST_RESULTS.txt` |
| Recorded Sepolia fork, both stages and trading | **1 passed, 0 failed, 0 skipped** | `FORK_RESULTS.txt` |
| Sustained manipulation and maximum tree gas | **4 passed**; actual economic measurements recorded | `ECONOMICS_RESULTS.txt` |
| Saved platform bytecode/source comparisons | PASS | `NETWORK_VERIFICATION_RESULTS.txt` |
| `forge lint src --severity high med` | Completed, warnings triaged below | `LINT_RESULTS.txt` |

The economic tests are part of the 142, not four additional tests. The protected suite is separate and its copies
are removed from `test/scratch` after execution. The default test suite never forks or reads environment variables.
The minimal-environment run used `forge test --threads 4 --fuzz-seed 0x20261013` from a child process whose environment
contained only PATH. Default fuzz runs are 256; individual properties declare 160 or 512 where noted. Stateful
invariants use 128 runs and depth 40, with handler reachability tests preventing a vacuous all-reverting campaign.

There is one compiler advisory: `afterInitialize` could have `view` mutability. It returns the expected selector
after authentication and does not write state. Lint reports 31 warnings: 23 checked/range-bounded casts, three
default-zero locals, two deliberate settlement-balance equalities, two generic reentrancy notices and one signed
floor-division precision notice. The reasoning and actual guarded external-call paths are in `SECURITY_REVIEW.md`.
No Slither, Mythril, formal verification or independent contributor review was performed on this revision.

## Coverage that matters

* Standard supply, metadata and transfers; factory-only initialization and exact hook permission flags.
* Stage-1 pool binding/seed, ordinary transfers/native claims before activation, and rejection of early
  swaps, credit synchronization and milestones.
* Actual reviewed creation-code provenance, malicious constructor/runtime rejection, owner-only one-time staging,
  wrong launch/pool/dependency rejection, certified complete reward roots and atomic activation rollback.
* Authentic router/trader context, spoofing, replay, direct-manager bypass, exact input/output and partial fills,
  executed E/S accounting, transfer-only wallets, deduplication and monotonic earned rights.
* Native claims before activation, duplicate recipients, incomplete trees, real multi-leaf proofs, later funded
  reward rounds without arbitrary cumulative ceilings, sweep/lock timing and claims independent of credit sync.
* Token-only seed with no ETH top-up, principal protection, 80/20 fee payouts, native refunds, rejecting recipients,
  reentrancy attempts and router balance/credit solvency.
* TWAP arithmetic against brute-force integration, full warm-up, stale/future/incoherent feed data, observed depth
  dips, invalid intervals, cadence/gaps, sequential thresholds, the separate final delay and irreversible unlock.
* The $100K tier reachable below 10 ETH actual reserves, and the sustained 56-hour manipulation, fee-recapture and
  counter-selling paths. Successful attack simulation is disclosed risk, not an audit pass.

The 1024-leaf sorted certificate consumed **13,943,571 execution gas** in its direct-call measurement; the test
asserts less than 16,000,000, leaving room for normal transaction/calldata overhead below a 16,777,216 cap. Larger
trees use the chunked session path (`ActivationRobustness.t.sol:ChunkedCertificationTest`, 1500 leaves in three
submissions and two reductions). A duplicate-recipient frozen tree is a preflight incompatibility, so stage 1 must
not be broadcast with it.

## Deployment sizes

| Contract | Creation body bytes | Runtime template bytes |
|---|---:|---:|
| UnlkToken | 3444 | 2320 |
| UnlkHook | 25702 | 24328 |
| UnlkSwapRouter | 8102 | 7761 |
| MerkleClaimEvidence | 5943 | 5675 |
| UnlkOracle | 7857 | 7517 |
| HookDeployer | 26292 | 26264 |

Every deployable runtime is below 24,576 bytes (`UnlkHook` with 248 bytes of margin after this revision's seed
and allocation checks). Creation bodies plus their fixed constructor arguments are below 49,152 bytes.
`HookDeployer` is an off-chain helper for prediction/mining whose runtime embeds the hook's init code and now
exceeds EIP-170; it is called in the VM by tests and scripts, never deployed, and is not a replacement for the
authenticated platform factory. Twenty ABIs are exported, including the verified platform factory, registry, fees and distributor.

## Repeating checks that use external inputs

```sh
# Only while the supplied protected inputs are present; the script copies them unchanged into scratch.
python3 scripts/check_protected.py

# Optional read-only network checks; no signatures and no broadcast.
python3 scripts/verify_network.py --rpc https://ethereum-sepolia-rpc.publicnode.com
scripts/rehearse-sepolia.sh https://ethereum-sepolia-rpc.publicnode.com
```

The fork is pinned to block **11904506**, hash
`0xf3867dcdde6c437c3297aa05a7e56c1e5c6c63490989ee69d9f69e21e941d87c`. It uses actual factory/registry/fees/manager/feed
code and the actual authorized signer identities, impersonated only inside Foundry. Synthetic launch number and
reward leaf are clearly labelled rehearsal inputs. Simulated output addresses are printed only as **FORK ONLY**.
No real UNLK address, transaction hash, PoolId, source-verification receipt or new GitHub publication commit exists
yet. Those remain outputs of the authorized live deployment/publication sequence, not requester prerequisites.
