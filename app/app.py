from fastapi import FastAPI
import sqlite3, json
from .GmailBotInsertData import main_insert,authenticate_gmail,create_connection_db
from pydantic import BaseModel
from typing import List
from fastapi import FastAPI, UploadFile, File
from googleapiclient.discovery import build


#########################################################################################################################################################
#                                                        MODELS COMING IN USE                                                                           #
#########################################################################################################################################################

class FieldModel(BaseModel):
    field: str
    predicate: str
    value: str

class ActionModel(BaseModel):
    action_type: str
    action_value: str

class RuleModel(BaseModel):
    rule_name: str
    rule_description: str
    rule_type: str
    rules: List[FieldModel]
    actions: List[ActionModel]

#########################################################################################################################################################
#                                                        FUNCTIONS COMING IN USE                                                                        #
#########################################################################################################################################################


def fetch_all_rows():
    conn,curr = create_connection_db()
    curr.execute("Select * FROM emails")
    rows = curr.fetchall()
    return rows

#########################################################################################################################################################
#                                                        FAST API COMING IN USE                                                                         #
#########################################################################################################################################################


app = FastAPI()
@app.get("/GET_DATA")
async def alldata() -> dict:
    try:
        return{"rows":fetch_all_rows()}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/LENGTH_DATA")
async def lendata() -> dict:
    try:
        return { "TotalRows" : len(fetch_all_rows()) }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/INSERT_DATA")
async def insert_data():
    try:
        result = main_insert()
        return {"status": "success", "output": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/CREATE_RULE")
async def create_rule(rule_data: RuleModel):
    ''' Get a json input make it as a rule for emails and save it as json file'''
    rule = {
        "rule_name": rule_data.rule_name,
        "rule_description": rule_data.rule_description,
        "rule_type": rule_data.rule_type,
        "rules": [
            {"field": field.field, "predicate": field.predicate, "value": field.value} 
            for field in rule_data.rules
        ],
        "actions": [
            {"action_type": action.action_type, "action_value": action.action_value} 
            for action in rule_data.actions
        ]
    }
    rule_json = json.dumps(rule, indent=2)
    
    file_name = f"{rule_data.rule_name.replace(' ', '_')}.json"
    # saving it in Json rules folder
    with open('json_rules/{}'.format(file_name), "w") as json_file:
        json_file.write(rule_json)

    return {"message": f"Rule '{rule_data.rule_name}' saved as {file_name}"}




def mark( ids , action_value ):

        creds = authenticate_gmail()
        service = build('gmail', 'v1', credentials=creds)

        for each_id in ids:
            if action_value.lower() == "read":
                body = {
                    'removeLabelIds': ['UNREAD']
                }

                service.users().messages().modify( userId='me', id=each_id, body=body).execute()
                print(f"Marked email with ID: {each_id} as read")
            elif action_value.lower() == "unread":
                body = {
                    'addLabelIds': ['UNREAD']
                }

                service.users().messages().modify( userId='me', id=each_id, body=body).execute()
                print(f"Marked email with ID: {each_id} as unread")
            else:
                print(f"Invalid action: {action_value}. No action taken.")

def move( ids, action_value ):
        creds = authenticate_gmail()
        service = build('gmail', 'v1', credentials=creds)
        for each_ids in ids:
            label_id = action_value.upper()
            service.users().messages().modify(userId='me', id=each_ids,
                                          body={'addLabelIds': [label_id]}).execute()

            print(f"Moved email with ID: {each_ids} to folder: {action_value}")

@app.post("/EXECUTE_RULE")
async def execute_rule(file: UploadFile = File(...)):
    '''Reading the file
        Finally applying those rules to fetch the given emails that are needed.
    '''
    contents = await file.read()
    json_data = json.loads(contents.decode('utf-8'))

    rule_type = json_data['rule_type']    
    rules = json_data['rules']
    
    #from subject message , date
    search_on = rules[0]['field']
    #["contains", "does not contain", "equals", "does not equal"],
    scenario = rules[0]['predicate']
    to_search = rules[0]['value']

    actions = json_data['actions']
    action_type = actions[0]['action_type']
    action_value = actions[0]['action_value']


    full_data = fetch_all_rows()

    # Result email , onky those emails that have passed the rules will be saved
    result_emails = []

    # id_ of those emaials , so action can be taken on them such as trash and spam.
    id_ = []

    for each_mail in full_data:
        id = each_mail[0]
        sender = each_mail[1]
        subject = each_mail[2]
        email_text =each_mail[3]
        date_time = each_mail[4]


        check_list = [sender, subject, email_text]
        if rule_type.lower():
            if (scenario == "does not contain") and (scenario == "does not equal"):
                for each_var in check_list:
                    if each_var:
                        if to_search.lower() not in each_var.lower():
                            result_emails.append(each_mail)
                            id_.append(id)
            else:
                for each_var in check_list:
                    if each_var:
                        if to_search.lower() in each_var.lower():
                            result_emails.append(each_mail)
                            id_.append(id)
    print(id_)
    if action_type.lower() == 'move':
        move(id_,action_value)
    else:
        mark(id_, action_value)

    return {"result":result_emails}
