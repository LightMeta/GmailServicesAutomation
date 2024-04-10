import json
from GmailBotInsertData import authenticate_gmail,create_connection_db
from googleapiclient.discovery import build

def fetch_all_rows():
    conn,curr = create_connection_db()
    curr.execute("Select * FROM emails")
    rows = curr.fetchall()
    return rows

def create_json_rule():
    rule_name = input("Enter the rule name:     ")
    rule_description = input("Enter the rule description:   ")
    rule_type = input("Enter the rule type (Any/All):   ")

    fields = []
    while True:
        field_name = input("Select field   From/Subject/Message/Received Date/Time:     ")
        predicate = input("Enter Predicates  contains/does not contain/equals/does not equal:   ")
        field_value = input("Enter the value we will search:    ")

        field = {"field": field_name,"predicate": predicate,"value": field_value}
        fields.append(field)

        another_field = input("Add another field? (yes/no): ")
        if another_field.lower() != "yes":
            break

    actions = []
    while True:
        action_type = input("Enter action Type mark/unmark:     ")
        action_value = input("Enter action value read/unread/move:      ")
        action = {"action_type": action_type,"action_value":action_value}
        actions.append(action)

        another_action = input("Add another action? (yes/no): ")
        if another_action.lower() != "yes":
            break

    rule = {
        "rule_name": rule_name,
        "rule_description": rule_description,
        "rule_type": rule_type,
        "rules": fields,
        "actions": actions
        }
    rule_json = json.dumps(rule, indent=2)
    
    # Save the rule as a JSON file with spaces replaced by underscores
    file_name = f"{rule_name.replace(' ', '_')}.json"
    with open(file_name, "w") as json_file:
        json_file.write(rule_json)

    print(f"Rule saved as {file_name}")

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
            label_id = action_value
            service.users().messages().modify(userId='me', id=each_ids,
                                          body={'addLabelIds': [label_id]}).execute()

            print(f"Moved email with ID: {each_ids} to folder: {action_value}")

def execute_rule():
    '''Reading the file
        Finally applying those rules to fetch the given emails that are needed.
    '''
    contents = open('reddit.json')
    json_data =json.load(contents)

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
    # import pdb; pdb.set_trace()

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

    if action_type.lower() == 'move':
        move(id_,action_value)
    else:
        mark(id_, action_value)
    
    return {"result":result_emails}

out = execute_rule()
