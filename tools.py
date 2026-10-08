from datetime import date, timedelta
import copy #to make deepcopy, so scenarios don't permanently alter SCHEDULE data, that can affect other evaluation scenarios while running


TODAY = date.today().isoformat()
TOMORROW = (date.today() + timedelta(days=1)).isoformat()

# SCHEDULE[doctor][date][time] -> None (open) or patient name (booked)
SCHEDULE = {
    "Dr. Rao": {
        TODAY: {
            "09:00": None,
            "10:00": "Anita Sharma",
            "11:00": None,
            "14:00": "Rahul Verma",
        },
        TOMORROW: {
            "09:00": None,
            "10:00": None,
            "11:00": "Priya Patel",
            "14:00": None,
        },
    },
    "Dr. Mehta": {
        TODAY: {
            "10:00": "Sunil Kumar",
            "11:00": "Deepak Joshi",
            "12:00": "Kavita Rao",
            "15:00": "Vikram Singh",
        },  # Fully booked date for testing "no availability" edge cases
        TOMORROW: {
            "10:00": None,
            "11:00": None,
            "12:00": None,
            "15:00": "Amitabh Roy",
        },
    },
    "Dr. Sen": {
        TODAY: {
            "09:30": None,
            "10:30": "Neha Gupta",
            "11:30": None,
        },
        TOMORROW: {
            "09:30": "Manish Malhotra",
            "10:30": None,
            "11:30": None,
        },
    },
}

_INITIAL_SCHEDULE = copy.deepcopy(SCHEDULE)

def reset_schedule():
       SCHEDULE.clear()
       SCHEDULE.update(copy.deepcopy(_INITIAL_SCHEDULE))

def check_availability(doctor, date_str):
    
    if doctor not in SCHEDULE:
        return  {
            "ok": False, 
            "error": "unknown_doctor"
                                }
    if date_str not in SCHEDULE[doctor]:
            return {
                      "ok":False,
                      "error":"unknown_date"
                                      }
    return {
              "ok": True, 
               "doctor" : doctor, 
               "date" : date_str,
               "open_slots":[time_slot for time_slot,patient in SCHEDULE[doctor][date_str].items() if patient is None]
                     }
    

def book_appointment(patient_name, doctor, date_str, time_str):
     if not patient_name or not patient_name.strip():
          return {
               'ok': False,
               'error': 'blank_patient_name'
          }
     if doctor not in SCHEDULE:
          return {'ok': False,
                  'error': 'unknown_doctor',
                  }
     if date_str not in SCHEDULE[doctor]:
          return {
               'ok': False,
               'error': 'unknown_date'
          }
     if time_str not in SCHEDULE[doctor][date_str]:
          return {
               'ok': False,
               'error': 'unknown_time'
          }
     if SCHEDULE[doctor][date_str][time_str] is not None:
          return {
               'ok': False,
               'error': 'slot_taken'
          }
     #after all checks patient_name is assigned said slot
     SCHEDULE[doctor][date_str][time_str]=patient_name
     return  {
          "ok": True, 
           "patient": patient_name.strip(), #to remve unnecessary trailing spaces '  Rahul '
           "doctor": doctor, 
           "date": date_str, 
           "time": time_str
           
     }

def cancel_appointment(patient_name, doctor, date_str, time_str):
     if doctor not in SCHEDULE:
          return {
               'ok': False,
               'error': 'unknown_doctor'
          }
     if date_str not in SCHEDULE[doctor]:
          return {
               'ok': False,
               'error': 'unknown_date'
          }
     slot = SCHEDULE[doctor][date_str]
     if time_str not in slot:
          return {
               'ok': False,
               'error': 'unknown_time'
          }
     if slot[time_str] is  None:
          return {
               'ok': False,
               'error': 'not_booked'
          }
     if slot[time_str].strip().lower()!=patient_name.strip().lower():
          return {
               'ok': False,
               'error': 'patient_mismatch'
          }
     slot[time_str]=None

     return {"ok": True, "patient": patient_name, "doctor": doctor, "date": date_str, "time": time_str}

def reschedule_appointment(patient_name, doctor, old_date, old_time, new_date, new_time):
     if not patient_name or not patient_name.strip():
               return {
                    'ok': False,
                    'error': 'blank_patient_name'
               }
     if doctor not in SCHEDULE:
               return {
                    'ok': False,
                    'error': 'unknown_doctor'
               }
     if old_date not in SCHEDULE[doctor]:
               return {
                    'ok': False,
                    'error': 'unknown_date'
               }
     if new_date not in SCHEDULE[doctor]:
                    return {
                         'ok': False,
                         'error': 'unknown_date'
                    }
     if old_time not in SCHEDULE[doctor][old_date]:
                         return {
                              'ok': False,
                              'error': 'unknown_time'
                         }
     if new_time not in SCHEDULE[doctor][new_date]:
                    return {
                         'ok': False,
                         'error': 'unknown_time'
                    }
     if SCHEDULE[doctor][old_date][old_time] is None:
            return {
                   'ok' : False ,
                   'error' : 'not_booked'
            }       
     if SCHEDULE[doctor][old_date][old_time].strip().lower()!=patient_name.strip().lower() :
            return {
                   'ok' : False,
                   'error' : 'patient_mismatch'
            }
     if old_date==new_date and old_time==new_time:
            return {
                   'ok' : False,
                   'error' : 'same_slot'
            }
     
     if SCHEDULE[doctor][new_date][new_time] is not None:
            return {
                   'ok' : False,
                   'error' : 'slot_taken'
            }

     
     booked_name=SCHEDULE[doctor][old_date][old_time]
     SCHEDULE[doctor][old_date][old_time]=None 
     SCHEDULE[doctor][new_date][new_time]=booked_name
     return {
                   "ok": True, 
                    "patient": patient_name, 
                    "doctor": doctor, 
                    "old_date": old_date,
                    "old_time": old_time,
                    "new_date": new_date, 
                    "new_time": new_time
            }

     
     

if __name__ == "__main__":   #Code under that line runs only when you execute python tools.py
     print(check_availability("Dr. Rao", TODAY))      # note the open slots
     book_appointment("Temp Patient", "Dr. Rao", TODAY, "09:00")
     print(check_availability("Dr. Rao", TODAY))      # 09:00 gone
     reset_schedule()
     print(check_availability("Dr. Rao", TODAY))      # must match the FIRST print
     book_appointment("Temp Patient", "Dr. Rao", TODAY, "09:00")
     reset_schedule()
     print(check_availability("Dr. Rao", TODAY))      # still matches the first print
    
