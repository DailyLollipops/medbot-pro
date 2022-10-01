def determine_pulse_rate_rating(age, pulse_rate):
    if(age <= 1):
        if(pulse_rate < 100):
            rating = 'Low Pulse Rate'
        elif(pulse_rate < 160):
            rating = 'Normal Pulse Rate'
        elif(pulse_rate >= 160):
            rating = 'High Pulse Rate'
        else:
            rating = False
    elif(age <= 3):
        if(pulse_rate < 80):
            rating = 'Low Pulse Rate'
        elif(pulse_rate < 130):
            rating = 'Normal Pulse Rate'
        elif(pulse_rate >= 130):
            rating = 'High Pulse Rate'
        else:
            rating = False
    elif(age <= 5):
        if(pulse_rate < 80):
            rating = 'Low Pulse Rate'
        elif(pulse_rate < 120):
            rating = 'Normal Pulse Rate'
        elif(pulse_rate >= 120):
            rating = 'High Pulse Rate'
        else:
            rating = False
    elif(age <= 10):
        if(pulse_rate < 70):
            rating = 'Low Pulse Rate'
        elif(pulse_rate < 110):
            rating = 'Normal Pulse Rate'
        elif(pulse_rate >= 110):
            rating = 'High Pulse Rate'
        else:
            rating = False
    elif(age <= 14):
        if(pulse_rate < 60):
            rating = 'Low Pulse Rate'
        elif(pulse_rate < 105):
            rating = 'Normal Pulse Rate'
        elif(pulse_rate >= 105):
            rating = 'High Pulse Rate'
        else:
            rating = False
    else:
        if(pulse_rate < 60):
            rating = 'Low Pulse Rate'
        elif(pulse_rate < 100):
            rating = 'Normal Pulse Rate'
        elif(pulse_rate >= 100):
            rating = 'High Pulse Rate'
        else:
            rating = False
    return rating

def determine_blood_pressure_rating(systolic, diastolic):
    if(systolic < 90 and diastolic < 60):
        rating = 'Low Blood Pressure'
    elif(systolic < 120 and diastolic < 80):
        rating = 'Normal'
    elif(systolic <= 129 and diastolic < 80):
        rating = 'Elevated Blood Pressure'
    elif(systolic <= 139 and diastolic <= 89):
        rating = 'High Blood Pressure Stage 1'
    elif(systolic <= 180 and diastolic <= 120):
        rating = 'High Blood Pressure Stage 2'
    elif(systolic > 180 and diastolic > 120):
        rating = 'Hypertensive Crisis'
    else:
        rating = False
    return rating

def determine_blood_saturation_rating(blood_saturation):
    if(blood_saturation < 95):
        rating = 'Low Blood Saturation'
    elif(blood_saturation <= 100):
        rating = 'Normal Blood Saturation'
    elif(blood_saturation > 100):
        rating = 'High Blood Saturation'
    else:
        rating = False
    return rating