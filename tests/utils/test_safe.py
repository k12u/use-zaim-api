#!/usr/bin/env python3
"""
CRUD操作テストスクリプト（安全版）
crypto_accountアカウントを使用してテストを実行
"""

import sys
import time
from datetime import date, datetime, timedelta
from zaim_client import ZaimClient


class SafeTestData:
    """安全なテスト用データの保持"""
    def __init__(self):
        self.created_records = []  # 作成したレコードのID等を保持
        self.client = None
        self.categories = None
        self.genres = None
        self.accounts = None
        self.crypto_account = None
        self.safe_accounts = []

    def setup(self):
        """テストの前準備"""
        try:
            self.client = ZaimClient()
            
            # マスターデータを取得
            self.categories = self.client.get_categories()
            self.genres = self.client.get_genres()
            self.accounts = self.client.get_accounts()
            
            # crypto_accountアカウントを特定
            for account in self.accounts['accounts']:
                if 'crypto_account' in account['name'].lower() and account['active'] == 1:
                    self.crypto_account_account = account
                    break
            
            if not self.crypto_account_account:
                print("⚠️ crypto_accountアカウントが見つかりません")
                return False
            
            # テスト用の安全なアカウントを選定（crypto_account + お財布/貯金など）
            safe_account_names = ['お財布', 'wallet', '貯金', 'savings', 'テスト', 'test']
            for account in self.accounts['accounts']:
                if (account['active'] == 1 and 
                    (account['id'] == self.crypto_account_account['id'] or
                     any(safe_name in account['name'].lower() for safe_name in safe_account_names))):
                    self.safe_accounts.append(account)
            
            print(f"✅ 安全テスト環境準備完了")
            print(f"   - crypto_accountアカウント: {self.crypto_account_account['name']} (ID: {self.crypto_account_account['id']})")
            print(f"   - 使用可能アカウント: {len(self.safe_accounts)}個")
            
            return True
        except Exception as e:
            print(f"❌ セットアップエラー: {e}")
            return False

    def cleanup(self):
        """テスト後のクリーンアップ"""
        print("\n=== 安全クリーンアップ ===")
        cleanup_success = True
        
        for record in self.created_records:
            try:
                self.client.delete_money(record['id'], record['type'])
                print(f"✅ 削除成功: {record['description']} (ID: {record['id']})")
            except Exception as e:
                print(f"⚠️ 削除失敗: {record['description']} - {e}")
                cleanup_success = False
        
        return cleanup_success

    def find_payment_category_and_genre(self):
        """支出用のカテゴリとジャンルを見つける"""
        payment_categories = [c for c in self.categories['categories'] if c['mode'] == 'payment']
        if not payment_categories:
            return None, None
        
        category = payment_categories[0]
        related_genres = [g for g in self.genres['genres'] if g['category_id'] == category['id']]
        
        if not related_genres:
            return None, None
            
        return category['id'], related_genres[0]['id']

    def find_income_category(self):
        """収入用のカテゴリを見つける"""
        income_categories = [c for c in self.categories['categories'] if c['mode'] == 'income']
        return income_categories[0]['id'] if income_categories else None


def test_safe_payment_with_crypto_account(test_data):
    """crypto_accountアカウントを使った支出テスト（少額）"""
    print("=== 安全支出テスト（crypto_account使用） ===")
    try:
        category_id, genre_id = test_data.find_payment_category_and_genre()
        if not category_id or not genre_id:
            print("⚠️ 支出用のカテゴリ・ジャンルが見つかりません")
            return False

        today = date.today().strftime('%Y-%m-%d')
        
        result = test_data.client.create_payment(
            category_id=category_id,
            genre_id=genre_id,
            amount=1,  # 1円の少額テスト
            date=today,
            from_account_id=test_data.crypto_account_account['id'],
            comment="【テスト】crypto_account少額支出テスト",
            name="テスト取引",
            place="API自動テスト"
        )
        
        # レスポンス構造の確認
        assert 'money' in result
        assert 'id' in result['money']
        assert 'user' in result
        
        record_id = result['money']['id']
        test_data.created_records.append({
            'id': record_id, 
            'type': 'payment',
            'description': 'crypto_account少額支出テスト'
        })
        
        print(f"✅ crypto_account支出データ作成成功: ID {record_id}")
        print(f"   金額: 1円, アカウント: {test_data.crypto_account_account['name']}")
        
        return True, record_id
        
    except Exception as e:
        print(f"❌ crypto_account支出テストエラー: {e}")
        return False, None


