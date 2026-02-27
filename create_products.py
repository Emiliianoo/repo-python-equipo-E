import json
import xmlrpc.client
import os
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("ODOO_URL")
db = os.getenv("ODOO_DB")
username = os.getenv("ODOO_USER")
password = os.getenv("ODOO_PASSWORD")

PRODUCTS_FILE = "products.json"


def authenticate_odoo():
    common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
    uid = common.authenticate(db, username, password, {})
    if not uid:
        raise Exception("No se pudo autenticar. Revisa db/username/password.")
    return uid


def get_odoo_models():
    return xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")


def load_products_from_json():
    with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict) and "products" in data and isinstance(data["products"], list):
        return data["products"]

    if isinstance(data, list):
        return data

    raise Exception(f"Formato inválido en {PRODUCTS_FILE}. Debe ser una lista o un objeto con 'products'.")


def product_exists(models, uid, default_code):
    ids = models.execute_kw(
        db, uid, password,
        "product.template", "search",
        [[["default_code", "=", default_code]]],
        {"limit": 1}
    )
    return bool(ids)


def create_product_template(models, uid, p):
    vals = {
        "name": p["name"],
        "default_code": p.get("default_code") or False,
        "list_price": float(p.get("list_price", 0)),
        "type": p.get("type", "consu"),
    }
    return models.execute_kw(db, uid, password, "product.template", "create", [vals])


def get_product_variant_id(models, uid, template_id):
    ids = models.execute_kw(
        db, uid, password,
        "product.product", "search",
        [[["product_tmpl_id", "=", template_id]]],
        {"limit": 1}
    )
    return ids[0] if ids else None


def update_product_stock(models, uid, product_id, template_id, units):
    wiz_id = models.execute_kw(
        db, uid, password,
        "stock.change.product.qty", "create",
        [{
            "product_id": product_id,
            "product_tmpl_id": template_id,
            "new_quantity": float(units)
        }]
    )
    models.execute_kw(db, uid, password, "stock.change.product.qty", "change_product_qty", [[wiz_id]])


def process_products(models, uid, productos):
    for p in productos:
        try:
            code = (p.get("default_code") or "").strip()
            if not code:
                print("Saltado (sin default_code):", p.get("name"))
                continue

            if product_exists(models, uid, code):
                print("Producto existente:", p["name"], "-", code)
                continue

            template_id = create_product_template(models, uid, p)
            variant_id = get_product_variant_id(models, uid, template_id)

            units = p.get("units", 0)
            if variant_id and float(units) > 0:
                update_product_stock(models, uid, variant_id, template_id, units)

            print("Producto creado:", p["name"], "| code:", code, "| units:", units)

        except Exception as e:
            nombre = p.get("name") if isinstance(p, dict) else str(p)
            print("Error al crear:", nombre, "|", str(e))


uid = authenticate_odoo()
models = get_odoo_models()
productos = load_products_from_json()
process_products(models, uid, productos)

print("Todos los productos procesados.")