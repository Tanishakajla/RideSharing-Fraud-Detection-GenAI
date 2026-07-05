# Velocity Fraud

## Definition
Velocity fraud occurs when a single account books an abnormally high
number of trips within a very short time window. This pattern is common
in stolen-account takeover, where a fraudster tries to extract maximum
value before the legitimate owner notices and locks the account.

## Related Features
- user_trips_last_1h: primary signal. Legitimate riders rarely book more
  than 1-2 trips per hour. 4+ trips/hour is a strong anomaly.
- seconds_since_signup: velocity fraud combined with a very new account
  (signed up minutes ago) is a much stronger signal than velocity alone
  on an old, established account.

## Typical Thresholds
- user_trips_last_1h >= 4 : moderate suspicion
- user_trips_last_1h >= 7 : high suspicion, especially if seconds_since_signup < 3600

## Recommended Action
Flag for manual review. Do not auto-block on velocity alone if the
account is old and previously trusted — could be a legitimate power
user (e.g. courier, commuter). Auto-hold only when combined with a
new-account signal.