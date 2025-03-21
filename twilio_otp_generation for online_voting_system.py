import hashlib
import random
import datetime
import json
import os
import tkinter as tk
from tkinter import messagebox, ttk
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

account_sid = 'ACadd6db7d880ebb27ba837730399d4fd8'
auth_token = 'a3ef4dff66698ca74889fbe54b8fc908'
twilio_phone_number = '+15173652563'

client = Client(account_sid, auth_token)

class Voter:
    def __init__(self, voter_id, name, dob, phone, has_voted=False):
        self.voter_id = voter_id
        self.name = name
        self.dob = dob
        self.phone = phone
        self.has_voted = has_voted

    def generate_otp(self):
        return random.randint(1000, 9999)

    def to_dict(self):
        return {
            "voter_id": self.voter_id,
            "name": self.name,
            "dob": self.dob,
            "phone": self.phone,
            "has_voted": self.has_voted
        }

class Candidate:
    def __init__(self, name, party, votes=0):
        self.name = name
        self.party = party
        self.votes = votes

    def add_vote(self):
        self.votes += 1

    def to_dict(self):
        return {
            "name": self.name,
            "party": self.party,
            "votes": self.votes
        }

class VotingSystem:
    def __init__(self):
        self.voters = {}
        self.candidates = {}
        self.vote_chain = []
        self.admin_credentials = {"admin": "password123"}
        self.load_data()

    def calculate_age(self, dob):
        birth_year = int(dob.split('/')[2])
        current_year = datetime.datetime.now().year
        return current_year - birth_year

    def add_voter(self, voter_id, name, dob, phone):
        if len(voter_id) > 16:
            return "Voter ID cannot exceed 16 characters."
        if len(phone) != 10:
            return "Phone number must be 10 digits."
        if self.calculate_age(dob) < 18:
            return "Voter must be at least 18 years old."
        if voter_id in self.voters:
            return "Voter ID already registered."
        self.voters[voter_id] = Voter(voter_id, name, dob, phone)
        self.save_data()
        return "Voter added successfully."

    def edit_voter(self, voter_id, name, dob, phone):
        if voter_id in self.voters:
            self.voters[voter_id] = Voter(voter_id, name, dob, phone, self.voters[voter_id].has_voted)
            self.save_data()
            return "Voter edited successfully."
        return "Voter not found."

    def remove_voter(self, voter_id):
        if voter_id in self.voters:
            del self.voters[voter_id]
            self.save_data()

    def add_candidate(self, name, party):
        self.candidates[name] = Candidate(name, party)
        self.save_data()

    def edit_candidate(self, name, new_name, party):
        if name in self.candidates:
            candidate = self.candidates.pop(name)
            candidate.name = new_name
            candidate.party = party
            self.candidates[new_name] = candidate
            self.save_data()
            return "Candidate edited successfully."
        return "Candidate not found."

    def remove_candidate(self, name):
        if name in self.candidates:
            del self.candidates[name]
            self.save_data()

    def cast_vote(self, voter_id, candidate_name):
        if voter_id not in self.voters:
            return "Voter not registered."

        voter = self.voters[voter_id]
        if voter.has_voted:
            return "Vote already cast."

        if candidate_name not in self.candidates:
            return "Candidate not found."

        self.candidates[candidate_name].add_vote()
        voter.has_voted = True

        vote_hash = hashlib.sha256(f"{voter_id}{candidate_name}".encode()).hexdigest()
        self.vote_chain.append(vote_hash)
        
        self.save_data()
        return "Vote cast successfully."

    def display_results(self):
        return {name: candidate.votes for name, candidate in self.candidates.items()}

    def get_voter_info(self):
        return self.voters

    def get_candidate_info(self):
        return self.candidates

    def save_data(self):
        with open('voting_data.json', 'w') as file:
            json.dump({
                "voters": {voter_id: voter.to_dict() for voter_id, voter in self.voters.items()},
                "candidates": {name: candidate.to_dict() for name, candidate in self.candidates.items()}
            }, file)

    def load_data(self):
        if os.path.exists('voting_data.json'):
            with open('voting_data.json', 'r') as file:
                data = json.load(file)
                self.voters = {voter_id: Voter(**voter_data) for voter_id, voter_data in data["voters"].items()}
                self.candidates = {name: Candidate(name=candidate_data['name'], party=candidate_data['party'], votes=candidate_data['votes']) for name, candidate_data in data["candidates"].items()}

    def get_sorted_voter_ids(self):
        return sorted(self.voters.keys())

    def binary_search_voter(self, voter_id):
        sorted_voter_ids = self.get_sorted_voter_ids()
        left, right = 0, len(sorted_voter_ids) - 1

        while left <= right:
            mid = (left + right) // 2
            mid_voter_id = sorted_voter_ids[mid]

            if mid_voter_id == voter_id:
                return self.voters[mid_voter_id]
            elif mid_voter_id < voter_id:
                left = mid + 1
            else:
                right = mid - 1

        return None

