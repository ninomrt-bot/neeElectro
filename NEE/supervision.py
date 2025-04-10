import paho.mqtt.publish as publish
from datetime import datetime

# === Configuration MQTT (réseau IT) ===
MQTT_BROKER = "10.10.0.10"              # Serveur InfluxDB + Mosquitto (IT)
MQTT_PORT = 1883                        # Port par défaut MQTT
MQTT_TOPIC = "nee/ligne4/production"   # Sujet personnalisé pour Grafana

def envoyer_donnees(of, status="OK"):
    """
    Envoie les infos de production d’un OF vers le broker MQTT
    Pour affichage dans Grafana via InfluxDB
    """
    try:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        payload = f"of={of['numero']},code={of['code']},quantite={of['quantite']},status={status},timestamp=\"{now}\""

        publish.single(
            topic=MQTT_TOPIC,
            payload=payload,
            hostname=MQTT_BROKER,
            port=MQTT_PORT
        )

        print(f"📡 MQTT envoyé → {payload}")
    except Exception as e:
        print(f"❌ Erreur MQTT : {e}")
