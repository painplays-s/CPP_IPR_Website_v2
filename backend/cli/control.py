#!/usr/bin/env python3
# backend/cli/control.py

import argparse
import sys
import os
import datetime
from getpass import getpass

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import get_db
from utils.password_utils import hash_password

class UserManager:
    def __init__(self):
        self.conn = get_db()
    
    def close(self):
        self.conn.close()
    
    def list_users(self):
        """List all users"""
        users = self.conn.execute(
            "SELECT id, username, created_at, last_login, is_active FROM user ORDER BY id"
        ).fetchall()
        
        if not users:
            print("No users found.")
            return
        
        print("\nID  Username             Status      Created                Last Login")
        print("-" * 70)
        for user in users:
            status = "Active" if user['is_active'] else "Inactive"
            last_login = user['last_login'] or "Never"
            print(f"{user['id']:<3} {user['username']:<20} {status:<10} {user['created_at'][:19]}  {last_login[:19] if last_login != 'Never' else last_login}")
        print()
    
    def add_user(self, username, password=None, is_active=True):
        """Add a new user"""
        try:
            # Check if username exists
            existing = self.conn.execute(
                "SELECT id FROM user WHERE username = ?", (username,)
            ).fetchone()
            
            if existing:
                print(f"Error: Username '{username}' already exists.")
                return False
            
            # Get password if not provided
            if not password:
                password = getpass("Enter password: ")
                confirm = getpass("Confirm password: ")
                if password != confirm:
                    print("Error: Passwords do not match.")
                    return False
                if not password:
                    print("Error: Password cannot be empty.")
                    return False
            
            hashed_password = hash_password(password)
            
            self.conn.execute(
                "INSERT INTO user (username, password, created_at, is_active) VALUES (?, ?, ?, ?)",
                (username, hashed_password, datetime.datetime.now().isoformat(), 1 if is_active else 0)
            )
            self.conn.commit()
            print(f"User '{username}' created successfully.")
            return True
            
        except Exception as e:
            print(f"Error creating user: {e}")
            return False
    
    def update_user(self, user_id, username=None, password=None, is_active=None):
        """Update user details"""
        try:
            user = self.conn.execute("SELECT * FROM user WHERE id = ?", (user_id,)).fetchone()
            
            if not user:
                print(f"Error: User with ID {user_id} not found.")
                return False
            
            updates = []
            params = []
            
            if username and username != user['username']:
                existing = self.conn.execute(
                    "SELECT id FROM user WHERE username = ? AND id != ?", (username, user_id)
                ).fetchone()
                
                if existing:
                    print(f"Error: Username '{username}' already exists.")
                    return False
                
                updates.append("username = ?")
                params.append(username)
            
            if password:
                updates.append("password = ?")
                params.append(hash_password(password))
            
            if is_active is not None:
                updates.append("is_active = ?")
                params.append(1 if is_active else 0)
            
            if not updates:
                print("No changes specified.")
                return False
            
            params.append(user_id)
            self.conn.execute(f"UPDATE user SET {', '.join(updates)} WHERE id = ?", params)
            self.conn.commit()
            
            print(f"User ID {user_id} updated successfully.")
            return True
            
        except Exception as e:
            print(f"Error updating user: {e}")
            return False
    
    def delete_user(self, user_id):
        """Delete a user"""
        try:
            user = self.conn.execute("SELECT username FROM user WHERE id = ?", (user_id,)).fetchone()
            
            if not user:
                print(f"Error: User with ID {user_id} not found.")
                return False
            
            confirm = input(f"Delete user '{user['username']}'? (yes/no): ")
            if confirm.lower() != 'yes':
                print("Deletion cancelled.")
                return False
            
            self.conn.execute("DELETE FROM user WHERE id = ?", (user_id,))
            self.conn.commit()
            print(f"User '{user['username']}' deleted successfully.")
            return True
            
        except Exception as e:
            print(f"Error deleting user: {e}")
            return False
    
    def reset_password(self, user_id):
        """Reset user password"""
        print("Enter new password:")
        new_pass = getpass()
        confirm = getpass("Confirm new password: ")
        
        if new_pass != confirm:
            print("Error: Passwords do not match.")
            return False
        
        return self.update_user(user_id, password=new_pass)
    
    def toggle_status(self, user_id):
        """Toggle user active status"""
        user = self.conn.execute("SELECT is_active FROM user WHERE id = ?", (user_id,)).fetchone()
        
        if not user:
            print(f"Error: User with ID {user_id} not found.")
            return False
        
        new_status = not user['is_active']
        return self.update_user(user_id, is_active=new_status)

def main():
    parser = argparse.ArgumentParser(description="User Control Panel")
    parser.add_argument('command', nargs='?', default='help',
                       choices=['list', 'add', 'update', 'delete', 'resetpass', 'toggle', 'help'],
                       help="Command to execute")
    parser.add_argument('--id', type=int, help="User ID")
    parser.add_argument('--name', help="Username")
    parser.add_argument('--pass', dest='password', help="Password")
    parser.add_argument('--active', choices=['yes', 'no'], help="Set active status")
    
    args = parser.parse_args()
    
    if args.command == 'help' or len(sys.argv) == 1:
        print("""
╔══════════════════════════════════════════════════════════╗
║                    USER CONTROL PANEL                    ║
╚══════════════════════════════════════════════════════════╝

COMMANDS:
  list                 Show all users
  add --name NAME      Create new user
  update --id ID       Update user (use --name, --active)
  delete --id ID       Delete user
  resetpass --id ID    Reset password
  toggle --id ID       Enable/disable user
  help                 Show this help

EXAMPLES:
  python control.py list
  python control.py add --name john
  python control.py update --id 2 --active no
  python control.py delete --id 3
  python control.py resetpass --id 2
  python control.py toggle --id 1
        """)
        return
    
    manager = UserManager()
    
    try:
        if args.command == 'list':
            manager.list_users()
        
        elif args.command == 'add':
            if not args.name:
                print("Error: --name required")
                return
            active = args.active == 'yes' if args.active else True
            manager.add_user(args.name, args.password, active)
        
        elif args.command == 'update':
            if not args.id:
                print("Error: --id required")
                return
            active = None if not args.active else (args.active == 'yes')
            manager.update_user(args.id, args.name, args.password, active)
        
        elif args.command == 'delete':
            if not args.id:
                print("Error: --id required")
                return
            manager.delete_user(args.id)
        
        elif args.command == 'resetpass':
            if not args.id:
                print("Error: --id required")
                return
            manager.reset_password(args.id)
        
        elif args.command == 'toggle':
            if not args.id:
                print("Error: --id required")
                return
            manager.toggle_status(args.id)
    
    finally:
        manager.close()

if __name__ == "__main__":
    main()