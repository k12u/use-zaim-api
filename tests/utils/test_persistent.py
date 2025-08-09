#!/usr/bin/env python3
"""
CRUD操作テスト（データ保持版）
テストデータを削除せずに残して検証用に保持
"""

import sys
import time
from datetime import date, datetime, timedelta
from zaim_client import ZaimClient


class PersistentTestData:
    """テスト用データの保持（削除なし）"""
    def __init__(self):
        self.created_records = []  # 作成したレコードのID等を保持
        self.client = None
        self.categories = None
        self.genres = None
        self.accounts = None
        self.crypto_account_account = None
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
            
            # テスト用の安全なアカウントを選定
            safe_account_names = ['お財布', 'wallet', '貯金', 'savings', 'テスト', 'test']
            for account in self.accounts['accounts']:
                if (account['active'] == 1 and 
                    (account['id'] == self.crypto_account_account['id'] or
                     any(safe_name in account['name'].lower() for safe_name in safe_account_names))):
                    self.safe_accounts.append(account)
            
            print(f"✅ テスト環境準備完了（データ保持モード）")
            print(f"   - crypto_accountアカウント: {self.crypto_account_account['name']} (ID: {self.crypto_account_account['id']})")
            print(f"   - 使用可能アカウント: {len(self.safe_accounts)}個")
            print(f"   ⚠️ 注意: テストデータは削除されずに残ります")
            
            return True
        except Exception as e:
            print(f"❌ セットアップエラー: {e}")
            return False

    def log_created_record(self, record_info):
        """作成したレコード情報をログ出力"""
        self.created_records.append(record_info)
        print(f"📝 作成記録: {record_info['description']} (ID: {record_info['id']}, タイプ: {record_info['type']})")

    def show_summary(self):
        """作成したテストデータのサマリーを表示"""
        print("\n" + "=" * 50)
        print("作成されたテストデータサマリー")
        print("=" * 50)
        
        if not self.created_records:
            print("作成されたテストデータはありません")
            return
            
        print(f"総作成レコード数: {len(self.created_records)}")
        print("\n詳細:")
        
        for i, record in enumerate(self.created_records, 1):
            print(f"{i}. [{record['type'].upper()}] {record['description']}")
            print(f"   ID: {record['id']}")
            print(f"   金額: {record.get('amount', '不明')}円")
            print(f"   日付: {record.get('date', '不明')}")
            if 'account' in record:
                print(f"   アカウント: {record['account']}")
            print()
        
        print("これらのデータは家計簿に残っています。")
        print("手動で削除する場合は、上記のIDを使用してください。")

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


def test_persistent_payment_series(test_data):
    """連続する支出データの作成テスト"""
    print("=== 連続支出データ作成テスト ===")
    try:
        category_id, genre_id = test_data.find_payment_category_and_genre()
        if not category_id or not genre_id:
            print("⚠️ 支出用のカテゴリ・ジャンルが見つかりません")
            return False

        today = date.today().strftime('%Y-%m-%d')
        
        # 複数の支出データを作成（異なる金額・コメント）
        payment_data = [
            {"amount": 100, "comment": "【API テスト】朝のコーヒー代", "name": "ブレンドコーヒー", "place": "スターバックス"},
            {"amount": 800, "comment": "【API テスト】昼食代", "name": "日替わり定食", "place": "定食屋"},
            {"amount": 500, "comment": "【API テスト】電車代", "name": "往復乗車券", "place": "JR駅"},
            {"amount": 1200, "comment": "【API テスト】本購入", "name": "プログラミング本", "place": "書店"},
        ]
        
        success_count = 0
        
        for i, data in enumerate(payment_data, 1):
            try:
                result = test_data.client.create_payment(
                    category_id=category_id,
                    genre_id=genre_id,
                    amount=data["amount"],
                    date=today,
                    from_account_id=test_data.crypto_account_account['id'],
                    comment=data["comment"],
                    name=data["name"],
                    place=data["place"]
                )
                
                record_info = {
                    'id': result['money']['id'],
                    'type': 'payment',
                    'description': data["comment"],
                    'amount': data["amount"],
                    'date': today,
                    'account': test_data.crypto_account_account['name']
                }
                
                test_data.log_created_record(record_info)
                print(f"   ✅ 支出 {i}: {data['amount']}円 - {data['comment']}")
                success_count += 1
                
            except Exception as e:
                print(f"   ❌ 支出 {i} 失敗: {e}")
        
        print(f"支出データ作成: {success_count}/{len(payment_data)} 件成功")
        return success_count > 0
        
    except Exception as e:
        print(f"❌ 連続支出テストエラー: {e}")
        return False


