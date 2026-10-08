TOOLS.py
1. Assumptions	"All slots are assumed to be in the future, even for today."
2. Tool design	"Tools return {ok: False, error: ...} instead of raising exceptions, so the LLM can read the error and recover."
3. Safety layers	"Identity checks are enforced in code (patient_mismatch), not only in the prompt, because a prompt is a request and a tool check is a guarantee."
4. Reschedule order	"Validate everything first, mutate last, so a failed reschedule can never lose the original booking."
5. Scope limits	"Reschedule keeps the same doctor. Changing doctors = cancel + new booking."
6. Booking IDs	"Chose not to add them, because name + doctor + date + time is unique enough for this scope." (or the opposite, with your reason)
7. Eval isolation	"reset_schedule() runs before each scenario so scores don't depend on run order."
8. Tools return errors as data, not exceptions.
9. Validate everything first, change data last.Each tool runs all its checks before touching SCHEDULE
10. Safety rules are enforced in code, not only in the prompt
11. Reschedule keeps the same doctor reschedule_appointment moves a booking to a different date or time with the same doctor only.
12. Reset function for reproducible evaluation.
13. Dates computed at runtime
14. "tool loop capped at 5 rounds to prevent runaway calls."