import agent, tools

tools.reset_schedule()
msgs = agent.make_messages()
reply, log = agent.run_turn(msgs, "Book Dr. Rao tomorrow at 09:00 for Asha Reddy")
print("REPLY:", reply)
print("LOG:")
for entry in log:
    print("  ", entry)