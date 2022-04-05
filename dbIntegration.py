import pymongo
from pymongo import MongoClient
import os
import certifi


ca = certifi.where()
mongodbclient_token = os.getenv("DATABASE_CLIENT_URL")

if mongodbclient_token is None:
	try:
		with open('./mongodbclient.0', 'r', encoding='utf-8') as client_url:
			print("Using MongoDB cluster url provided in file")
			cluster = MongoClient(client_url.read(), tlsCAFile=ca)
	except FileNotFoundError:
		print("File not found [mongodbclient.0]")
		print("Neither environment variable nor client file exist")
		print("Abort")
		exit()
else:
	print("Using MongoDB cluster url provided in environment variable..")
	cluster = MongoClient(mongodbclient_token, tlsCAFile=ca)


db = cluster["ticket_scanner"]
participants = db["participants"]

print("Database connection has been established\n")



def insert_participants_details(srn, name, phoneNumber, mailId, teamName, teamMembers, hash):
    
    details = None
    details = participants.find_one({"hash": str(hash)})

    if details is not None:
        participants.delete_one({"hash": str(hash)})

    results = participants.insert_one({"name": str(name), "srn": str(srn), "phoneNumber": str(phoneNumber), "mailId": str(mailId), "teamName": str(teamName), "teamMembers": str(teamMembers), "hash": str(hash)})

def retrieve_participants_details(hash):
    
    details = None
    details = participants.find_one({"hash": str(hash)})
    if details is not None:
        details.pop("_id")
    return details

def delete_participants_details(hash):

    details = None
    details = participants.find_one({"hash": hash})

    participants.delete_one({"hash": str(hash)})
    return details


def shell():
    while(True):
        try:
            argument = input("~$ ")
        except KeyboardInterrupt:
            print("\nbye")
            return

        broken_argument = argument.split(' ')

        if broken_argument[0].lower() in ["add", "insert"]:
            name = input("Enter the name: ")
            srn = input("Enter the SRN: ")
            phoneNumber = input("Enter the phone number: ")
            mailId = input("Enter the mailId: ")
            teamName = input("Enter the teamName: ")
            teamMembers = input("Enter the teamMembers: ")
            hash = input("Enter the hash: ")

            insert_participants_details(name = name, srn = srn, phoneNumber =  phoneNumber, mailId =  mailId, teamName =  teamName, teamMembers = teamMembers, hash = hash)

            print("done")

        elif broken_argument[0].lower() in ["fetch", "get"]:
            hash = input("Enter the hash: ")
            data = retrieve_participants_details(hash)
            if (data is None):
                print("No details for this hash")
            else:
                print(data)


        elif broken_argument[0].lower() in ["remove", "del", "delete", "purge"]:
            hash = input("Enter the hash to remove: ")
            data = delete_participants_details(hash)

            if data is None:
                print(f"Could not find a team with hash '{hash}'")
            else:
                print(f"Done\n{data}")


        elif broken_argument[0].lower() in ["drop"]:
            if len(broken_argument) > 1 and broken_argument[1].lower() != "":
                if broken_argument[1].lower() in db.list_collection_names():

                    while(True):
                        final_check = input(f"Are you sure you want to drop the table '{broken_argument[1].lower()}'?: ")
                        if final_check.lower() in ["y", "yes"]:
                            db[broken_argument[1].lower()].drop()
                            print(f"'{broken_argument[1].lower()}' table has been dropped")
                            break

                        elif final_check.lower() in ["n", "no"]:
                            print("Table has not been dropped")
                            break
                        else:
                            print("Please enter y or n")

                else:
                    print(f"The table '{broken_argument[1].lower()}' does not exist")
            else:
                table_to_delete = input("Enter the name of the table to drop: ")
                if table_to_delete.lower() in db.list_collection_names():
                    while(True):
                        final_check = input(f"Are you sure you want to drop the table '{table_to_delete.lower()}'?: ")
                        if final_check.lower() in ["y", "yes"]:
                            db[table_to_delete.lower()].drop()
                            print(f"'{table_to_delete.lower()}' table has been dropped")
                            break

                        elif final_check.lower() in ["n", "no"]:
                            print("Table has not been dropped")
                            break
                        else:
                            print("Please enter y or n")
                else:
                    print(f"table '{table_to_delete}' doesnt exist")


        elif broken_argument[0].lower() == 'exit':
            print("bye")
            return

        elif (broken_argument[0].lower() == "check"):

            if len(broken_argument) > 1 and broken_argument[1].lower() != "":
                if broken_argument[1].lower() in db.list_collection_names():
                    print(f"'{broken_argument[1].lower()}' table exists")
                else:
                    print(f"'{broken_argument[1].lower()}' table doesnt exists")
            
            else:
                table_input = input("Enter the table name to check ('Enter' to print all the tables): ")
                if table_input.strip() == "":
                    print("The table name(s) are:")
                    for table in db.list_collection_names():
                        print(table)
                else:
                    if table_input in db.list_collection_names():
                        print(f"'{table_input}' table exists")
                    else:
                        print(f"'{table_input}' table doesnt exist")

        elif (broken_argument[0].lower() in ["clear", "cls"]):
            if os.name == 'nt':
                os.system("cls")
            else:
                os.system("clear")
            print("Database shell")

        elif (broken_argument[0].lower() in ["ls", "la"]):
            if os.name == 'nt':
                os.system("dir")
            else:
                os.system("ls -la")


        else:
            print(f"'{broken_argument[0]}': command not found")


if __name__ == "__main__": 
    print("Shell created")
    shell()
