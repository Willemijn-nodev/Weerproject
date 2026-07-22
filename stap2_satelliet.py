import requests
import os
from datetime import datetime, timedelta

# ============ CONFIGURATIE ============
SATELLIET_LAATSTE_URL = "https://cdn.knmi.nl/knmi/map/page/weer/actueel-weer/satelliet/satlast.jpg"
SATELLIET_LOOP_URL = "https://cdn.knmi.nl/knmi/map/page/weer/actueel-weer/satelliet/MET10_RGB-HRV-RGB_8bit-wwwloop_920x591.gif"
OPSLAG_MAP = "satellietbeelden"
RETENTION_DAYS = 7   # hoeveel dagen je wilt bewaren

def haal_op(url):
    headers = {"User-Agent": "Persoonlijk-weerproject (privegebruik)"}
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()
    return response.content

def bewaar(data, bestandsnaam):
    os.makedirs(OPSLAG_MAP, exist_ok=True)
    pad = os.path.join(OPSLAG_MAP, bestandsnaam)
    with open(pad, "wb") as f:
        f.write(data)
    return pad

def ruim_oude_bestanden_op():
    grens = datetime.now() - timedelta(days=RETENTION_DAYS)
    for bestand in os.listdir(OPSLAG_MAP):
        pad = os.path.join(OPSLAG_MAP, bestand)
        gemaakt_op = datetime.fromtimestamp(os.path.getmtime(pad))
        if gemaakt_op < grens:
            os.remove(pad)

def main():
    tijdstempel = datetime.now().strftime("%Y%m%d_%H%M")

    # 1. Laatste losse beeld
    laatste_data = haal_op(SATELLIET_LAATSTE_URL)
    pad_laatste = bewaar(laatste_data, f"satelliet_laatste_{tijdstempel}.jpg")
    print(f"Laatste beeld opgeslagen: {pad_laatste}")

    # 2. Loop van de afgelopen 6 uur
    loop_data = haal_op(SATELLIET_LOOP_URL)
    pad_loop = bewaar(loop_data, f"satelliet_loop_{tijdstempel}.gif")
    print(f"Loop opgeslagen: {pad_loop}")

    # 3. Opschonen op basis van bewaartermijn
    ruim_oude_bestanden_op()

if __name__ == "__main__":
    main()