def test_persistent_income_series(test_data):
    """連続する収入データの作成テスト"""
    print("\n=== 連続収入データ作成テスト ===")
    try:
        category_id = test_data.find_income_category()
        if not category_id:
            print("⚠️ 収入用のカテゴリが見つかりません")
            return False

        today = date.today().strftime('%Y-%m-%d')
        
        # 複数の収入データを作成
        income_data = [
            {"amount": 50000, "comment": "【API テスト】給与（基本給）", "place": "勤務先"},
            {"amount": 10000, "comment": "【API テスト】副業収入", "place": "フリーランス"},
            {"amount": 5000, "comment": "【API テスト】ポイント還元", "place": "クレジットカード"},
        ]
        
        success_count = 0
        
        for i, data in enumerate(income_data, 1):
            try:
                result = test_data.client.create_income(
                    category_id=category_id,
                    amount=data["amount"],
                    date=today,
                    to_account_id=test_data.crypto_account_account['id'],
                    comment=data["comment"],
                    place=data["place"]
                )
                
                record_info = {
                    'id': result['money']['id'],
                    'type': 'income',
                    'description': data["comment"],
                    'amount': data["amount"],
                    'date': today,
                    'account': test_data.crypto_account_account['name']
                }
                
                test_data.log_created_record(record_info)
                print(f"   ✅ 収入 {i}: {data['amount']}円 - {data['comment']}")
                success_count += 1
                
            except Exception as e:
                print(f"   ❌ 収入 {i} 失敗: {e}")
        
        print(f"収入データ作成: {success_count}/{len(income_data)} 件成功")
        return success_count > 0
        
    except Exception as e:
        print(f"❌ 連続収入テストエラー: {e}")
        return False


def test_persistent_transfer_series(test_data):
    """連続する振替データの作成テスト"""
    print("\n=== 連続振替データ作成テスト ===")
    try:
        if len(test_data.safe_accounts) < 2:
            print("⚠️ 振替に必要な安全アカウントが不足しています")
            return False

        # crypto_account以外の安全アカウントを取得
        other_accounts = [acc for acc in test_data.safe_accounts 
                         if acc['id'] != test_data.crypto_account_account['id']]
        
        if not other_accounts:
            print("⚠️ crypto_account以外の安全アカウントが見つかりません")
            return False

        today = date.today().strftime('%Y-%m-%d')
        
        # 複数の振替データを作成
        transfer_data = [
            {
                "amount": 10000, 
                "comment": "【API テスト】月次貯金", 
                "from": test_data.crypto_account_account,
                "to": other_accounts[0]
            },
            {
                "amount": 5000, 
                "comment": "【API テスト】現金引き出し", 
                "from": other_accounts[0] if len(other_accounts) > 0 else test_data.crypto_account_account,
                "to": test_data.crypto_account_account
            },
        ]
        
        success_count = 0
        
        for i, data in enumerate(transfer_data, 1):
            try:
                result = test_data.client.create_transfer(
                    amount=data["amount"],
                    date=today,
                    from_account_id=data["from"]['id'],
                    to_account_id=data["to"]['id'],
                    comment=data["comment"]
                )
                
                record_info = {
                    'id': result['money']['id'],
                    'type': 'transfer',
                    'description': data["comment"],
                    'amount': data["amount"],
                    'date': today,
                    'account': f"{data['from']['name']} → {data['to']['name']}"
                }
                
                test_data.log_created_record(record_info)
                print(f"   ✅ 振替 {i}: {data['amount']}円 - {data['from']['name']} → {data['to']['name']}")
                success_count += 1
                
            except Exception as e:
                print(f"   ❌ 振替 {i} 失敗: {e}")
        
        print(f"振替データ作成: {success_count}/{len(transfer_data)} 件成功")
        return success_count > 0
        
    except Exception as e:
        print(f"❌ 連続振替テストエラー: {e}")
        return False