voting_system = VotingSystem()

root = tk.Tk()
root.title("Online Voting System")
root.geometry("800x600")
root.configure(bg="#121212")

style = ttk.Style()
style.configure("TButton", foreground="cyan", background="#282828", font=("Helvetica", 12))
style.configure("TLabel", foreground="white", background="#121212", font=("Helvetica", 12))
style.configure("TFrame", background="#121212")

def admin_login():
    login_window = tk.Toplevel(root)
    login_window.title("Admin Login")
    login_window.geometry("300x200")
    login_window.configure(bg="#121212")

    tk.Label(login_window, text="Username:", bg="#121212", fg="white").pack(pady=5)
    username_entry = tk.Entry(login_window, bg="#282828", fg="white", insertbackground="white")
    username_entry.pack(pady=5)

    tk.Label(login_window, text="Password:", bg="#121212", fg="white").pack(pady=5)
    password_entry = tk.Entry(login_window, show="*", bg="#282828", fg="white", insertbackground="white")
    password_entry.pack(pady=5)

    def verify_login():
        username = username_entry.get()
        password = password_entry.get()
        if username in voting_system.admin_credentials and voting_system.admin_credentials[username] == password:
            login_window.destroy()
            open_admin_panel()
        else:
            messagebox.showerror("Error", "Invalid credentials")

    tk.Button(login_window, text="Login", command=verify_login, bg="#282828", fg="cyan").pack(pady=10)

def open_admin_panel():
    global admin_window
    admin_window = tk.Toplevel(root)
    admin_window.title("Admin Panel")
    admin_window.geometry("800x600")
    admin_window.configure(bg="#121212")

    tk.Button(admin_window, text="Add Voter", command=add_voter_window, bg="#282828", fg="cyan").pack(pady=5)
    tk.Button(admin_window, text="Edit Voter", command=initiate_edit_voter, bg="#282828", fg="cyan").pack(pady=5)
    tk.Button(admin_window, text="Delete Voter", command=delete_voter_window, bg="#282828", fg="cyan").pack(pady=5)
    tk.Button(admin_window, text="Add Candidate", command=add_candidate_window, bg="#282828", fg="cyan").pack(pady=5)
    tk.Button(admin_window, text="Edit Candidate", command=edit_candidate_window, bg="#282828", fg="cyan").pack(pady=5)
    tk.Button(admin_window, text="Delete Candidate", command=delete_candidate_window, bg="#282828", fg="cyan").pack(pady=5)
    tk.Button(admin_window, text="Voter Info", command=show_voter_info, bg="#282828", fg="cyan").pack(pady=5)
    tk.Button(admin_window, text="Candidate Info", command=show_candidate_info, bg="#282828", fg="cyan").pack(pady=5)

    tk.Button(admin_window, text="Search Voter by ID", command=open_search_voter_window, bg="#282828", fg="cyan").pack(pady=5)