def test_safe_income_with_crypto_account(test_data):
    """crypto_accountアカウントを使った収入テスト（少額）"""
    print("\n=== 安全収入テスト（crypto_account使用） ===")
    try:
        category_id = test_data.find_income_category()
        if not category_id:
            print("⚠️ 収入用のカテゴリが見つかりません")
            return False

        today = date.today().strftime('%Y-%m-%d')
        
        result = test_data.client.create_income(
            category_id=category_id,
            amount=1,  # 1円の少額テスト
            date=today,
            to_account_id=test_data.crypto_account_account['id'],
            comment="【テスト】crypto_account少額収入テスト",
            place="API自動テスト"
        )
        
        # レスポンス構造の確認
        assert 'money' in result
        assert 'id' in result['money']
        assert 'user' in result
        
        record_id = result['money']['id']
        test_data.created_records.append({
            'id': record_id, 
            'type': 'income',
            'description': 'crypto_account少額収入テスト'
        })
        
        print(f"✅ crypto_account収入データ作成成功: ID {record_id}")
        print(f"   金額: 1円, アカウント: {test_data.crypto_account_account['name']}")
        
        return True, record_id
        
    except Exception as e:
        print(f"❌ crypto_account収入テストエラー: {e}")
        return False, None


def test_safe_transfer_with_crypto_account(test_data):
    """crypto_accountと安全アカウント間の振替テスト（少額）"""
    print("\n=== 安全振替テスト（crypto_account使用） ===")
    try:
        if len(test_data.safe_accounts) < 2:
            print("⚠️ 振替に必要な安全アカウントが不足しています")
            return False

        # crypto_account以外の安全アカウントを見つける
        other_account = None
        for account in test_data.safe_accounts:
            if account['id'] != test_data.crypto_account_account['id']:
                other_account = account
                break
        
        if not other_account:
            print("⚠️ crypto_account以外の安全アカウントが見つかりません")
            return False

        today = date.today().strftime('%Y-%m-%d')
        
        result = test_data.client.create_transfer(
            amount=1,  # 1円の少額テスト
            date=today,
            from_account_id=test_data.crypto_account_account['id'],
            to_account_id=other_account['id'],
            comment="【テスト】crypto_account→安全アカウント少額振替テスト"
        )
        
        # レスポンス構造の確認
        assert 'money' in result
        assert 'id' in result['money']
        assert 'user' in result
        
        record_id = result['money']['id']
        test_data.created_records.append({
            'id': record_id, 
            'type': 'transfer',
            'description': f'crypto_account→{other_account["name"]}振替テスト'
        })
        
        print(f"✅ crypto_account振替データ作成成功: ID {record_id}")
        print(f"   金額: 1円, {test_data.crypto_account_account['name']} → {other_account['name']}")
        
        return True, record_id
        
    except Exception as e:
        print(f"❌ crypto_account振替テストエラー: {e}")
        return False, None


