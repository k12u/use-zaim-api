#!/usr/bin/env python3
"""
CRUD操作テストスクリプト
"""

import sys
import time
from datetime import date, datetime, timedelta
from zaim_client import ZaimClient


class TestData:
    """テスト用データの保持"""
    def __init__(self):
        self.created_records = []  # 作成したレコードのID等を保持
        self.client = None
        self.categories = None
        self.genres = None
        self.accounts = None

    def setup(self):
        """テストの前準備"""
        try:
            self.client = ZaimClient()
            
            # マスターデータを取得
            self.categories = self.client.get_categories()
            self.genres = self.client.get_genres()
            self.accounts = self.client.get_accounts()
            
            return True
        except Exception as e:
            print(f"❌ セットアップエラー: {e}")
            return False

    def cleanup(self):
        """テスト後のクリーンアップ"""
        print("\n=== クリーンアップ ===")
        cleanup_success = True
        
        for record in self.created_records:
            try:
                self.client.delete_money(record['id'], record['type'])
                print(f"✅ 削除成功: {record['type']} ID {record['id']}")
            except Exception as e:
                print(f"⚠️ 削除失敗: {record['type']} ID {record['id']} - {e}")
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


def test_create_payment(test_data):
    """支出データ作成テスト"""
    print("=== 支出データ作成テスト ===")
    try:
        category_id, genre_id = test_data.find_payment_category_and_genre()
        if not category_id or not genre_id:
            print("⚠️ 支出用のカテゴリ・ジャンルが見つかりません")
            return False

        today = date.today().strftime('%Y-%m-%d')
        
        result = test_data.client.create_payment(
            category_id=category_id,
            genre_id=genre_id,
            amount=500,
            date=today,
            comment="テスト支出データ",
            name="テスト商品",
            place="テスト店舗"
        )
        
        # レスポンス構造の確認
        assert 'money' in result
        assert 'id' in result['money']
        assert 'user' in result
        
        record_id = result['money']['id']
        test_data.created_records.append({'id': record_id, 'type': 'payment'})
        
        print(f"✅ 支出データ作成成功: ID {record_id}")
        print(f"   金額: 500円, 日付: {today}")
        
        return True, record_id
        
    except Exception as e:
        print(f"❌ 支出データ作成テストエラー: {e}")
        return False, None


def test_create_income(test_data):
    """収入データ作成テスト"""
    print("\n=== 収入データ作成テスト ===")
    try:
        category_id = test_data.find_income_category()
        if not category_id:
            print("⚠️ 収入用のカテゴリが見つかりません")
            return False

        today = date.today().strftime('%Y-%m-%d')
        
        result = test_data.client.create_income(
            category_id=category_id,
            amount=10000,
            date=today,
            comment="テスト収入データ",
            place="テスト会社"
        )
        
        # レスポンス構造の確認
        assert 'money' in result
        assert 'id' in result['money']
        assert 'user' in result
        
        record_id = result['money']['id']
        test_data.created_records.append({'id': record_id, 'type': 'income'})
        
        print(f"✅ 収入データ作成成功: ID {record_id}")
        print(f"   金額: 10000円, 日付: {today}")
        
        return True, record_id
        
    except Exception as e:
        print(f"❌ 収入データ作成テストエラー: {e}")
        return False, None


def test_create_transfer(test_data):
    """振替データ作成テスト"""
    print("\n=== 振替データ作成テスト ===")
    try:
        if len(test_data.accounts['accounts']) < 2:
            print("⚠️ 振替に必要な2つのアカウントが見つかりません")
            return False

        from_account = test_data.accounts['accounts'][0]
        to_account = test_data.accounts['accounts'][1]
        today = date.today().strftime('%Y-%m-%d')
        
        result = test_data.client.create_transfer(
            amount=5000,
            date=today,
            from_account_id=from_account['id'],
            to_account_id=to_account['id'],
            comment="テスト振替データ"
        )
        
        # レスポンス構造の確認
        assert 'money' in result
        assert 'id' in result['money']
        assert 'user' in result
        
        record_id = result['money']['id']
        test_data.created_records.append({'id': record_id, 'type': 'transfer'})
        
        print(f"✅ 振替データ作成成功: ID {record_id}")
        print(f"   金額: 5000円, {from_account['name']} → {to_account['name']}")
        
        return True, record_id
        
    except Exception as e:
        print(f"❌ 振替データ作成テストエラー: {e}")
        return False, None


def test_get_money(test_data):
    """家計簿データ取得テスト"""
    print("\n=== 家計簿データ取得テスト ===")
    try:
        # 基本的な取得
        result = test_data.client.get_money(limit=10)
        
        # レスポンス構造の確認
        assert 'money' in result
        assert isinstance(result['money'], list)
        assert 'requested' in result
        
        print(f"✅ データ取得成功: {len(result['money'])} 件")
        
        # パラメータ指定での取得テスト
        today = date.today().strftime('%Y-%m-%d')
        yesterday = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        # 日付範囲指定
        filtered_result = test_data.client.get_money(
            start_date=yesterday,
            end_date=today,
            limit=5
        )
        
        print(f"✅ 日付フィルタ取得成功: {len(filtered_result['money'])} 件")
        
        # 作成したデータが取得結果に含まれているか確認
        created_ids = {r['id'] for r in test_data.created_records}
        retrieved_ids = {r['id'] for r in result['money']}
        
        found_count = len(created_ids & retrieved_ids)
        print(f"   作成したデータのうち {found_count}/{len(created_ids)} 件が取得結果に含まれています")
        
        return True
        
    except Exception as e:
        print(f"❌ データ取得テストエラー: {e}")
        return False


