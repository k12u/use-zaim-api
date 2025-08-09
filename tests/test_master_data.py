#!/usr/bin/env python3
"""
マスターデータ取得テストスクリプト
"""

import sys
from zaim_client import ZaimClient


def test_get_categories():
    """ユーザーカテゴリ取得テスト"""
    print("=== ユーザーカテゴリ取得テスト ===")
    try:
        client = ZaimClient()
        categories = client.get_categories()
        
        # レスポンス構造の確認
        assert 'categories' in categories
        assert isinstance(categories['categories'], list)
        assert 'requested' in categories
        
        # カテゴリデータの確認
        if categories['categories']:
            category = categories['categories'][0]
            required_fields = ['id', 'name', 'mode', 'sort', 'active']
            for field in required_fields:
                assert field in category, f"カテゴリに{field}フィールドがありません"
        
        print(f"✅ カテゴリ取得成功: {len(categories['categories'])} 件")
        
        # カテゴリの種類を表示
        payment_categories = [c for c in categories['categories'] if c['mode'] == 'payment']
        income_categories = [c for c in categories['categories'] if c['mode'] == 'income']
        
        print(f"   - 支出カテゴリ: {len(payment_categories)} 件")
        print(f"   - 収入カテゴリ: {len(income_categories)} 件")
        
        return True, categories
        
    except Exception as e:
        print(f"❌ カテゴリ取得テストエラー: {e}")
        return False, None


def test_get_genres():
    """ユーザージャンル取得テスト"""
    print("\n=== ユーザージャンル取得テスト ===")
    try:
        client = ZaimClient()
        genres = client.get_genres()
        
        # レスポンス構造の確認
        assert 'genres' in genres
        assert isinstance(genres['genres'], list)
        assert 'requested' in genres
        
        # ジャンルデータの確認
        if genres['genres']:
            genre = genres['genres'][0]
            required_fields = ['id', 'name', 'category_id', 'sort', 'active']
            for field in required_fields:
                assert field in genre, f"ジャンルに{field}フィールドがありません"
        
        print(f"✅ ジャンル取得成功: {len(genres['genres'])} 件")
        return True, genres
        
    except Exception as e:
        print(f"❌ ジャンル取得テストエラー: {e}")
        return False, None


def test_get_accounts():
    """ユーザーアカウント取得テスト"""
    print("\n=== ユーザーアカウント取得テスト ===")
    try:
        client = ZaimClient()
        accounts = client.get_accounts()
        
        # レスポンス構造の確認
        assert 'accounts' in accounts
        assert isinstance(accounts['accounts'], list)
        assert 'requested' in accounts
        
        # アカウントデータの確認
        if accounts['accounts']:
            account = accounts['accounts'][0]
            required_fields = ['id', 'name', 'sort', 'active']
            for field in required_fields:
                assert field in account, f"アカウントに{field}フィールドがありません"
        
        print(f"✅ アカウント取得成功: {len(accounts['accounts'])} 件")
        
        # アカウント名を表示
        for account in accounts['accounts'][:5]:  # 最初の5件のみ表示
            print(f"   - {account['name']} (ID: {account['id']})")
            
        return True, accounts
        
    except Exception as e:
        print(f"❌ アカウント取得テストエラー: {e}")
        return False, None


def test_get_default_categories():
    """デフォルトカテゴリ取得テスト"""
    print("\n=== デフォルトカテゴリ取得テスト ===")
    try:
        client = ZaimClient()
        categories = client.get_default_categories()
        
        # レスポンス構造の確認
        assert 'categories' in categories
        assert isinstance(categories['categories'], list)
        assert 'requested' in categories
        
        # デフォルトカテゴリは必ず存在する
        assert len(categories['categories']) > 0, "デフォルトカテゴリが存在しません"
        
        # カテゴリデータの確認
        category = categories['categories'][0]
        required_fields = ['id', 'name', 'mode']
        for field in required_fields:
            assert field in category, f"デフォルトカテゴリに{field}フィールドがありません"
        
        print(f"✅ デフォルトカテゴリ取得成功: {len(categories['categories'])} 件")
        return True, categories
        
    except Exception as e:
        print(f"❌ デフォルトカテゴリ取得テストエラー: {e}")
        return False, None


def test_get_default_genres():
    """デフォルトジャンル取得テスト"""
    print("\n=== デフォルトジャンル取得テスト ===")
    try:
        client = ZaimClient()
        genres = client.get_default_genres()
        
        # レスポンス構造の確認
        assert 'genres' in genres
        assert isinstance(genres['genres'], list)
        assert 'requested' in genres
        
        # デフォルトジャンルは必ず存在する
        assert len(genres['genres']) > 0, "デフォルトジャンルが存在しません"
        
        # ジャンルデータの確認
        genre = genres['genres'][0]
        required_fields = ['id', 'name', 'category_id']
        for field in required_fields:
            assert field in genre, f"デフォルトジャンルに{field}フィールドがありません"
        
        print(f"✅ デフォルトジャンル取得成功: {len(genres['genres'])} 件")
        return True, genres
        
    except Exception as e:
        print(f"❌ デフォルトジャンル取得テストエラー: {e}")
        return False, None


