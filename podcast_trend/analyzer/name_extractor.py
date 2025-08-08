import re

STOP = {"podcast","odcinek","live","część","czesc","ft","feat","ep","premiera","rozmowa","gość","gosc","prowadzący","prowadzący","z","u","vs","x"}

def clean_title(t:str)->str:
    t = re.sub(r"[^]]|[^])|{[^}]}", " ", t)
    t = re.sub(r"[#№]\s\d+"," ", t)
    t = re.sub(r"\d{1,2}\s*/\s*\d{1,2}"," ", t)
    t = re.sub(r"[^\w\s-.'']", " ", t, flags=re.UNICODE)
    return re.sub(r"\s+"," ", t).strip()

def is_stop(w:str)->bool:
    return w.lower() in STOP

def normalize_name(n:str)->str:
    n = n.replace("'","'").replace(" .",".").strip()
    parts = [p.capitalize() for p in n.split()]
    return " ".join(parts)

def extract_names_from_title(title:str)->list[str]:
    t = clean_title(title)
    tokens = t.split()
    cand = set()
    for i in range(len(tokens)-1):
        a,b = tokens[i], tokens[i+1]
        if a[0:].istitle() and b[0:].istitle() and not is_stop(a) and not is_stop(b):
            cand.add(normalize_name(f"{a} {b}"))
    # single-word nicki po znacznikach typu ft. lub na końcu
    m = re.findall(r"(?:ft.?|feat.?)\s+([A-Za-zÀ-ž][\w'.-]{2,})", t, flags=re.IGNORECASE)
    for x in m:
        if not is_stop(x):
            cand.add(normalize_name(x))
    return sorted(cand)
