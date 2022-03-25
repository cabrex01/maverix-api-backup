from flask import Flask
from dbIntegration import *


app = Flask(__name__)

# data = [
#     {
#         "name": "Amogh ASV",
#         "srn": "PES1UG20EC002",
#         "mailid": "asvamogh@adgpes.com",
#         "hash": "df698a1a6c77ec45fcf37061d1731b2e"
#     },
#     {
#         "name": "Anirdhdhan",
#         "srn": "PES1UG20EC029",
#         "mailid": "blastrois2002@gmail.com",
#         "hash": "2a2d724d61caf214a159ed719875d5a8"
#     }
# ]

error = {
    "status": "hash not found"
}



@app.route('/')
def index():
    # return jsonify(error), 404
    return error, 404



@app.route('/<hash>', methods=['GET'])
def get_data(hash):

    print(f"the hash is: {hash}")
    # print(len(data))

    data = retrieve_participants_details(hash)

    if data is not None:
        return data
    else:
        return error, 404



if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port="80")
