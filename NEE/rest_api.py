# rest_api.py
from flask import Flask, request, jsonify

app = Flask(__name__)

# Simulation d'état de la ligne
LINE_STATUS = {
    "LGN-01": "OK",
    "LGN-02": "OK",
    "LGN-03": "NOK"
}

@app.route("/api/ligne/status", methods=["GET"])
def get_ligne_status():
    """
    Renvoie un JSON avec l'état de chaque îlot.
    ex: {
      "LGN-01": "OK",
      "LGN-02": "OK",
      "LGN-03": "NOK"
    }
    """
    return jsonify(LINE_STATUS), 200

@app.route("/api/ligne/start_of", methods=["POST"])
def start_of():
    """
    Reçoit un JSON contenant : {
      "numero": "OF0001",
      "code": "Assemblage 7 (REF7)",
      "quantite": 5
    }
    et on simule le lancement de l'OF sur la ligne.
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON body"}), 400

    numero = data.get("numero")
    code = data.get("code")
    qt = data.get("quantite")

    # Ici tu mets ta vraie logique, ex: ordonnancement,
    # mise en file d'attente, etc.
    print(f"🟢 Démarrage OF {numero} => {code}, qty={qt}")

    # Réponse
    return jsonify({
        "status": "OK",
        "OF": numero,
        "message": f"OF {numero} started with {qt} units"
    }), 200

if __name__ == "__main__":
    # Lancement du serveur sur http://127.0.0.1:5000
    app.run(port=5000, debug=True)
