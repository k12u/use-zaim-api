#!/usr/bin/env python3
"""
Zaim API Client Usage Example
"""

from zaim_client import ZaimClient
from datetime import datetime, date
import json


def main():
    try:
        # Initialize client (uses environment variables)
        client = ZaimClient()
        
        # Verify authentication
        print("=== User Verification ===")
        user_info = client.verify_user()
        print(f"User: {user_info['me']['name']}")
        print(f"Input count: {user_info['me']['input_count']}")
        print()
        
        # Get categories, genres, accounts
        print("=== Getting Master Data ===")
        categories = client.get_categories()
        genres = client.get_genres()
        accounts = client.get_accounts()
        
        print(f"Categories: {len(categories['categories'])}")
        print(f"Genres: {len(genres['genres'])}")
        print(f"Accounts: {len(accounts['accounts'])}")
        print()
        
        # Example: Create a payment (lunch expense)
        print("=== Creating Payment Record ===")
        today = date.today().strftime('%Y-%m-%d')
        
        # Find food category and lunch genre (adjust IDs based on your data)
        food_categories = [c for c in categories['categories'] if 'food' in c['name'].lower()]
        if food_categories:
            category_id = food_categories[0]['id']
            
            # Find related genre
            related_genres = [g for g in genres['genres'] if g['category_id'] == category_id]
            if related_genres:
                genre_id = related_genres[0]['id']
                
                # Create payment
                payment = client.create_payment(
                    category_id=category_id,
                    genre_id=genre_id,
                    amount=800,
                    date=today,
                    comment="Lunch at office",
                    name="Lunch set",
                    place="Restaurant ABC"
                )
                print(f"Created payment with ID: {payment['money']['id']}")
                print()
        
        # Get recent money records
        print("=== Recent Money Records ===")
        money_records = client.get_money(limit=5)
        for record in money_records['money']:
            print(f"{record['date']} - {record['mode']}: {record['amount']} JPY - {record.get('comment', 'No comment')}")
        print()
        
        # Example: Create income record
        print("=== Creating Income Record ===")
        income_categories = [c for c in categories['categories'] if c['mode'] == 'income']
        if income_categories:
            income = client.create_income(
                category_id=income_categories[0]['id'],
                amount=5000,
                date=today,
                comment="Bonus payment"
            )
            print(f"Created income with ID: {income['money']['id']}")
            print()
        
        # Example: Create transfer between accounts
        if len(accounts['accounts']) >= 2:
            print("=== Creating Transfer Record ===")
            transfer = client.create_transfer(
                amount=10000,
                date=today,
                from_account_id=accounts['accounts'][0]['id'],
                to_account_id=accounts['accounts'][1]['id'],
                comment="Monthly savings"
            )
            print(f"Created transfer with ID: {transfer['money']['id']}")
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()