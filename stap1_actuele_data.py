import requests
import json
import os
from datetime import datetime, timedelta

# ============ CONFIGURATIE (hier pas jij dingen aan) ============
import os
API_KEY = os.environ.get("WEERLIVE_API_KEY", "demo")          # API key opslaan in veilige plek in Github, zie stap 4a
LOCATIE = "de Bilt"     # Referentiepunt voor NL — later evt. meerdere locaties
DATA_FILE = "weerdata_geschiedenis.json"
RETENTION_DAYS = 7        # <-- Hoeveel dagen geschiedenis je wilt bewaren, pas gerust aan

def haal_actuele_data_op():
    """Haalt actuele KNMI-data + korte verwachting op."""
    url = f"https://weerlive.nl/api/weerlive_api_v2.php?key={API_KEY}&locatie={LOCATIE}"
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    return response.json()

def laad_geschiedenis():
    """Leest wat er al eerder is opgeslagen (nodig om verder te gaan, ook na een storing)."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def bewaar_geschiedenis(geschiedenis):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(geschiedenis, f, ensure_ascii=False, indent=2)

def ruim_oude_data_op(geschiedenis):
    """Verwijdert automatisch alles ouder dan RETENTION_DAYS."""
    grens = datetime.now() - timedelta(days=RETENTION_DAYS)
    return [
        item for item in geschiedenis
        if datetime.fromisoformat(item["opgehaald_op"]) > grens
    ]

def main():
    nieuwe_data = haal_actuele_data_op()
    geschiedenis = laad_geschiedenis()

    nieuwe_data["opgehaald_op"] = datetime.now().isoformat()
    geschiedenis.append(nieuwe_data)

    geschiedenis = ruim_oude_data_op(geschiedenis)
    bewaar_geschiedenis(geschiedenis)

    print(f"Opgeslagen. Aantal bewaarde metingen: {len(geschiedenis)}")

if __name__ == "__main__":
    main()