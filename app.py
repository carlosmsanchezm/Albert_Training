from flask import Flask, jsonify, request
import json
import random

# Load mock bank data from clincuser.json to mock_bank_data
with open('clincuser.json', 'r') as clincuser_json:
    mock_bank_data = json.loads(clincuser_json.read())
    possible_accounts = [
    {
        'value': account['fields']['name'],
        'nickname': account['fields']['nickname'],
        'balance': account['fields']['balance']
    }
    for account in mock_bank_data
    if account['model'] == "bankapi.FinieAccount"
        and account['fields']['account_type'] == 'DE'
        and account['fields']['user'] == '271b36c8-5df4-49b0-a8b1-340d0e4f66a7'
    ]

app = Flask(__name__)

@app.route('/clean_hello', methods=['POST'])
def clean_hello():
    body = json.loads(str(request.data, encoding='utf-8'))
    print(json.dumps(body))

    # set response slot
    body['response_slots'] = {
        "response_type": "clean_hello",
        "visuals": {
            "name": "Hi Albert!"
        },
        "speakables": {
            "name": "Hi Albert!"
        }
    }

    return jsonify(body)

@app.route ("/get_balance", methods = ["POST"])
def get_balance():
    body=json.loads(str(request.data, encoding="utf-8"))
    print(json.dumps(body))
    
    accounts = {'checking' : '500',
                'savings' : '1000'
               };
    
    # Check to see if state equals account_transfer
    if body["state"] == "get_balance":
        # Check to see if there is a slot with the name _SOURCE_ACCOUNT_
        if "_SOURCE_ACCOUNT_" in body["slots"]:
            body["slots"]["_SOURCE_ACCOUNT_"]["values"][0]["resolved"] = 1
            # Check to see if the source type found in in the tokens key of _SOURCE_ACCOUNT_ is a valid account type.
            if body["slots"]["_SOURCE_ACCOUNT_"]["values"][0]["tokens"] == "checking":
                # fetch the account balance for the corresponding source value. Add a new balance property to the 
                # _SOURCE_ACCOUNT_ slot. Set the balance value to the balance found in step 3.
                body["slots"]["_SOURCE_ACCOUNT_"]["values"][0]["balance"] = accounts
                body["slots"]["_SOURCE_ACCOUNT_"]["values"][0]["value"] = body["slots"]["_SOURCE_ACCOUNT_"]["values"][0]["balance"]["checking"]
             
                #If it is not a valid account type, set an error property to invalid account type.                                 
            elif body["slots"]["_SOURCE_ACCOUNT_"]["values"][0]["tokens"] != "Checking":
                body["slots"]["_SOURCE_ACCOUNT_"]["values"][0]["error"] == "invalid"
                                                                    
    return jsonify(body)            
                                                   
                                                   
@app.route ('/account_transfer', methods = ['POST'])
def account_transfer():
    body=json.loads(str(request.data, encoding='utf-8'))
    print(json.dumps(body))                                              

    return jsonify(body)  


@app.route('/check_balance', methods=['POST'])
def check_balance():
    body = json.loads(str(request.data, encoding='utf-8'))

    if '_SOURCE_ACCOUNT_' in body['slots']:
        body['slots']['_SOURCE_ACCOUNT_']['candidates'] = possible_accounts

        body['slots']['_SOURCE_ACCOUNT_']['mappings'] = [
            {
                "algorithm": "partial_ratio",
                "threshold": 0.6,
                "type": "fuzzy",
                "values": {}
            }
        ]

        for account in possible_accounts:
            body['slots']['_SOURCE_ACCOUNT_']['mappings'][0]['values'][account['value']] = [
                account['value'],
                account['nickname']
            ]

        for account in body['slots']['_SOURCE_ACCOUNT_']['values']:
            account['resolved'] = 0
            # account['value'] = account['tokens']


    print(json.dumps(body['slots']['_SOURCE_ACCOUNT_']))
    print(json.dumps(body))


    return jsonify(body)

@app.route('/check_balance2', methods=['POST'])
def check_balance2():
    body = json.loads(str(request.data, encoding='utf-8'))
    print(json.dumps(body))

    # Add possible accounts as response slot
    body['response_slots'] = {
        'response_type': 'check_balance',
        'visuals': {
            'possible_accounts': possible_accounts
        },
        'speakables': {
            'possible_accounts': possible_accounts
        }
    }

    # Loop through events
    for event in body['event_list']:
        if event['slot'] == '_SOURCE_ACCOUNT_':
            # Add a new widget for each mapped account
            if event['new_status'] == 'MAPPED':
                # resolve account_match
                body['slots']['_SOURCE_ACCOUNT_']['values'][event['index']]['status'] = 'CONFIRMED'

                # Add visual_payload to payload if not already there
                if 'visual_payload' not in body:
                    body['visual_payload'] = {
                        'widget': {
                            'type': 'list',
                            'list_type': 'vertical',
                            'children': []
                        }
                    }
                    
            # Reject accounts that don't match
            elif event['new_status'] == 'FAILED_MAPPING':
                body['slots']['_SOURCE_ACCOUNT_']['values'][event['index']]['status'] = 'REJECTED'
            # Remove confirmed accounts
            elif event['new_status'] == 'CONFIRMED':
                body['slots']['_SOURCE_ACCOUNT_']['values'][event['index']]['status'] = 'DELETE'
            # Configure slot mapper if source account was extracted
            elif event['new_status'] == 'EXTRACTED':
                # Add possible accounts as slot mapper candidates
                body['slots']['_SOURCE_ACCOUNT_']['candidates'] = possible_accounts

                # Configure a fuzzy mapper mapper
                body['slots']['_SOURCE_ACCOUNT_']['mappings'] = [
                    {
                        "algorithm": "simple_ratio",
                        "threshold": 0.6,
                        "type": "fuzzy",
                        "values": {}
                    }
                ]

                # Add value and nickname as secondary clusters
                for account in possible_accounts:
                    body['slots']['_SOURCE_ACCOUNT_']['mappings'][0]['values'][account['value']] = [
                        account['value'],
                        account['nickname']
                    ]

    print(json.dumps(body))
    return jsonify(body)

if __name__ == '__main__':
    app.run()