def test_update_money(test_data):
    """データ更新テスト"""
    print("\n=== データ更新テスト ===")
    try:
        if not test_data.created_records:
            print("⚠️ 更新対象のデータがありません")
            return False

        # 最初に作成したレコードを更新
        record = test_data.created_records[0]
        record_id = record['id']
        record_type = record['type']
        
        today = date.today().strftime('%Y-%m-%d')
        
        if record_type == 'payment':
            result = test_data.client.update_money(
                record_id=record_id,
                record_type=record_type,
                amount=1000,  # 500円から1000円に変更
                date=today,
                comment="更新されたテスト支出データ"
            )
        elif record_type == 'income':
            result = test_data.client.update_money(
                record_id=record_id,
                record_type=record_type,
                amount=15000,  # 10000円から15000円に変更
                date=today,
                comment="更新されたテスト収入データ"
            )
        elif record_type == 'transfer':
            result = test_data.client.update_money(
                record_id=record_id,
                record_type=record_type,
                amount=7000,  # 5000円から7000円に変更
                date=today,
                comment="更新されたテスト振替データ"
            )
        
        # レスポンス構造の確認
        assert 'money' in result
        assert 'id' in result['money']
        assert result['money']['id'] == record_id
        
        print(f"✅ データ更新成功: {record_type} ID {record_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ データ更新テストエラー: {e}")
        return False


def test_delete_money(test_data):
    """データ削除テスト"""
    print("\n=== データ削除テスト ===")
    try:
        if not test_data.created_records:
            print("⚠️ 削除対象のデータがありません")
            return False

        # 最後に作成したレコードを削除（クリーンアップと重複を避けるため）
        record = test_data.created_records.pop()
        record_id = record['id']
        record_type = record['type']
        
        result = test_data.client.delete_money(record_id, record_type)
        
        # レスポンス構造の確認
        assert 'money' in result
        assert 'id' in result['money']
        assert result['money']['id'] == record_id
        
        print(f"✅ データ削除成功: {record_type} ID {record_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ データ削除テストエラー: {e}")
        return False


def test_boundary_values(test_data):
    """境界値テスト"""
    print("\n=== 境界値テスト ===")
    try:
        category_id, genre_id = test_data.find_payment_category_and_genre()
        if not category_id or not genre_id:
            print("⚠️ テスト用のカテゴリ・ジャンルが見つかりません")
            return False

        today = date.today().strftime('%Y-%m-%d')
        test_results = []
        
        # 金額の境界値テスト
        print("   金額境界値テスト:")
        
        # 最小値: 1円
        try:
            result = test_data.client.create_payment(
                category_id=category_id,
                genre_id=genre_id,
                amount=1,
                date=today,
                comment="境界値テスト:最小金額"
            )
            record_id = result['money']['id']
            test_data.created_records.append({'id': record_id, 'type': 'payment'})
            print("     ✅ 最小金額(1円)テスト成功")
            test_results.append(True)
        except Exception as e:
            print(f"     ❌ 最小金額テスト失敗: {e}")
            test_results.append(False)
        
        # 大きな値: 999999円
        try:
            result = test_data.client.create_payment(
                category_id=category_id,
                genre_id=genre_id,
                amount=999999,
                date=today,
                comment="境界値テスト:大金額"
            )
            record_id = result['money']['id']
            test_data.created_records.append({'id': record_id, 'type': 'payment'})
            print("     ✅ 大金額(999999円)テスト成功")
            test_results.append(True)
        except Exception as e:
            print(f"     ❌ 大金額テスト失敗: {e}")
            test_results.append(False)
        
        # コメント文字数制限テスト
        print("   コメント文字数制限テスト:")
        
        # 100文字（上限値）
        long_comment = "あ" * 100
        try:
            result = test_data.client.create_payment(
                category_id=category_id,
                genre_id=genre_id,
                amount=100,
                date=today,
                comment=long_comment
            )
            record_id = result['money']['id']
            test_data.created_records.append({'id': record_id, 'type': 'payment'})
            print("     ✅ 100文字コメントテスト成功")
            test_results.append(True)
        except Exception as e:
            print(f"     ❌ 100文字コメントテスト失敗: {e}")
            test_results.append(False)
        
        success_rate = sum(test_results) / len(test_results)
        print(f"   境界値テスト成功率: {success_rate:.0%}")
        
        return success_rate > 0.5  # 50%以上成功で合格
        
    except Exception as e:
        print(f"❌ 境界値テストエラー: {e}")
        return False


def main():
    """CRUD操作テストの実行"""
    print("Zaim API Client - CRUD操作テスト")
    print("=" * 50)
    
    test_data = TestData()
    
    # セットアップ
    if not test_data.setup():
        print("❌ セットアップに失敗しました")
        return 1
    
    tests = [
        (test_create_payment, "支出データ作成"),
        (test_create_income, "収入データ作成"), 
        (test_create_transfer, "振替データ作成"),
        (test_get_money, "データ取得"),
        (test_update_money, "データ更新"),
        (test_delete_money, "データ削除"),
        (test_boundary_values, "境界値テスト")
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
        print("テスト結果サマリー:")
        
        passed = sum(results)
        total = len(results)
        
        for i, ((test_func, test_name), result) in enumerate(zip(tests, results)):
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{i+1}. {test_name}: {status}")
        
        print(f"\n合計: {passed}/{total} テスト通過")
        print(f"クリーンアップ: {'✅ 成功' if cleanup_success else '⚠️ 一部失敗'}")
        
        if passed == total and cleanup_success:
            print("🎉 すべてのCRUD操作テストが成功しました！")
            return 0
        else:
            print("⚠️ 一部のテストが失敗しました。")
            return 1


if __name__ == "__main__":
    sys.exit(main())