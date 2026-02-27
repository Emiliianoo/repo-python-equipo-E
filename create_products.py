import json
import xmlrpc.client
import os
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("ODOO_URL")
db = os.getenv("ODOO_DB")
username = os.getenv("ODOO_USER")
password = os.getenv("ODOO_PASSWORD")

# Conectar
common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
uid = common.authenticate(db, username, password, {})

if not uid:
    raise Exception("No pude iniciar sesión. Revisa db/username/password.")

models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")

# Leer JSON
with open("products.json", "r", encoding="utf-8") as f:
    products = json.load(f)

# Crear productos
for p in products:
    vals = {
        "name": p["name"],
        "default_code": p.get("default_code", False),
        "list_price": float(p.get("list_price", 0)),
        "type": p.get("type", "consu"),
    }

    new_id = models.execute_kw(db, uid, password, "product.template", "create", [vals])
    print("Creado:", new_id, "-", p["name"])