def open_search_voter_window():
    search_window = tk.Toplevel(admin_window)
    search_window.title("Search Voter")
    search_window.geometry("300x200")
    search_window.configure(bg="#121212")

    tk.Label(search_window, text="Enter Voter ID:", bg="#121212", fg="white").pack(pady=5)
    search_entry = tk.Entry(search_window, bg="#282828", fg="white", insertbackground="white")
    search_entry.pack(pady=5)

    def search_voter():
        voter_id = search_entry.get()
        voter = voting_system.binary_search_voter(voter_id)
        if voter:
            messagebox.showinfo("Voter Found", f"ID: {voter.voter_id}, Name: {voter.name}")
        else:
            messagebox.showerror("Voter Not Found", "No voter found with the given ID.")

    tk.Button(search_window, text="Search", command=search_voter, bg="#282828", fg="cyan").pack(pady=10)

def show_voter_info():
    voter_info_window = tk.Toplevel(admin_window)
    voter_info_window.title("Voter Information")
    voter_info_window.geometry("600x450")
    voter_info_window.configure(bg="#121212")

    tree = ttk.Treeview(voter_info_window, columns=("Voter ID", "Name", "DOB", "Phone", "Voted"), show="headings")
    tree.heading("Voter ID", text="Voter ID")
    tree.heading("Name", text="Name")
    tree.heading("DOB", text="Date of Birth")
    tree.heading("Phone", text="Phone Number")
    tree.heading("Voted", text="Voted")

    for voter in voting_system.get_voter_info().values():
        tree.insert("", "end", values=(voter.voter_id, voter.name, voter.dob, voter.phone, voter.has_voted))

    tree.pack(fill="both", expand=True, padx=10, pady=10)

def add_voter_window():
    voter_window = tk.Toplevel(admin_window)
    voter_window.title("Add Voter")
    voter_window.geometry("400x300")
    voter_window.configure(bg="#121212")

    tk.Label(voter_window, text="Voter ID:", bg="#121212", fg="white").pack(pady=5)
    voter_id_entry = tk.Entry(voter_window, bg="#282828", fg="white", insertbackground="white")
    voter_id_entry.pack(pady=5)

    tk.Label(voter_window, text="Name:", bg="#121212", fg="white").pack(pady=5)
    name_entry = tk.Entry(voter_window, bg="#282828", fg="white", insertbackground="white")
    name_entry.pack(pady=5)

    tk.Label(voter_window, text="Date of Birth (DD/MM/YYYY):", bg="#121212", fg="white").pack(pady=5)
    dob_entry = tk.Entry(voter_window, bg="#282828", fg="white", insertbackground="white")
    dob_entry.pack(pady=5)

    tk.Label(voter_window, text="Phone Number:", bg="#121212", fg="white").pack(pady=5)
    phone_entry = tk.Entry(voter_window, bg="#282828", fg="white", insertbackground="white")
    phone_entry.pack(pady=5)

    def submit_voter():
        message = voting_system.add_voter(voter_id_entry.get(), name_entry.get(), dob_entry.get(), phone_entry.get())
        messagebox.showinfo("Add Voter", message)

    tk.Button(voter_window, text="Add Voter", command=submit_voter, bg="#282828", fg="cyan").pack(pady=10)

def initiate_edit_voter():
    edit_window = tk.Toplevel(admin_window)
    edit_window.title("Initiate Edit Voter")
    edit_window.geometry("300x200")
    edit_window.configure(bg="#121212")

    tk.Label(edit_window, text="Voter ID:", bg="#121212", fg="white").pack(pady=5)
    voter_id_entry = tk.Entry(edit_window, bg="#282828", fg="white", insertbackground="white")
    voter_id_entry.pack(pady=5)

    tk.Label(edit_window, text="Phone Number:", bg="#121212", fg="white").pack(pady=5)
    phone_entry = tk.Entry(edit_window, bg="#282828", fg="white", insertbackground="white")
    phone_entry.pack(pady=5)

    def verify_voter():
        voter_id = voter_id_entry.get()
        phone = phone_entry.get()
        if len(voter_id) > 16:
            messagebox.showerror("Error", "Voter ID cannot exceed 16 characters.")
            return
        if len(phone) != 10:
            messagebox.showerror("Error", "Phone number must be 10 digits.")
            return
        if voter_id in voting_system.voters and voting_system.voters[voter_id].phone == phone:
            if voting_system.voters[voter_id].has_voted:
                messagebox.showerror("Error", "Voter has already voted and cannot be edited.")
                return
            edit_window.destroy()
            send_otp_and_verify_edit(voter_id, phone)
        else:
            messagebox.showerror("Error", "Voter not registered or invalid phone number")

    tk.Button(edit_window, text="Verify", command=verify_voter, bg="#282828", fg="cyan").pack(pady=10)

