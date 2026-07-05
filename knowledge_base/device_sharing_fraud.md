# Device Sharing Fraud

## Definition
Occurs when a single physical device is used to create or operate
multiple distinct rider accounts. This is a classic signature of
promo abuse rings and fake-account fraud farms, where one operator
runs many accounts to repeatedly claim new-user discounts or launder
payments.

## Related Features
- num_users_on_device: primary signal. A device tied to 1-2 accounts
  (e.g. shared family device) is normal. 5+ distinct accounts on one
  device is not normal consumer behavior.
- device_degree: a graph-based feature - counts how many other
  entities (cards, accounts) connect through this device. High degree
  means the device sits at the center of a suspicious cluster.

## Typical Thresholds
- num_users_on_device >= 5 : suspicious
- device_degree >= 5 : suggests device is part of a fraud ring, not
  an isolated incident

## Recommended Action
Escalate to fraud ring investigation, not just single-transaction
review. If multiple accounts on the device also share a card_degree
pattern, treat as high-confidence organized fraud.