#!/usr/bin/env python3
"""
全テスト実行スクリプト
"""

import sys
import subprocess
import time
from datetime import datetime


def run_test_script(script_name, description):
    """テストスクリプトを実行し、結果を返す"""
    print(f"\n{'='*60}")
    print(f"実行中: {description}")
    print(f"スクリプト: {script_name}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            [sys.executable, script_name],
            capture_output=True,
            text=True,
            timeout=300  # 5分でタイムアウト
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        # 標準出力を表示
        if result.stdout:
            print(result.stdout)
        
        # 標準エラー出力を表示
        if result.stderr:
            print("STDERR:", result.stderr)
        
        print(f"\n実行時間: {duration:.2f}秒")
        print(f"終了コード: {result.returncode}")
        
        return result.returncode == 0, duration
        
    except subprocess.TimeoutExpired:
        print("❌ テストがタイムアウトしました (5分)")
        return False, 300
    except FileNotFoundError:
        print(f"❌ テストスクリプトが見つかりません: {script_name}")
        return False, 0
    except Exception as e:
        print(f"❌ テスト実行エラー: {e}")
        return False, 0


def check_environment():
    """実行環境の確認"""
    print("=== 実行環境確認 ===")
    
    # 必要なファイルの存在確認
    required_files = [
        'zaim_client.py',
        'test_auth.py',
        'test_master_data.py',
        'test_crud.py',
        'test_error_handling.py',
        'test_integration.py'
    ]
    
    missing_files = []
    for file in required_files:
        try:
            with open(file, 'r'):
                pass
        except FileNotFoundError:
            missing_files.append(file)
    
    if missing_files:
        print("❌ 以下のファイルが見つかりません:")
        for file in missing_files:
            print(f"   - {file}")
        return False
    
    # 環境変数の確認（警告のみ）
    import os
    env_vars = ['ZAIM_CONSUMER_KEY', 'ZAIM_CONSUMER_SECRET', 
                'ZAIM_ACCESS_TOKEN', 'ZAIM_ACCESS_TOKEN_SECRET']
    
    missing_env = [var for var in env_vars if not os.getenv(var)]
    if missing_env:
        print("⚠️ 以下の環境変数が設定されていません:")
        for var in missing_env:
            print(f"   - {var}")
        print("   認証が必要なテストは失敗する可能性があります。")
    
    print("✅ 実行環境確認完了")
    return True


def main():
    """全テストの実行"""
    print("Zaim API Client - 全テスト実行")
    print("=" * 60)
    print(f"実行開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 実行環境確認
    if not check_environment():
        print("❌ 実行環境に問題があります")
        return 1
    
    # テスト一覧
    tests = [
        ('test_auth.py', '認証テスト'),
        ('test_master_data.py', 'マスターデータ取得テスト'),
        ('test_crud.py', 'CRUD操作テスト'),
        ('test_error_handling.py', 'エラーハンドリングテスト'),
        ('test_integration.py', '統合テスト')
    ]
    
    results = []
    total_duration = 0
    
    for script, description in tests:
        success, duration = run_test_script(script, description)
        results.append((script, description, success, duration))
        total_duration += duration
        
        if not success:
            print(f"\n⚠️ {description}が失敗しましたが、続行します...")
        
        # 次のテストまで少し待機
        time.sleep(1)
    
    # 結果サマリー
    print("\n" + "=" * 60)
    print("全テスト結果サマリー")
    print("=" * 60)
    
    passed_tests = 0
    for i, (script, description, success, duration) in enumerate(results):
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{i+1}. {description}: {status} ({duration:.2f}秒)")
        if success:
            passed_tests += 1
    
    total_tests = len(results)
    success_rate = passed_tests / total_tests
    
    print(f"\n総実行時間: {total_duration:.2f}秒")
    print(f"成功率: {passed_tests}/{total_tests} ({success_rate:.0%})")
    
    # 全体評価
    print("\n" + "=" * 60)
    if success_rate >= 0.8:
        print("🎉 テスト結果: 優秀")
        print("   Zaim APIクライアントは本格的な使用に適しています！")
        final_result = 0
    elif success_rate >= 0.6:
        print("🟡 テスト結果: 良好")
        print("   基本機能は動作しますが、一部改善の余地があります。")
        final_result = 0
    elif success_rate >= 0.4:
        print("🟠 テスト結果: 要改善")
        print("   基本的な機能は動作しますが、問題があります。")
        final_result = 1
    else:
        print("🔴 テスト結果: 重大な問題")
        print("   多くの機能で問題が発生しています。設定を確認してください。")
        final_result = 1
    
    print(f"\n終了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    return final_result


if __name__ == "__main__":
    sys.exit(main())