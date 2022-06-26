# API Created by Amogh ASV (https://github.com/0xcabrex/)
# API for Ticket Scanner Project.

"""
Module that runs the API to create various events and do operations on participant details.
"""

from flask import Flask, jsonify, request
from database.dbIntegration import *
from datetime import datetime
import pytz
import sys



app = Flask(__name__)

database = DatabaseIntegration()

# ---------------------------------------------------- error codes -----------------------------------------------------------------

error = {
    "status": "hash not found"
}

invalid = {
    "status": "Event has ended"
}

analytics_error = {
    "status": "No analytics for the given data"
}

# ---------------------------------------------------- participants parameters -----------------------------------------------------

@app.route('/')
def index():
    return error, 404



@app.route('/<hash>', methods=['GET'])
def get_data(hash):

    """Returns a dictionary with data of the participant for the given hash

    methods: GET

    :param hash: (string) hash 
    :return: (dictionary) details of participant
    """

    print(f"the hash is: {hash}")

    participant_data = database.retrieve_participants_details(hash)

    if participant_data is not None:
        unique_event_name = participant_data["unique_event_name"]
        event_data = database.retrieve_event_details(unique_event_name)

        event_date = datetime.strptime(event_data["event_date"], "%d/%m/%Y")
        present = datetime.now()

        # participant_data["registration_time"] = str(datetime.now().strftime("%d/%m/%Y %H:%M:%S:%f")).replace("-","/")
        participant_data["registration_time"] = datetime.now(tz=pytz.UTC).astimezone(pytz.timezone('Asia/Kolkata')).strftime("%d/%m/%Y %H:%M:%S:%f")

    if participant_data is not None:
        if event_date.date() > present.date():
            database.insert_analytics_data(participant_data)
            participant_data.pop("_id")
            return jsonify(participant_data)
        else:
            return invalid, 406
    else:
        return error, 404

@app.route('/insertparticipantdetails/', methods=["POST"])
def insert_participant_details():

    """Inserts participant details to database.

    methods: POST

    :return: Dictionary with status
    """

    form_data = request.form
    form_data = dict(form_data)

    data = {}

    if not "api_key" in form_data.keys():
        data["status"] = "api_key not found"
        return data, 401

    valid_api_key = database.is_valid_api_key(form_data["api_key"])

    if not valid_api_key["status"]:
        data["status"] = "API key not valid"
        return data, 401
    
    error_string = ""

    if not "name" in form_data.keys():
        error_string += "name,"
    if not "srn" in form_data.keys():
        error_string += "srn,"
    if not "phoneNumber" in form_data.keys():
        error_string += "phoneNumber,"
    if not "mailId" in form_data.keys():
        error_string += "mailId,"
    if not "teamName" in form_data.keys():
        error_string += "teamName,"
    if not "teamMembers" in form_data.keys():
        error_string += "teamMembers,"
    if not "hash" in form_data.keys():
        error_string += "hash,"
    if not "unique_event_name" in form_data.keys():
        error_string += "unique_event_name,"
    
    if error_string != "":
        data["status"] = f"{error_string} key not present in the form"
        return data, 404
        
    name = form_data["name"]
    srn = form_data["srn"]
    phoneNumber = form_data["phoneNumber"]
    mailId = form_data["mailId"]
    teamName = form_data["teamName"]
    teamMembers = form_data["teamMembers"]
    hash = form_data["hash"]
    unique_event_name = form_data["unique_event_name"]

    database.insert_participants_details(srn = srn, name = name, phoneNumber = phoneNumber, mailId = mailId, teamName = teamName, teamMembers = teamMembers, hash = hash, unique_event_name = unique_event_name)

    data = {}
    data["status"] = True
    return data


