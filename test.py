import sys
import json
sys.path.append(".")

from orderportal import utils
utils.load_settings("test_settings.yaml")
db = utils.get_db()


order = db['2c3143e5b2594bf4bc09488a27db961b']
# TODO : Testing
owner_email = order['owner']
owner_id = db.view("account/email")[owner_email].rows[0].id
owner = db[owner_id]

files = [] # TODO

print("{owner:" + json.dumps(owner) + ", order: " + json.dumps(order) + "}")

