
import pymongo
from pymongo import MongoClient
import os
import certifi
import hashlib
import secrets

from getpass import getpass


class DatabaseIntegration():
	ca = certifi.where()
	mongodbclient_token = os.getenv("DATABASE_CLIENT_URL")
	initialized = False
	db = None
	events = None
	participants = None
	admins = None
	analytics = None

	def __init__(self):

		if DatabaseIntegration.initialized is False:
			DatabaseIntegration.initialized = True
		else:
			return

		if self.mongodbclient_token is None:
			try:
				with open('./mongodbclient.0', 'r', encoding='utf-8') as client_url:
					print("Using MongoDB cluster url provided in file")
					cluster = MongoClient(client_url.read(), tlsCAFile=self.ca)
			except FileNotFoundError:
				print("File not found [mongodbclient.0]")
				print("Neither environment variable nor client file exist")
				print("Abort")
				exit()
		else:
			print("Using MongoDB cluster url provided in environment variable..")
			cluster = MongoClient(self.mongodbclient_token, tlsCAFile=self.ca)


		DatabaseIntegration.db = cluster["ticket_scanner"]
		DatabaseIntegration.admins = DatabaseIntegration.db["admins"]
		DatabaseIntegration.events = DatabaseIntegration.db["events"]
		DatabaseIntegration.participants = DatabaseIntegration.db["registrations"]
		DatabaseIntegration.analytics = DatabaseIntegration.db["analytics"]

		print("Database connection has been established\n")


	# ---------------------------------------------------- User authentication --------------------------------------------------------

	def signup_admin(self, username, password, role = None):
		details = None
		details = self.admins.find_one({"username": username})

		token = secrets.token_urlsafe(32)

		if details is not None:
			return -1

		if role is None:
			role = "mod"

		results = self.admins.insert_one({"username": username, "password": password, "role": role, "api_key": token})


	def signin_admin(self, username, password):
		details = None
		details = self.admins.find_one({"username": username, "password": password})

		data = {}

		if details is not None:
			data["status"] = True
			data["api_key"] = details["api_key"]
		else:
			data["status"] = False

		return data

	def change_admin_password(self, username, password, new_password):
		details = None
		details = self.admins.find_one({"username": username, "password": password})

		if details is not None:
			results = self.admins.update_one({"username": username}, {"$set": {"password": new_password}})
			return True
		else:
			return False

	def check_username(self, username):
		details = None
		details = self.admins.find_one({"username": username})

		return details

	def is_valid_api_key(self, key):
		details = None
		details = self.admins.find({})

		api_token_list = []

		data = {}

		for element in details:
			if key == element["api_key"]:
				data["status"] = True
				return data

		data["status"] = False	

		return data




	# ---------------------------------------------------- event data -----------------------------------------------------------------


	def insert_event_details(self, event_name, event_date, event_time, event_duration, event_venue):
		
		details = None
		event_name = str(event_name)
		event_date_encoded = str(event_date).replace("/","")
		event_name = event_name.replace(" ", "_")
		details = self.events.find_one({"unique_event_name": f"{event_name}_{event_date_encoded}"})

		if details is not None:
			self.events.delete_one({"unique_event_name": f"{event_name}_{event_date}"})

		results = self.events.insert_one({"event_name": event_name, "event_date": str(event_date), "event_time": str(event_time), "event_duration": str(event_duration), "event_venue": str(event_venue), "unique_event_name": f"{event_name}_{event_date_encoded}"})

	def retrieve_event_details(self, unique_event_name):

		details = None
		details = self.events.find_one({"unique_event_name": unique_event_name})

		if details is not None:
			details.pop("_id")

		return details


	def purge_event(self, unique_event_name):

		details = None
		details = self.events.find_one({"unique_event_name": unique_event_name})

		if details is not None:
			self.events.delete_one({"unique_event_name": unique_event_name})
			self.participants.delete_many({"unique_event_name": unique_event_name})
			self.analytics.delete_many({"unique_event_name": unique_event_name})


	# ---------------------------------------------------- particpant data -------------------------------------------------------------


	def insert_participants_details(self, srn, name, phoneNumber, mailId, hash, unique_event_name, teamName = None, teamMembers = None):
		
		details = None
		details = self.participants.find_one({"hash": str(hash), "unique_event_name": str(unique_event_name)})

		if details is not None:
			self.participants.delete_one({"hash": str(hash), "unique_event_name": str(unique_event_name)})

		results = self.participants.insert_one({"name": str(name), "srn": str(srn), "phoneNumber": str(phoneNumber), "mailId": str(mailId), "teamName": str(teamName), "teamMembers": str(teamMembers), "hash": str(hash), "unique_event_name": str(unique_event_name)})


	def retrieve_participants_details(self, hash):
		
		details = None
		details = self.participants.find_one({"hash": str(hash)})
		if details is not None:
			details.pop("_id")
		return details

	def delete_participants_details(self, hash):

		details = None
		details = self.participants.find_one({"hash": hash})

		self.participants.delete_one({"hash": str(hash)})
		return details

	def drop_table(self, table_name):
		if table_name.lower() in self.db.list_collection_names():
			self.db[table_name].drop()
			print("Table has been dropped")
		else:
			print(f"Invalid name to table '{table_name}': No such table exists")

	
	def number_of_participants(self, unique_event_name):

		details = None
		details = self.participants.find({"unique_event_name": unique_event_name})
		count = 0
		if details is not None:
			for element in details:
				count += 1

		return count

	# ---------------------------------------------------- event analytics -------------------------------------------------------------

	def insert_analytics_data(self, registration_details):

		self.analytics.insert_one(registration_details)

	def retrieve_analytics_data(self, unique_event_name):

		details = None
		details = self.analytics.find({"unique_event_name": unique_event_name})

		list = []

		for detail in details:
			detail.pop("_id")
			list.append(detail)

		results = {}
		results["data"] = list

		return results




	# ---------------------------------------------------- Database shell --------------------------------------------------------------

	def shell(self):
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

				self.insert_participants_details(name = name, srn = srn, phoneNumber =  phoneNumber, mailId =  mailId, teamName =  teamName, teamMembers = teamMembers, hash = hash)

				print("done")

			elif broken_argument[0].lower() in ["fetch", "get"]:
				if len(broken_argument) > 1 and broken_argument[1].lower() != "":
					hash = broken_argument[1].lower()
				else:
					hash = input("Enter the hash: ")

				data = self.retrieve_participants_details(hash)
				if (data is None):
					print(f"No details for hash {hash}")
				else:
					print(data)


			elif broken_argument[0].lower() in ["remove", "del", "delete", "purge"]:

				if broken_argument[1].lower() in ["event"] and len(broken_argument) > 1:
					unique_event_name = input("Enter the unique event name: ")
					data = self.retrieve_event_details(unique_event_name)
					if data is not None:
						name = data["event_name"]
						choice = input(f"Are you sure you sure you want to delete '{name}'?: ")
						if choice.lower() in ["y", "yes"]:
							self.purge_event(unique_event_name)
							print(f"Event '{name}' has been removed")
						else:
							print("Enter either y or n")
					else:
						print(f"No event with the name '{unique_event_name}'")				
				else:
					hash = input("Enter the hash to remove: ")
					data = self.delete_participants_details(hash)

					if data is None:
						print(f"Could not find a team with hash '{hash}'")
					else:
						print(f"Done\n{data}")


			elif broken_argument[0].lower() in ["drop"]:
				if len(broken_argument) > 1 and broken_argument[1].lower() != "":
					table_to_delete = broken_argument[1].lower()
				else:
					table_to_delete = input("Enter the name of the table to drop: ")
					
				if table_to_delete.lower() in self.db.list_collection_names():
					while(True):
						final_check = input(f"Are you sure you want to drop the table '{table_to_delete.lower()}'?: ")
						if final_check.lower() in ["y", "yes"]:
							self.db[table_to_delete.lower()].drop()
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
					if broken_argument[1].lower() in self.db.list_collection_names():
						print(f"'{broken_argument[1].lower()}' table exists")
					else:
						print(f"'{broken_argument[1].lower()}' table doesnt exists")
				
				else:
					table_input = input("Enter the table name to check ('Enter' to print all the tables): ")
					if table_input.strip() == "":
						print("The table name(s) are:")
						for table in self.db.list_collection_names():
							print(table)
					else:
						if table_input in self.db.list_collection_names():
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

			elif (broken_argument[0].lower() in ["signup"]):
				username = input("Enter username: ")
				check = self.check_username(username)
				if check is not None:
					print("Username already exists")
					break
				password1 = getpass("Enter password: ")
				password2 = getpass("Enter password again for verification: ")
				if password1 != password2:
					print("Passwords dont match. try again.")
					break
				else:
					role = input("Enter role(admin, mod): ")
					if role.lower() == "admin":
						role = "admin"
					elif role.lower() == "mod":
						role = "mod"
					else:
						print("Invalid role entered. Try again.")
						break
					password = hashlib.sha256(password1.encode('utf-8')).hexdigest()
					self.signup_admin(username, password, role)
					print(f"Signup for admin '{username}' with role '{role}' has been completed")


			elif (broken_argument[0].lower() in ["signin"]):
				username = input("Enter username to login: ")
				check = self.check_username(username)
				if check is None:
					print("User does not exist")
					break

				password = getpass("Enter password: ")
				password = hashlib.sha256(password.encode('utf-8')).hexdigest()
				if self.signin_admin(username, password):
					print("User login successful")
				else:
					print("User login failed")

			elif len(broken_argument) > 1 and broken_argument[0].lower() in ["change"] and broken_argument[1].lower() in ["password", "pass"]:
				username = input("Enter username: ")
				password = getpass("Enter previous password: ")
				password = hashlib.sha256(password.encode('utf-8')).hexdigest()
				if self.signin_admin(username, password):
					new_password1 = getpass("Enter your new password: ")
					new_password2 = getpass("Enter your new password for verification: ")
					if new_password1 == new_password2:
						new_password = hashlib.sha256(new_password1.encode('utf-8')).hexdigest()
						self.change_admin_password(username, password, new_password)
						print(f"Password of user '{username}' has been changed successfully")
					else:
						print("Passwords do not match. Please try again.")
				else:
					print("Invalid password entered. Please try again.")



			else:
				string = " ".join(broken_arguments for broken_arguments in broken_argument)
				print(f"'{string}': command not found")


if __name__ == "__main__": 
	db = DatabaseIntegration()

	print("Shell created")
	db.shell()
