#!/usr/bin/env python3
"""
認証テストスクリプト
"""

import os
import sys
from zaim_client import ZaimClient


def test_successful_auth():
    """正常認証テスト"""
    print("=== 正常認証テスト ===")
    try:
        client = ZaimClient()
        user_info = client.verify_user()
        
        # レスポンス構造の確認
        assert 'me' in user_info
        assert 'id' in user_info['me']
        assert 'name' in user_info['me']
        assert 'input_count' in user_info['me']
        
        print(f"✅ 認証成功: ユーザー名 = {user_info['me']['name']}")
        print(f"   ユーザーID = {user_info['me']['id']}")
        print(f"   入力回数 = {user_info['me']['input_count']}")
        return True
        
    except Exception as e:
        print(f"❌ 認証テストエラー: {e}")
        return False


def test_invalid_credentials():
    """認証情報不正テスト"""
    print("\n=== 認証情報不正テスト ===")
    try:
        # 不正な認証情報でクライアントを作成
        client = ZaimClient(
            consumer_key="invalid_key",
            consumer_secret="invalid_secret", 
            access_token="invalid_token",
            access_token_secret="invalid_token_secret"
        )
        
        try:
            user_info = client.verify_user()
            print("❌ 不正な認証情報で認証が成功してしまいました")
            return False
        except Exception as e:
            print(f"✅ 期待通り認証エラーが発生: {str(e)[:100]}...")
            return True
            
    except Exception as e:
        print(f"❌ テスト実行エラー: {e}")
        return False


def test_missing_credentials():
    """認証情報未設定テスト"""
    print("\n=== 認証情報未設定テスト ===")
    try:
        # 環境変数を一時的にクリア
        original_env = {}
        env_vars = ['ZAIM_CONSUMER_KEY', 'ZAIM_CONSUMER_SECRET', 
                    'ZAIM_ACCESS_TOKEN', 'ZAIM_ACCESS_TOKEN_SECRET']
        
        for var in env_vars:
            original_env[var] = os.environ.get(var)
            if var in os.environ:
                del os.environ[var]
        
        try:
            # 認証情報なしでクライアント作成を試行
            client = ZaimClient()
            print("❌ 認証情報なしでクライアントが作成されてしまいました")
            return False
            
        except ValueError as e:
            if "OAuth credentials are required" in str(e):
                print("✅ 期待通りValueErrorが発生")
                return True
            else:
                print(f"❌ 予期しないValueError: {e}")
                return False
                
        except Exception as e:
            print(f"❌ 予期しないエラー: {e}")
            return False
            
        finally:
            # 環境変数を復元
            for var, value in original_env.items():
                if value is not None:
                    os.environ[var] = value
                    
    except Exception as e:
        print(f"❌ テスト実行エラー: {e}")
        return False


def test_constructor_parameters():
    """コンストラクタパラメータ指定テスト"""
    print("\n=== コンストラクタパラメータ指定テスト ===")
    try:
        # 環境変数から認証情報を取得
        consumer_key = os.getenv('ZAIM_CONSUMER_KEY')
        consumer_secret = os.getenv('ZAIM_CONSUMER_SECRET')
        access_token = os.getenv('ZAIM_ACCESS_TOKEN')
        access_token_secret = os.getenv('ZAIM_ACCESS_TOKEN_SECRET')
        
        if not all([consumer_key, consumer_secret, access_token, access_token_secret]):
            print("⚠️ 環境変数が設定されていないため、このテストをスキップします")
            return True
        
        # コンストラクタで直接指定
        client = ZaimClient(
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            access_token=access_token,
            access_token_secret=access_token_secret
        )
        
        user_info = client.verify_user()
        print(f"✅ コンストラクタパラメータでの認証成功: {user_info['me']['name']}")
        return True
        
    except Exception as e:
        print(f"❌ コンストラクタパラメータテストエラー: {e}")
        return False


def main():
    """認証テストの実行"""
    print("Zaim API Client - 認証テスト")
    print("=" * 50)
    
    tests = [
        test_successful_auth,
        test_invalid_credentials,
        test_missing_credentials,
        test_constructor_parameters
    ]
    
    results = []
    for test in tests:
        result = test()
        results.append(result)
    
    print("\n" + "=" * 50)
    print("テスト結果サマリー:")
    
    passed = sum(results)
    total = len(results)
    
    for i, (test, result) in enumerate(zip(tests, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{i+1}. {test.__name__}: {status}")
    
    print(f"\n合計: {passed}/{total} テスト通過")
    
    if passed == total:
        print("🎉 すべての認証テストが成功しました！")
        return 0
    else:
        print("⚠️ 一部のテストが失敗しました。")
        return 1


if __name__ == "__main__":
    sys.exit(main())