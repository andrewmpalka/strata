# Attribution invariants

Violating these rules invalidates the study. The canonical PRD supplies the full
chain semantics and dataset contract.

## Ethereum

- The ERC-4337 bundler is never the actor. Attribute a UserOperation to its
  `sender`.
- Factory data comes from `AccountDeployed`, never from `UserOperationEvent`.
- An EIP-7702 authorization attempt, recovered authority, protocol validity, and
  applied delegation are distinct states; never collapse them.
- A `delegation_observation` exists only with application proof from
  block-boundary evidence or stronger evidence.
- The recovered authority can differ from the outer transaction sender. Recover
  it from the authorization tuple signature. A malformed signature fails loudly
  and must never resolve to a plausible but wrong address.
- Exposure state is assigned using code at the index block, never `latest`.
- `eoa_7702_direct` is descriptive-only and never a matched arm without the
  stronger attribution evidence required by the PRD.

## Both chains

- Fee payers and sponsors are never actors. Sponsorship and signing scheme
  remain separate fields, never one enum.
- Receipt never activates an address. A passive participant has
  `participant_role = passive` and produces zero actor facts.
- Aptos identity is the account address, never a key. Key rotation does not
  create a new actor.
- Address is not person. Perform no identity resolution, ownership attribution,
  or person-level experience claims.
- Name structurally observed transfers `direct_address_transfer`; do not use
  language that implies hidden ownership or execution.