@app.route('/numberofparticipants/', methods = ['GET'])
def numberOfParticipants():
    """Returns the number of participants for the given unique_event_name

    methods: GET

    :return: Dictionary with key "count"
    """
    
    params = request.args
    
    error_string = ""
    data={}

    if not "unique_event_name" in params:
        error_string += "unique_event_name,"
    if not "api_key" in params:
        error_string += "api_key,"

    error_string = error_string.strip(',')

    if error_string != "":
        data["status"] = f"{error_string} key not present"
        return data, 404

    valid_api_key = database.is_valid_api_key(params["api_key"])

    if not valid_api_key["status"]:
        data["status"] = "api_key is invalid"
        return data, 401 

    count = database.number_of_participants(params["unique_event_name"])

    data["status"] = "OK"
    data["count"] = count

    return data


# ---------------------------------------------------- analytics -------------------------------------------------------------------

@app.route('/analytics/', methods=['GET'])
def get_analytics():
    """ Returns dictionary with analytics information

    methods: GET

    :return: dictionary with analytics information
    """

    params = request.args

    error_data = {}

    if not "unique_event_name" in params:
        if not "api_key" in params:
            error_data["status"] = "unique_event_name and api_key are missing parameters"
        else:
            error_data["status"] = "unique_event_name is a missing parameter"
    elif not "api_key" in params:
        error_data["status"] = "api_key is a missing parameter"

    if error_data != {}:
        return error_data, 401

    valid_api_key = database.is_valid_api_key(params["api_key"])

    if not valid_api_key["status"]:
        error_data["status"] = "API key not valid"
        return error_data, 401

    data = database.retrieve_analytics_data(params["unique_event_name"])

    if data is not None:
        return data
    else:
        return analytics_error, 404


# ---------------------------------------------------------- signin ----------------------------------------------------------------

@app.route('/signin/', methods=['POST'])
def signin_for_admin():
    """Does check for valid credentials passed through POST request

    methods: POST

    :return: dictionary with "status" key (True or False)
    """

    form_data = request.form

    form_error = {
        "status": ""
    }

    data = {
        "status": ""
    }

    if not "username" in form_data.keys():
        if not "password" in form_data.keys():
            form_error["status"] = "Username and Password field missing (CASE SENSITIVE)"
        else:
            form_error["status"] = "Username field missing (CASE SENSITIVE)"
    elif not "password" in form_data.keys():
        form_error["status"] = "Password field missing (CASE SENSITIVE)"


    if form_error["status"] != "":
        return form_error, 401
    
    signin_data = database.signin_admin(form_data["username"], form_data["password"])


    is_signin = signin_data["status"]

    data["status"] = is_signin

    if is_signin:
        data["api_key"] = signin_data["api_key"]
        data["role"] = signin_data["role"]


    return data
        

@app.route("/signup/", methods=['POST'])
def signup_for_admin():
    """Adds given user to said role and allots an API key to the user

    methods: POST

    :return: dictionary with key "status"
    """

    form_data = request.form

    form_error = {
        "status": ""
    }

    data = {
        "status": ""
    }

    print(form_data)

    if not "api_key" in form_data.keys():
        return {"status", "API key not found"}, 401

    if not "username" in form_data.keys():
        if not "password" in form_data.keys():
            if not "role" in form_data.keys():
                form_error["status"] = "username, password and role fields are missing (CASE SENSITIVE)"
            else:
                form_error["status"] = "username and password field missing (CASE SENSITIVE)"
        elif not "role" in form_data.keys():
            form_error["status"] = "username and role fields are missing (CASE SENSITIVE)"
        else:
            form_error["status"] = "username field missing (CASE SENSITIVE)"
    elif not "password" in form_data.keys():
        if not "role" in form_data.keys():
            form_error["status"] = "password and role fields are missing (CASE SENSITIVE)"
        else:
            form_error["status"] = "password field missing (CASE SENSITIVE)"


    if form_error["status"] != "":
        return form_error, 401
    
    is_signin = database.signup_admin(form_data["username"], form_data["password"], form_data["role"])

    data["status"] = is_signin


    return data