def test_get_default_accounts():
    """デフォルトアカウント取得テスト"""
    print("\n=== デフォルトアカウント取得テスト ===")
    try:
        client = ZaimClient()
        accounts = client.get_default_accounts()
        
        # レスポンス構造の確認
        assert 'accounts' in accounts
        assert isinstance(accounts['accounts'], list)
        assert 'requested' in accounts
        
        # デフォルトアカウントは必ず存在する
        assert len(accounts['accounts']) > 0, "デフォルトアカウントが存在しません"
        
        # アカウントデータの確認
        account = accounts['accounts'][0]
        required_fields = ['id', 'name']
        for field in required_fields:
            assert field in account, f"デフォルトアカウントに{field}フィールドがありません"
        
        print(f"✅ デフォルトアカウント取得成功: {len(accounts['accounts'])} 件")
        return True, accounts
        
    except Exception as e:
        print(f"❌ デフォルトアカウント取得テストエラー: {e}")
        return False, None


def test_get_currencies():
    """通貨リスト取得テスト"""
    print("\n=== 通貨リスト取得テスト ===")
    try:
        client = ZaimClient()
        currencies = client.get_currencies()
        
        # レスポンス構造の確認
        assert 'currencies' in currencies
        assert isinstance(currencies['currencies'], list)
        assert 'requested' in currencies
        
        # 通貨は必ず存在する
        assert len(currencies['currencies']) > 0, "通貨リストが存在しません"
        
        # 通貨データの確認
        currency = currencies['currencies'][0]
        required_fields = ['currency_code', 'unit', 'name', 'point']
        for field in required_fields:
            assert field in currency, f"通貨に{field}フィールドがありません"
        
        print(f"✅ 通貨リスト取得成功: {len(currencies['currencies'])} 種類")
        
        # 日本円の存在確認
        jpy_currencies = [c for c in currencies['currencies'] if c['currency_code'] == 'JPY']
        if jpy_currencies:
            jpy = jpy_currencies[0]
            print(f"   - 日本円: {jpy['name']} ({jpy['unit']})")
        
        return True, currencies
        
    except Exception as e:
        print(f"❌ 通貨リスト取得テストエラー: {e}")
        return False, None


def test_data_consistency():
    """データ整合性テスト"""
    print("\n=== データ整合性テスト ===")
    try:
        client = ZaimClient()
        
        # 各データを取得
        categories = client.get_categories()
        genres = client.get_genres()
        
        # ジャンルのcategory_idが実在するカテゴリを参照しているかチェック
        category_ids = {c['id'] for c in categories['categories']}
        orphan_genres = []
        
        for genre in genres['genres']:
            if genre['category_id'] not in category_ids:
                orphan_genres.append(genre)
        
        if orphan_genres:
            print(f"⚠️ 存在しないカテゴリを参照するジャンル: {len(orphan_genres)} 件")
            for genre in orphan_genres[:3]:  # 最初の3件のみ表示
                print(f"   - ジャンル '{genre['name']}' -> カテゴリID {genre['category_id']}")
        else:
            print("✅ ジャンル・カテゴリ関係の整合性確認完了")
        
        return True
        
    except Exception as e:
        print(f"❌ データ整合性テストエラー: {e}")
        return False


def main():
    """マスターデータテストの実行"""
    print("Zaim API Client - マスターデータ取得テスト")
    print("=" * 50)
    
    tests = [
        test_get_categories,
        test_get_genres, 
        test_get_accounts,
        test_get_default_categories,
        test_get_default_genres,
        test_get_default_accounts,
        test_get_currencies,
        test_data_consistency
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            if isinstance(result, tuple):
                results.append(result[0])
            else:
                results.append(result)
        except Exception as e:
            print(f"❌ テスト実行エラー ({test.__name__}): {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("テスト結果サマリー:")
    
    passed = sum(results)
    total = len(results)
    
    for i, (test, result) in enumerate(zip(tests, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{i+1}. {test.__name__}: {status}")
    
    print(f"\n合計: {passed}/{total} テスト通過")
    
    if passed == total:
        print("🎉 すべてのマスターデータテストが成功しました！")
        return 0
    else:
        print("⚠️ 一部のテストが失敗しました。")
        return 1


if __name__ == "__main__":
    sys.exit(main())