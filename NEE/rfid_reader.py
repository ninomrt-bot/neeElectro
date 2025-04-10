

import serial

# === Configuration du port série (à adapter si besoin) ===
PORT = "/dev/ttyUSB0"  # ou ttyACM0 selon le lecteur
BAUDRATE = 9600        # valeur typique, à vérifier

def lire_badge():
    """
    Lit un badge RFID et retourne son identifiant (hex)
    """
    try:
        ser = serial.Serial(PORT, BAUDRATE, timeout=3)
        badge = ser.readline().decode('utf-8').strip()
        print(f"📡 Badge lu : {badge}")
        return badge
    except Exception as e:
        print(f"❌ Erreur lecture badge : {e}")
        return "UNKNOWN"
