#!/usr/bin/env python3
"""
User Management Script for CapGenie
Run this script to add, remove, or list users.
"""

import sys
import getpass
from werkzeug.security import generate_password_hash
from auth import USERS, add_user

def list_users():
    """List all current users"""
    print("\n=== Current Users ===")
    for username, user in USERS.items():
        print(f"Username: {username}")
    print(f"Total users: {len(USERS)}")

def add_new_user():
    """Add a new user"""
    print("\n=== Add New User ===")
    username = input("Enter username: ").strip()
    
    if username in USERS:
        print(f"Error: User '{username}' already exists!")
        return
    
    password = getpass.getpass("Enter password: ")
    confirm_password = getpass.getpass("Confirm password: ")
    
    if password != confirm_password:
        print("Error: Passwords don't match!")
        return
    
    if len(password) < 6:
        print("Error: Password must be at least 6 characters long!")
        return
    
    # Add user to the auth module
    if add_user(username, password):
        print(f"Success: User '{username}' added successfully!")
    else:
        print("Error: Failed to add user!")

def change_password():
    """Change a user's password"""
    print("\n=== Change Password ===")
    username = input("Enter username: ").strip()
    
    if username not in USERS:
        print(f"Error: User '{username}' not found!")
        return
    
    password = getpass.getpass("Enter new password: ")
    confirm_password = getpass.getpass("Confirm new password: ")
    
    if password != confirm_password:
        print("Error: Passwords don't match!")
        return
    
    if len(password) < 6:
        print("Error: Password must be at least 6 characters long!")
        return
    
    # Update the user's password
    USERS[username].password_hash = generate_password_hash(password)
    print(f"Success: Password for '{username}' updated successfully!")

def main():
    """Main menu"""
    while True:
        print("\n" + "="*50)
        print("CapGenie User Management")
        print("="*50)
        print("1. List users")
        print("2. Add new user")
        print("3. Change password")
        print("4. Exit")
        print("-"*50)
        
        choice = input("Enter your choice (1-4): ").strip()
        
        if choice == '1':
            list_users()
        elif choice == '2':
            add_new_user()
        elif choice == '3':
            change_password()
        elif choice == '4':
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == '__main__':
    main() 