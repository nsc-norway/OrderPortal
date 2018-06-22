"""API example script: Edit an order; fields, title, tags and history.

NOTE: You need to change several variables to make this work. See below.

NOTE: This uses the third-party 'requests' module, which is much nicer than
the standard 'urllib' module.
"""

from __future__ import print_function
import json
import requests # http://docs.python-requests.org/en/master/

# Variables whose values must be changed for your site:
BASE_URL = 'http://localhost:8886'  # Base URL for your OrderPortal instance.
API_KEY = '7f075a4c5b324e3ca63f22d8dc0929c4'  # API key for the user account.
ORDER_ID = 'NMI00603'  # The ID or IUID for the order.


url = "{base}/api/v1/order/{id}".format(base=BASE_URL,
                                        id=ORDER_ID)
headers = {'X-OrderPortal-API-key': API_KEY}

data = {'title': 'New title',
        'tags': ['first_tag', 'second_tag'],  # NOTE: identifier format!
        'links': {'external': [{'href': 'http://scilifelab.se',
                                'title': 'SciLifeLab'},
                               {'href': 'http://dummy.com'}]},
        'fields': {'Expected_results': 'Great!',
                   'Node_support': 'KTH'},
        'history': {'accepted': '2018-06-01'}}

response = requests.post(url, headers=headers, json=data)
assert response.status_code == 200, (response.status_code, response.reason)

print(json.dumps(response.json(), indent=2))