def test_safe_data_retrieval(test_data):
    """安全なデータ取得テスト"""
    print("\n=== 安全データ取得テスト ===")
    try:
        # 今日のデータを取得
        today = date.today().strftime('%Y-%m-%d')
        
        result = test_data.client.get_money(
            start_date=today,
            end_date=today,
            limit=10
        )
        
        # レスポンス構造の確認
        assert 'money' in result
        assert isinstance(result['money'], list)
        assert 'requested' in result
        
        print(f"✅ 今日のデータ取得成功: {len(result['money'])} 件")
        
        # 作成したテストデータが含まれているかチェック
        created_ids = {r['id'] for r in test_data.created_records}
        retrieved_ids = {r['id'] for r in result['money']}
        
        found_count = len(created_ids & retrieved_ids)
        print(f"   作成したテストデータのうち {found_count}/{len(created_ids)} 件が取得されました")
        
        return True
        
    except Exception as e:
        print(f"❌ データ取得テストエラー: {e}")
        return False


def test_safe_update_and_delete(test_data):
    """安全な更新・削除テスト"""
    print("\n=== 安全更新・削除テスト ===")
    try:
        if not test_data.created_records:
            print("⚠️ 更新・削除対象のデータがありません")
            return False

        # 最初のレコードを更新
        record = test_data.created_records[0]
        record_id = record['id']
        record_type = record['type']
        
        today = date.today().strftime('%Y-%m-%d')
        
        # 更新テスト（金額を2円に変更）
        update_result = test_data.client.update_money(
            record_id=record_id,
            record_type=record_type,
            amount=2,  # 1円から2円に変更
            date=today,
            comment=f"【更新テスト】{record['description']}"
        )
        
        assert 'money' in update_result
        assert update_result['money']['id'] == record_id
        
        print(f"✅ データ更新成功: {record['description']} (ID: {record_id})")
        
        # 削除テスト（最後のレコードを削除）
        if len(test_data.created_records) > 1:
            delete_record = test_data.created_records.pop()
            
            delete_result = test_data.client.delete_money(
                delete_record['id'], 
                delete_record['type']
            )
            
            assert 'money' in delete_result
            assert delete_result['money']['id'] == delete_record['id']
            
            print(f"✅ データ削除成功: {delete_record['description']} (ID: {delete_record['id']})")
        
        return True
        
    except Exception as e:
        print(f"❌ 更新・削除テストエラー: {e}")
        return False


def main():
    """安全なCRUD操作テストの実行"""
    print("Zaim API Client - 安全CRUD操作テスト")
    print("=" * 50)
    print("crypto_accountアカウントを使用して少額（1円）でテストします")
    
    test_data = SafeTestData()
    
    # セットアップ
    if not test_data.setup():
        print("❌ セットアップに失敗しました")
        return 1
    
    tests = [
        (test_safe_payment_with_crypto_account, "crypto_account支出テスト"),
        (test_safe_income_with_crypto_account, "crypto_account収入テスト"),
        (test_safe_transfer_with_crypto_account, "crypto_account振替テスト"),
        (test_safe_data_retrieval, "データ取得テスト"),
        (test_safe_update_and_delete, "更新・削除テスト")
    ]
    
    results = []
    
    try:
        for test_func, test_name in tests:
            try:
                result = test_func(test_data)
                if isinstance(result, tuple):
                    results.append(result[0])
                else:
                    results.append(result)
            except Exception as e:
                print(f"❌ テスト実行エラー ({test_name}): {e}")
                results.append(False)
    
    finally:
        # クリーンアップの実行
        cleanup_success = test_data.cleanup()
        
        print("\n" + "=" * 50)
        print("安全テスト結果サマリー:")
        
        passed = sum(results)
        total = len(results)
        
        for i, ((test_func, test_name), result) in enumerate(zip(tests, results)):
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{i+1}. {test_name}: {status}")
        
        print(f"\n合計: {passed}/{total} テスト通過")
        print(f"クリーンアップ: {'✅ 成功' if cleanup_success else '⚠️ 一部失敗'}")
        
        if passed == total and cleanup_success:
            print("🎉 すべての安全CRUD操作テストが成功しました！")
            return 0
        else:
            print("⚠️ 一部のテストが失敗しました。")
            return 1


if __name__ == "__main__":
    sys.exit(main())