# Card Testing Fraud

## Definition
Fraudsters test stolen credit card numbers by running many small
transactions across different accounts to check which cards are
still active before using them for larger fraud elsewhere.

## Related Features
- card_degree: primary signal. Counts how many distinct accounts have
  used this same card. A card used by 1 account is normal (the owner).
  A card used by 4+ accounts in a short window is a strong signal of
  stolen-card testing.
- fare: card testing transactions are often unusually low value,
  since the goal is just to test validity, not extract money yet.

## Typical Thresholds
- card_degree >= 4 : suspicious
- fare below typical trip cost combined with high card_degree : strong signal

## Recommended Action
Flag the card itself, not just the individual trip - block further
use of that card across all accounts pending review.