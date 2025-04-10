import xmlrpc.client

URL = "http://10.10.0.10:9060"
BDD = "NEE"
USERNAME = "OperateurC@nee.com"
PASSWORD = "nee25Codoo!"

def connect_odoo():
    common = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/common")
    uid = common.authenticate(BDD, USERNAME, PASSWORD, {})
    models = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/object")
    return uid, models

def get_of_list():
    """
    Récupère la liste des OF confirmés avec :
      - numero : nom de l’OF
      - code : NomArticle (codeBOM)   <-- si BOM
      - quantite
    """
    try:
        uid, models = connect_odoo()

        # Lire mrp.production
        ofs = models.execute_kw(
            BDD, uid, PASSWORD,
            'mrp.production', 'search_read',
            [[['state', '=', 'confirmed']]],
            {
                'fields': [
                    'name',         # nom OF (OF00012)
                    'product_id',   # [id, nom_prod]
                    'product_qty',
                    'bom_id'        # [id, "Nom BOM"]
                ],
                'limit': 100
            }
        )

        liste_of = []
        for of_data in ofs:
            numero = of_data['name']
            quantite = of_data['product_qty']

            product_name = "Produit inconnu"
            if of_data['product_id']:
                product_name = of_data['product_id'][1]  # le nom du produit

            # Récupérer la BOM si elle existe
            code_bom = None
            if of_data.get('bom_id'):
                bom_id = of_data['bom_id'][0]    # ID de la BOM
                code_bom = get_bom_code(bom_id)  # fonction qu’on va créer

            # Construire le code à afficher
            if code_bom:
                code_affiche = f"{product_name} ({code_bom})"
            else:
                # si pas de BOM => "?"
                code_affiche = f"{product_name} (?)"

            liste_of.append({
                "numero": numero,
                "code": code_affiche,
                "quantite": quantite
            })

        return liste_of

    except Exception as e:
        print(f"❌ get_of_list : {e}")
        return []

def get_bom_code(bom_id):
    """
    Lit la nomenclature mrp.bom et renvoie le champ 'code'.
    """
    try:
        uid, models = connect_odoo()
        bom_data = models.execute_kw(
            BDD, uid, PASSWORD,
            'mrp.bom', 'read',
            [bom_id],
            {'fields': ['code']}
        )
        if bom_data and 'code' in bom_data[0]:
            return bom_data[0]['code']  # la référence BOM
        return None

    except Exception as e:
        print(f"❌ get_bom_code : {e}")
        return None

def get_of_components(of_name):
    """
    Récupère la liste des composants REELS depuis stock.move (move_raw_ids),
    ex: ["ModA x2", "Vis M6 x10"].
    """
    try:
        uid, models = connect_odoo()

        of_data = models.execute_kw(
            BDD, uid, PASSWORD,
            'mrp.production', 'search_read',
            [[['name', '=', of_name]]],
            {'fields': ['id', 'move_raw_ids'], 'limit': 1}
        )
        if not of_data:
            return [f"❌ OF '{of_name}' introuvable"]

        move_ids = of_data[0].get('move_raw_ids', [])
        if not move_ids:
            return ["❓ Aucun composant"]

        moves = models.execute_kw(
            BDD, uid, PASSWORD,
            'stock.move', 'read',
            [move_ids],
            {'fields': ['product_id', 'product_uom_qty']}
        )

        if not moves:
            return ["❓ Pas de moves pour cet OF"]

        composants = []
        for mv in moves:
            prod_name = mv['product_id'][1] if isinstance(mv['product_id'], list) else "Inconnu"
            qty = mv['product_uom_qty']
            composants.append(f"{prod_name} x{qty}")

        return composants

    except Exception as e:
        print(f"❌ get_of_components : {e}")
        return [f"❌ Erreur get_of_components : {e}"]
