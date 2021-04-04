# MVP Rules

## Examples

1. User did not enter any activity in the last 24 hours
2. User did not report his medication 3 days in a row
3. PRO rating is increasing 3 days in a row
4. The user has done more than 5 tasks on the same day

## Rules

1. `Absence` of any event of the `event_category` from the user during the last `time_period`
2. `Absence` of event of `event_type` during the last `time_period`
3. Value of `measurement` is increasing during the last `time_period`
4. `Count` of events of the `event_category` is greater than the `threshold_value`