def test_persistent_data_verification(test_data):
    """作成したデータの検証テスト"""
    print("\n=== データ検証テスト ===")
    try:
        # 今日のデータを取得
        today = date.today().strftime('%Y-%m-%d')
        
        result = test_data.client.get_money(
            start_date=today,
            end_date=today,
            limit=50
        )
        
        print(f"✅ 今日のデータ取得成功: {len(result['money'])} 件")
        
        # 作成したテストデータが含まれているかチェック
        created_ids = {r['id'] for r in test_data.created_records}
        retrieved_ids = {r['id'] for r in result['money']}
        
        found_count = len(created_ids & retrieved_ids)
        print(f"   作成したテストデータのうち {found_count}/{len(created_ids)} 件が取得されました")
        
        # 各タイプの集計
        type_counts = {'payment': 0, 'income': 0, 'transfer': 0}
        type_amounts = {'payment': 0, 'income': 0, 'transfer': 0}
        
        for record in result['money']:
            if record['id'] in created_ids:
                mode = record.get('mode', '')
                amount = record.get('amount', 0)
                if mode in type_counts:
                    type_counts[mode] += 1
                    type_amounts[mode] += amount
        
        print(f"\n   検証結果:")
        for mode, count in type_counts.items():
            mode_name = {'payment': '支出', 'income': '収入', 'transfer': '振替'}.get(mode, mode)
            amount = type_amounts[mode]
            if count > 0:
                print(f"     - {mode_name}: {count}件, 合計{amount:,}円")
        
        return found_count > 0
        
    except Exception as e:
        print(f"❌ データ検証テストエラー: {e}")
        return False


def test_sample_data_update(test_data):
    """サンプルデータの更新テスト"""
    print("\n=== サンプルデータ更新テスト ===")
    try:
        if not test_data.created_records:
            print("⚠️ 更新対象のデータがありません")
            return True  # データがない場合も成功とみなす

        # 最初のレコードを更新
        record = test_data.created_records[0]
        record_id = record['id']
        record_type = record['type']
        
        today = date.today().strftime('%Y-%m-%d')
        original_comment = record['description']
        
        # 更新（コメントを変更）
        update_result = test_data.client.update_money(
            record_id=record_id,
            record_type=record_type,
            amount=record['amount'] + 50,  # 50円プラス
            date=today,
            comment=f"{original_comment} 【更新済み】"
        )
        
        assert 'money' in update_result
        assert update_result['money']['id'] == record_id
        
        # 更新をレコードにも反映
        record['description'] = f"{original_comment} 【更新済み】"
        record['amount'] = record['amount'] + 50
        
        print(f"✅ データ更新成功: {original_comment} (ID: {record_id})")
        print(f"   金額を{record['amount']-50}円から{record['amount']}円に変更")
        
        return True
        
    except Exception as e:
        print(f"❌ データ更新テストエラー: {e}")
        return False


def main():
    """データ保持版CRUD操作テストの実行"""
    print("Zaim API Client - データ保持版CRUD操作テスト")
    print("=" * 50)
    print("⚠️ 重要: このテストで作成されるデータは削除されません")
    print("実際の家計簿データとして残ります。")
    
    # 実行確認
    confirmation = input("\n続行しますか？ [y/N]: ")
    if confirmation.lower() != 'y':
        print("テストを中止しました。")
        return 0
    
    test_data = PersistentTestData()
    
    # セットアップ
    if not test_data.setup():
        print("❌ セットアップに失敗しました")
        return 1
    
    tests = [
        (test_persistent_payment_series, "連続支出データ作成"),
        (test_persistent_income_series, "連続収入データ作成"),
        (test_persistent_transfer_series, "連続振替データ作成"),
        (test_persistent_data_verification, "データ検証"),
        (test_sample_data_update, "サンプル更新")
    ]
    
    results = []
    
    for test_func, test_name in tests:
        try:
            result = test_func(test_data)
            results.append(result)
        except Exception as e:
            print(f"❌ テスト実行エラー ({test_name}): {e}")
            results.append(False)
    
    # 結果サマリーとデータ保持情報
    print("\n" + "=" * 50)
    print("データ保持版テスト結果サマリー:")
    
    passed = sum(results)
    total = len(results)
    
    for i, ((test_func, test_name), result) in enumerate(zip(tests, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{i+1}. {test_name}: {status}")
    
    print(f"\n合計: {passed}/{total} テスト通過")
    
    # 作成されたデータのサマリー表示
    test_data.show_summary()
    
    if passed == total:
        print("🎉 すべてのデータ保持テストが成功しました！")
        return 0
    else:
        print("⚠️ 一部のテストが失敗しました。")
        return 1


if __name__ == "__main__":
    sys.exit(main())