def send_otp_and_verify_edit(voter_id, phone):
    voter = voting_system.voters[voter_id]
    otp = voter.generate_otp()
    voter.otp = otp

    formatted_phone = f'+91{phone}'

    try:
        message = client.messages.create(
            body=f'Your OTP is {otp}.',
            from_=twilio_phone_number,
            to=formatted_phone
        )
        if message.sid:
            verify_otp_for_edit(voter_id, otp)
        else:
            messagebox.showerror("Error", "Failed to send OTP")
    except TwilioRestException as e:
        messagebox.showerror("Error", f"Failed to send OTP: {e}")

def verify_otp_for_edit(voter_id, expected_otp):
    otp_window = tk.Toplevel(root)
    otp_window.title("Verify OTP")
    otp_window.geometry("300x200")
    otp_window.configure(bg="#121212")

    tk.Label(otp_window, text="Enter the OTP sent to your phone:", bg="#121212", fg="white").pack(pady=5)
    otp_entry = tk.Entry(otp_window, bg="#282828", fg="white", insertbackground="white")
    otp_entry.pack(pady=5)

    def verify_otp():
        entered_otp = otp_entry.get()
        if entered_otp == str(expected_otp):
            otp_window.destroy()
            edit_voter_details(voter_id)
        else:
            messagebox.showerror("Error", "Invalid OTP. Please try again.")

    tk.Button(otp_window, text="Verify OTP", command=verify_otp, bg="#282828", fg="cyan").pack(pady=10)

def edit_voter_details(voter_id):
    voter_window = tk.Toplevel(admin_window)
    voter_window.title("Edit Voter")
    voter_window.geometry("400x300")
    voter_window.configure(bg="#121212")

    tk.Label(voter_window, text="Name:", bg="#121212", fg="white").pack(pady=5)
    name_entry = tk.Entry(voter_window, bg="#282828", fg="white", insertbackground="white")
    name_entry.pack(pady=5)

    tk.Label(voter_window, text="Date of Birth (DD/MM/YYYY):", bg="#121212", fg="white").pack(pady=5)
    dob_entry = tk.Entry(voter_window, bg="#282828", fg="white", insertbackground="white")
    dob_entry.pack(pady=5)

    tk.Label(voter_window, text="Phone Number:", bg="#121212", fg="white").pack(pady=5)
    phone_entry = tk.Entry(voter_window, bg="#282828", fg="white", insertbackground="white")
    phone_entry.pack(pady=5)

    def submit_voter():
        message = voting_system.edit_voter(voter_id, name_entry.get(), dob_entry.get(), phone_entry.get())
        messagebox.showinfo("Edit Voter", message)

    tk.Button(voter_window, text="Edit Voter", command=submit_voter, bg="#282828", fg="cyan").pack(pady=10)

def delete_voter_window():
    voter_window = tk.Toplevel(admin_window)
    voter_window.title("Delete Voter")
    voter_window.geometry("400x150")
    voter_window.configure(bg="#121212")

    tk.Label(voter_window, text="Voter ID:", bg="#121212", fg="white").pack(pady=5)
    voter_id_entry = tk.Entry(voter_window, bg="#282828", fg="white", insertbackground="white")
    voter_id_entry.pack(pady=5)

    def submit_voter():
        voting_system.remove_voter(voter_id_entry.get())
        messagebox.showinfo("Delete Voter", "Voter deleted successfully")

    tk.Button(voter_window, text="Delete Voter", command=submit_voter, bg="#282828", fg="cyan").pack(pady=10)

