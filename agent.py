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

system_prompt=f"""You are a scheduling assistant for a clinic. Today's date is {tools.TODAY} and tomorrow's date is 
                 {tools.TOMORROW}. the doctors are {", ".join(tools.SCHEDULE.keys())}. You only help patients check
                 availability, book, cancel and reschedule appointments.ask for the patient name, never invent one for
                  yourself You never give medical advice. Keep replies short."""

messages=[{'role':'system', 'content':system_prompt }]


while True:
    text=input("Patient: ")

    #quit chat 
    if text.strip().lower()=="quit":
        break

    #appended input text to messages
    messages.append({'role':'user', 'content':text})

    response=client.chat.completions.create(model=MODEL,messages=messages, tools=TOOLS)
    msg = response.choices[0].message

    rounds = 0
    while msg.tool_calls and rounds < 5:
        rounds+=1
        messages.append(msg)
        for call in msg.tool_calls:
            #get arguments of function
            func_args=call.function.arguments
            args=json.loads(func_args)  #convert strings to dict bcoz func_args is present as json string in model reply response.choice[0].message.tool_calls[0].function.arguments

            #get function name
            func_name=call.function.name
            func=getattr(tools,func_name)  #get function def from tools 
            result=json.dumps(func(**args))
            print("TOOL RESULT:", result)
            # append result to messages
            messages.append({'role':'tool',
                         'tool_call_id':call.id,
                           'content':result})
  
        response=client.chat.completions.create(model=MODEL, messages=messages, tools=TOOLS)
        msg=response.choices[0].message
    print("chat:" , msg.content)
    messages.append({'role':'assistant', 'content':msg.content})
    print(msg.tool_calls)
    print(tools.SCHEDULE["Dr. Rao"][tools.TOMORROW])