@app.route('/checkusername/', methods=["GET"])
def check_username():
    """Checks if username exists in the database

    methods: GET

    :return: dictionary with "status" key
    """

    form_data = request.args

    data = {}

    error_data = {
        "status": "username field not found (CASE SENSITIVE)"
    }

    if not "username" in form_data.keys():
        return error_data, 404

    is_valid_username = database.check_username(form_data["username"])

    if is_valid_username:
        data["status"] = True
    else:
        data["status"] = False

    return data


@app.route('/api/<key>')
def api_check(key):
    """Check if the given API string is valid or not

    methods: ANY

    :param key: API key to check validity for
    :return: Dictionary with "status" key
    """

    details = database.is_valid_api_key(key)

    return details

# ---------------------------------------------------- Event details ----------------------------------------------------------------

@app.route('/eventinsert/', methods=['POST'])
def insert_event_details_api():
    """Inserting Event details into the database
    methods: POST

    :return: Dictionary with "status" key
    """
    
    form_data = request.form

    data = {}

    error_string = ""

    if not "api_key" in form_data.keys():
        data["status"] = "api_key not found"
        return data, 401

    valid_api_key = database.is_valid_api_key(form_data["api_key"])

    if not valid_api_key["status"]:
        data["status"] = "API key invalid"
        return data, 401

    if not "event_name" in form_data.keys():
        error_string += "event_name,"
    if not "event_date" in form_data.keys():
        error_string += "event_date,"
    if not "event_time" in form_data.keys():
        error_string += "event_time,"
    if not "event_duration" in form_data.keys():
        error_string += "event_duration,"
    if not "event_venue" in form_data.keys():
        error_string += "event_venue,"
    
    if not error_string == "":
        data["status"] = f"{error_string.strip(',')} not present in the form." 
        return data, 404

    database.insert_event_details(form_data["event_name"], form_data["event_date"], form_data["event_time"], form_data["event_duration"], form_data["event_venue"])

    data["status"] = "OK"

    return data

@app.route("/checkevent/", methods=["GET"])
def check_for_event():
    """Checks if there exists an event for the entered unique_event_name string.

    methods: GET

    :return: Dictionary with "status" key
    """
    
    form_data = request.args
    data = {}

    if not "api_key" in form_data.keys():
        data["status"] = "api_key not found"
        return data, 401

    valid_api_key = database.is_valid_api_key(form_data["api_key"])

    if not valid_api_key["status"]:
        data["status"] = "API key not valid"
        return data, 401


    if not "unique_event_name" in form_data.keys():
        data["status"] = "unique_event_name doesnt exist."
        return data, 404

    db_data = database.retrieve_event_details(form_data["unique_event_name"])

    if db_data is None:
        data["status"] = False
    else:
        data["status"] = True

    return data

@app.route('/retrieveevent/', methods=["GET"])
def retrieve_event():
    """Returns details of the event for the given unique_event_name

    methods: GET

    :return: Dictionary with details about the event and "status" key
    """

    form_data = request.args
    data = {}

    if not "api_key" in form_data.keys():
        data["status"] = "api_key not found"
        return data, 401

    valid_api_key = database.is_valid_api_key(form_data["api_key"])

    if not valid_api_key["status"]:
        data["status"] = "API key not valid"
        return data, 401


    if not "unique_event_name" in form_data.keys():
        data["status"] = "unique_event_name doesnt exist."
        return data, 404

    db_data = database.retrieve_event_details(form_data["unique_event_name"])

    if db_data is None:
        data["status"] = False
        return data, 404

    db_data["status"] = True

    return db_data


# ---------------------------------------------------- Server checking -------------------------------------------------------------

@app.route('/checkstatus/', methods=['GET', 'POST'])
def checkstatus():
    """ Checks the status of the server

    methods: GET, POST

    :return: Dictionary with "status" key 
    """


    data = {}
    data["status"] = "OK"

    return data

# ---------------------------------------------------- Flask Server ----------------------------------------------------------------

if __name__ == '__main__':


    args = sys.argv

    if len(args) > 1 and args[1] == "debug":
        app.run(debug=True, host="0.0.0.0", port="80")
    else:
        app.run(debug=False, host="0.0.0.0", port="80")

