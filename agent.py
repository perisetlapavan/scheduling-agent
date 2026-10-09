from dotenv import load_dotenv
from groq import Groq
import tools # from tools.py
import json #to convert arguments present in json format in the toolcalls into dict 


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "check_availability",
            "description": "List the open appointment slots for a doctor on a specific date.",
            "parameters": {
                "type": "object",
                "properties": {
                    "doctor": {"type": "string", "description": "Doctor's name, e.g. 'Dr. Rao'"},
                    "date_str": {"type": "string", "description": "Date in YYYY-MM-DD format"},
                },
                "required": ["doctor", "date_str"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "book_appointment",
            "description": "Book a specific appointment slot for a patient. Only use this when you have the patient's real name and have confirmed the slot is open.",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_name": {"type": "string", "description": "The patient's real name"},
                    "doctor": {"type": "string", "description": "Doctor's name, e.g. 'Dr. Rao'"},
                    "date_str": {"type": "string", "description": "Date in YYYY-MM-DD format"},
                    "time_str": {"type": "string", "description": "Time slot, e.g. '09:00'"},
                },
                "required": ["patient_name", "doctor", "date_str", "time_str"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_appointment",
            "description": "Cancel an existing appointment for a patient given the doctor, date, time, and patient name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_name": {"type": "string", "description": "The patient's real name"},
                    "doctor": {"type": "string", "description": "Doctor's name, e.g. 'Dr. Rao'"},
                    "date_str": {"type": "string", "description": "Date in YYYY-MM-DD format"},
                    "time_str": {"type": "string", "description": "Time slot to cancel, e.g. '09:00'"},
                },
                "required": ["patient_name", "doctor", "date_str", "time_str"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reschedule_appointment",
            "description": "Reschedule an existing patient appointment from an old date and time to a new date and time.",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_name": {"type": "string", "description": "The patient's real name"},
                    "doctor": {"type": "string", "description": "Doctor's name, e.g. 'Dr. Rao'"},
                    "old_date": {"type": "string", "description": "Current appointment date in YYYY-MM-DD format"},
                    "old_time": {"type": "string", "description": "Current appointment time, e.g. '09:00'"},
                    "new_date": {"type": "string", "description": "New desired date in YYYY-MM-DD format"},
                    "new_time": {"type": "string", "description": "New desired time, e.g. '11:00'"},
                },
                "required": ["patient_name", "doctor", "old_date", "old_time", "new_date", "new_time"],
            },
        },
    }
]

load_dotenv()

client=Groq()

MODEL='openai/gpt-oss-120b'

VERBODE=True

system_prompt=f"""You are a scheduling assistant for a clinic. Today's date is {tools.TODAY} and tomorrow's date is 
                 {tools.TOMORROW}. the doctors are {", ".join(tools.SCHEDULE.keys())}. You only help patients check
                 availability, book, cancel and reschedule appointments.ask for the patient name, never invent one for
                  yourself You never give medical advice. Keep replies short."""
def load_improvements(path="improvements.json"):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)["improvements"]
    except FileNotFoundError:
        return []


def build_system_prompt():
    rules = [imp["rule"] for imp in load_improvements() if imp.get("active", True)]
    if not rules:
        return system_prompt
    return system_prompt + "\n\nAdditional rules:\n" + "\n".join(f"- {r}" for r in rules)


def make_messages():
    return [{'role': 'system', 'content': build_system_prompt()}]

def run_turn(messages, user_text):
    tool_log = []
    """Handle one patient message. Updates messages in place and returns the reply text."""
    messages.append({'role': 'user', 'content': user_text})

    response = client.chat.completions.create(model=MODEL, messages=messages, tools=TOOLS)
    msg = response.choices[0].message

    rounds = 0
    while msg.tool_calls and rounds < 5:
        rounds += 1
        messages.append(msg)
        for call in msg.tool_calls:
            # arguments arrive as a JSON string, so convert to a dict
            args = json.loads(call.function.arguments)

            # look up the real Python function by name
            func_name = call.function.name
            func = getattr(tools, func_name)
            result_dict = func(**args)
            tool_log.append({"tool": func_name, "args": args, "result": result_dict})
            result = json.dumps(result_dict)
            if VERBOSE:
                print("TOOL RESULT:", result)

            # hand the result back to the model
            messages.append({'role': 'tool',
                             'tool_call_id': call.id,
                             'content': result})

        response = client.chat.completions.create(model=MODEL, messages=messages, tools=TOOLS)
        msg = response.choices[0].message

    messages.append({'role': 'assistant', 'content': msg.content})
    return msg.content, tool_log


def main():
    messages = make_messages()
    while True:
        text = input("Patient: ")
        if text.strip().lower() == "quit":
            break
        reply, _  = run_turn(messages, text)
        print("chat:", reply)


if __name__ == "__main__":
    main()