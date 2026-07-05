# New Account Fraud

## Definition
Fraud committed via freshly created accounts, typically to abuse
sign-up promotions, or because a legitimate long-term identity would
already be flagged/blacklisted, so fraudsters churn through new
accounts instead.

## Related Features
- seconds_since_signup: primary signal. Very low values (account is
  minutes or seconds old) combined with any other suspicious feature
  compounds risk significantly.
- user_trip_count: a brand-new account with an unusually high trip
  count already is itself an anomaly.

## Typical Thresholds
- seconds_since_signup < 600 (10 minutes) combined with
  user_trips_last_1h >= 2 : high suspicion

## Recommended Action
Apply stricter automatic thresholds to new accounts than established
ones. Do not treat a 10-minute-old account with the same trust level
as a 2-year-old account with clean history.