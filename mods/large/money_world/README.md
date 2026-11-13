# Money World — Meridian

A dead economy's living bank. Find a Meridian card, sell junk and ammo to the
recycler, and buy supplies and time-limited leases from machines, not humans.

## Setup

- Back up your save before enabling. Removing this mod mid-save is unsupported:
  visited branch tiles, the ATM furniture, and leased items reference mod IDs.
- Enable `money_world` alongside `dda`. No other dependencies.

## How it works

- The card is a key, not a wallet. Balance lives on your character
  (`u_mw_cents`) and survives losing the card. Death wipes it.
- Buyback is recycler-only: whitelisted scrap and ammo at a fixed 2 cents per
  charge. Branch ATM pays 100％, the mobile card pays 50％.
- Non-whitelisted items (containers, food, gear, valuables) are never bought,
  so backpack contents can never vanish into a sale.
- Top gear is lease-only and dissolves when the lease expires.

## Reissue

- Lost your card? Any branch ATM prints one for free, or craft one
  (plastic chunk + e-scrap + wire, soldering).

## v1.0 scope

- 14 permanent goods, 2 leases, 2 services, 1 branch, ranks 0-2.
- No shared balance with vanilla `cash`, ATMs, or NPC traders.
