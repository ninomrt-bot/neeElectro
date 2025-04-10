"""
opcua_client.py

📡 Gère les communications OPC-UA entre Python et les automates WAGO :
- Ligne 1 : reçoit un OF (numéro, code, quantité) → Trigger_Start
- Ligne 1 : peut renvoyer l'état 'En cours'
- Ligne 3 : renvoie l'état final (Ctrl OK, Ctrl NOK) + horodatage
"""

from opcua import Client

# Adresses OPC-UA
LGN01_URL = "opc.tcp://172.30.30.11:4840"  # Ligne 1 = assemblage
LGN03_URL = "opc.tcp://172.30.30.13:4840"  # Ligne 3 = contrôle qualité

def envoyer_of_aux_lignes(of):
    """
    Envoie un OF actif aux automates :
    - Ligne 1 reçoit : numéro, code, quantité, Trigger_Start
    - Ligne 3 reçoit aussi les infos (pour traçabilité complète)
    """
    try:
        numero = int(of["numero"])
        code = str(of["code"])
        quantite = int(of.get("quantite", 1))

        client1 = Client(LGN01_URL)
        client3 = Client(LGN03_URL)
        client1.connect()
        client3.connect()

        # Nœuds Ligne 1 (réception OF)
        client1.get_node("ns=2;s=OF_Actif_Numero").set_value(numero)
        client1.get_node("ns=2;s=OF_Actif_Code").set_value(code)
        client1.get_node("ns=2;s=OF_Actif_Quantite").set_value(quantite)
        client1.get_node("ns=2;s=Trigger_Start").set_value(True)

        # Nœuds Ligne 3 (pour info parallèle)
        client3.get_node("ns=2;s=OF_Actif_Numero").set_value(numero)
        client3.get_node("ns=2;s=OF_Actif_Code").set_value(code)
        client3.get_node("ns=2;s=OF_Actif_Quantite").set_value(quantite)

        print(f"✅ OF {numero} envoyé aux lignes 1 & 3 : {code} x{quantite}")

    except Exception as e:
        print(f"❌ Erreur envoi OF : {e}")

    finally:
        try:
            client1.disconnect()
            client3.disconnect()
        except:
            pass


def lire_etat_ligne1(of_num):
    """
    Lit l'état de l'OF actif sur la ligne 1 (En cours)
    """
    try:
        client = Client(LGN01_URL)
        client.connect()
        node = client.get_node(f"ns=2;s=Etat_OF[{of_num}]")
        etat = node.get_value()
        print(f"📥 Ligne 1 : OF {of_num} → état = {etat}")
        return etat
    except Exception as e:
        print(f"❌ Erreur lecture état ligne 1 OF {of_num} : {e}")
        return "Indisponible"
    finally:
        try:
            client.disconnect()
        except:
            pass


def lire_traceabilite_ligne3(of_num):
    """
    Lit l'état final (OK, NOK...) et horodatage depuis ligne 3
    """
    try:
        client = Client(LGN03_URL)
        client.connect()
        etat = client.get_node(f"ns=2;s=Etat_OF[{of_num}]").get_value()
        hora = client.get_node(f"ns=2;s=Hora_OF[{of_num}]").get_value()
        print(f"📤 Ligne 3 : OF {of_num} → {etat} à {hora}")
        return etat, hora
    except Exception as e:
        print(f"❌ Erreur lecture trace ligne 3 OF {of_num} : {e}")
        return "Indisponible", "—"
    finally:
        try:
            client.disconnect()
        except:
            pass
