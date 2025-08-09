#!/usr/bin/env python3
"""
OAuth認証フローのテスト（Step1のみ）
"""

import os
from oauth_helper import ZaimOAuthHelper


def test_request_token():
    """リクエストトークン取得のテスト"""
    print("=== OAuth Step 1 テスト ===")
    
    try:
        helper = ZaimOAuthHelper()
        
        # Step 1: リクエストトークン取得
        oauth_token, oauth_token_secret = helper.get_request_token()
        
        print(f"\n✅ テスト成功!")
        print(f"Request Token: {oauth_token}")
        print(f"Request Token Secret: {oauth_token_secret[:20]}...")
        
        # Step 2: 認証URLも生成（ブラウザは開かない）
        auth_url = helper.get_authorization_url(oauth_token)
        print(f"\n認証URL（手動でアクセス）:")
        print(auth_url)
        
        print(f"\n🎉 OAuth Step 1 (リクエストトークン取得) は正常に動作しています!")
        print(f"実際の認証を行うには、以下のコマンドを対話的に実行してください:")
        print(f"python oauth_helper.py")
        
        return True
        
    except Exception as e:
        print(f"❌ テスト失敗: {e}")
        return False


if __name__ == "__main__":
    test_request_token()