def add_candidate_window():
    candidate_window = tk.Toplevel(admin_window)
    candidate_window.title("Add Candidate")
    candidate_window.geometry("400x250")
    candidate_window.configure(bg="#121212")

    tk.Label(candidate_window, text="Candidate Name:", bg="#121212", fg="white").pack(pady=5)
    name_entry = tk.Entry(candidate_window, bg="#282828", fg="white", insertbackground="white")
    name_entry.pack(pady=5)

    tk.Label(candidate_window, text="Party Name:", bg="#121212", fg="white").pack(pady=5)
    party_entry = tk.Entry(candidate_window, bg="#282828", fg="white", insertbackground="white")
    party_entry.pack(pady=5)

    def submit_candidate():
        voting_system.add_candidate(name_entry.get(), party_entry.get())
        messagebox.showinfo("Add Candidate", "Candidate added successfully")

    tk.Button(candidate_window, text="Add Candidate", command=submit_candidate, bg="#282828", fg="cyan").pack(pady=10)

def edit_candidate_window():
    candidate_window = tk.Toplevel(admin_window)
    candidate_window.title("Edit Candidate")
    candidate_window.geometry("400x250")
    candidate_window.configure(bg="#121212")

    tk.Label(candidate_window, text="Current Candidate Name:", bg="#121212", fg="white").pack(pady=5)
    name_entry = tk.Entry(candidate_window, bg="#282828", fg="white", insertbackground="white")
    name_entry.pack(pady=5)

    tk.Label(candidate_window, text="New Candidate Name:", bg="#121212", fg="white").pack(pady=5)
    new_name_entry = tk.Entry(candidate_window, bg="#282828", fg="white", insertbackground="white")
    new_name_entry.pack(pady=5)

    tk.Label(candidate_window, text="Party Name:", bg="#121212", fg="white").pack(pady=5)
    party_entry = tk.Entry(candidate_window, bg="#282828", fg="white", insertbackground="white")
    party_entry.pack(pady=5)

    def submit_candidate():
        message = voting_system.edit_candidate(name_entry.get(), new_name_entry.get(), party_entry.get())
        messagebox.showinfo("Edit Candidate", message)

    tk.Button(candidate_window, text="Edit Candidate", command=submit_candidate, bg="#282828", fg="cyan").pack(pady=10)

def delete_candidate_window():
    candidate_window = tk.Toplevel(admin_window)
    candidate_window.title("Delete Candidate")
    candidate_window.geometry("400x150")
    candidate_window.configure(bg="#121212")

    tk.Label(candidate_window, text="Candidate Name:", bg="#121212", fg="white").pack(pady=5)
    name_entry = tk.Entry(candidate_window, bg="#282828", fg="white", insertbackground="white")
    name_entry.pack(pady=5)

    def submit_candidate():
        voting_system.remove_candidate(name_entry.get())
        messagebox.showinfo("Delete Candidate", "Candidate deleted successfully")

    tk.Button(candidate_window, text="Delete Candidate", command=submit_candidate, bg="#282828", fg="cyan").pack(pady=10)

def show_candidate_info():
    candidate_info_window = tk.Toplevel(admin_window)
    candidate_info_window.title("Candidate Information")
    candidate_info_window.geometry("600x450")
    candidate_info_window.configure(bg="#121212")

    tree = ttk.Treeview(candidate_info_window, columns=("Name", "Party", "Votes"), show="headings")
    tree.heading("Name", text="Name")
    tree.heading("Party", text="Party")
    tree.heading("Votes", text="Votes")

    for candidate in voting_system.get_candidate_info().values():
        tree.insert("", "end", values=(candidate.name, candidate.party, candidate.votes))

    tree.pack(fill="both", expand=True, padx=10, pady=10)

