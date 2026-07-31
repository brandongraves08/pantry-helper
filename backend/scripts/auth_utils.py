#!/usr/bin/env python3
"""
Device authentication utility

Usage:
  python auth_utils.py hash-token <token>
  python auth_utils.py generate-token
"""

import argparse
import hashlib
import secrets

def hash_token(token: str) -> str:
    """Hash a device token using SHA256"""
    return hashlib.sha256(token.encode()).hexdigest()

def generate_token() -> str:
    """Generate a random secure token"""
    return secrets.token_urlsafe(32)

def main():
    parser = argparse.ArgumentParser(description="Device authentication utilities")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Hash token command
    hash_parser = subparsers.add_parser("hash-token", help="Hash a device token")
    hash_parser.add_argument("token", help="Token to hash")
    
    # Generate token command
    subparsers.add_parser("generate-token", help="Generate a new random token")
    
    args = parser.parse_args()
    
    if args.command == "hash-token":
        hashed = hash_token(args.token)
        print(f"Token: {args.token}")
        print(f"Hash:  {hashed}")
    elif args.command == "generate-token":
        token = generate_token()
        print(f"New token: {token}")
        print(f"Hash:      {hash_token(token)}")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
