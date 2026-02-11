def classify_asset(name):
    name = name.lower()

    if "ahu" in name or "chiller" in name:
        return "HVAC"
    elif "dg" in name:
        return "DG"
    elif "lift" in name:
        return "Lifts"
    elif "stp" in name:
        return "STP"
    elif "wtp" in name:
        return "WTP"
    elif "cctv" in name:
        return "CCTV"
    elif "fire" in name:
        return "Fire Fighting"
    elif "bms" in name:
        return "BMS"
    else:
        return "Electrical"