def voter_login():
    login_window = tk.Toplevel(root)
    login_window.title("Voter Login")
    login_window.geometry("300x200")
    login_window.configure(bg="#121212")

    tk.Label(login_window, text="Voter ID:", bg="#121212", fg="white").pack(pady=5)
    voter_id_entry = tk.Entry(login_window, bg="#282828", fg="white", insertbackground="white")
    voter_id_entry.pack(pady=5)

    tk.Label(login_window, text="Phone Number:", bg="#121212", fg="white").pack(pady=5)
    phone_entry = tk.Entry(login_window, bg="#282828", fg="white", insertbackground="white")
    phone_entry.pack(pady=5)

    def verify_voter():
        voter_id = voter_id_entry.get()
        phone = phone_entry.get()
        if len(voter_id) > 16:
            messagebox.showerror("Error", "Voter ID cannot exceed 16 characters.")
            return
        if len(phone) != 10:
            messagebox.showerror("Error", "Phone number must be 10 digits.")
            return
        if voter_id in voting_system.voters and voting_system.voters[voter_id].phone == phone:
            if voting_system.voters[voter_id].has_voted:
                messagebox.showerror("Error", "Voter has already voted.")
                return
            login_window.destroy()
            send_otp_and_verify(voter_id, phone)
        else:
            messagebox.showerror("Error", "Voter not registered or invalid phone number")

    tk.Button(login_window, text="Login", command=verify_voter, bg="#282828", fg="cyan").pack(pady=10)

def send_otp_and_verify(voter_id, phone):
    voter = voting_system.voters[voter_id]
    otp = voter.generate_otp()
    voter.otp = otp 

    formatted_phone = f'+91{phone}'

    try:
        message = client.messages.create(
            body=f'Your OTP is {otp}.',
            from_=twilio_phone_number,
            to=formatted_phone
        )
        if message.sid:
            verify_otp_window(voter_id, otp)
        else:
            messagebox.showerror("Error", "Failed to send OTP")
    except TwilioRestException as e:
        messagebox.showerror("Error", f"Failed to send OTP: {e}")

def verify_otp_window(voter_id, expected_otp):
    otp_window = tk.Toplevel(root)
    otp_window.title("Verify OTP")
    otp_window.geometry("300x200")
    otp_window.configure(bg="#121212")

    tk.Label(otp_window, text="Enter the OTP sent to your phone:", bg="#121212", fg="white").pack(pady=5)
    otp_entry = tk.Entry(otp_window, bg="#282828", fg="white", insertbackground="white")
    otp_entry.pack(pady=5)

    def verify_otp():
        entered_otp = otp_entry.get()
        if entered_otp == str(expected_otp):
            otp_window.destroy()
            select_candidate_and_vote(voter_id)
        else:
            messagebox.showerror("Error", "Invalid OTP. Please try again.")

    tk.Button(otp_window, text="Verify OTP", command=verify_otp, bg="#282828", fg="cyan").pack(pady=10)

def select_candidate_and_vote(voter_id):
    vote_window = tk.Toplevel(root)
    vote_window.title("Cast Vote")
    vote_window.geometry("400x300")
    vote_window.configure(bg="#121212")

    voter = voting_system.voters[voter_id]

    tk.Label(vote_window, text=f"Welcome {voter.name}! Please select a candidate to vote for:", bg="#121212", fg="white").pack(pady=5)

    candidate_var = tk.StringVar(value="Select Candidate")

    voting_system.load_data()  # Reload candidate data
    candidate_menu = tk.OptionMenu(vote_window, candidate_var, *voting_system.candidates.keys())
    candidate_menu.config(bg="#282828", fg="cyan")
    candidate_menu["menu"].config(bg="#282828", fg="cyan")
    candidate_menu.pack(pady=10)

    def submit_vote():
        candidate_name = candidate_var.get()
        message = voting_system.cast_vote(voter_id, candidate_name)
        messagebox.showinfo("Cast Vote", message)
        vote_window.destroy()
        update_results()

    tk.Button(vote_window, text="Submit Vote", command=submit_vote, bg="#282828", fg="cyan").pack(pady=10)

def update_results():
    voting_system.load_data()  # Reload data from JSON
    results = voting_system.display_results()
    results_text = "\n".join([f"{name}: {votes}" for name, votes in results.items()])
    results_label.config(text=f"Real-time Results:\n{results_text}", bg="#121212", fg="white")

tk.Button(root, text="Admin Login", command=admin_login, bg="#282828", fg="cyan").pack(pady=10)
tk.Button(root, text="Voter Login", command=voter_login, bg="#282828", fg="cyan").pack(pady=10)

results_label = tk.Label(root, text="Real-time Results:", bg="#121212", fg="white")
results_label.pack(pady=10)

root.mainloop()
