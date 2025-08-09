#!/usr/bin/env python3
"""
Zaim残高管理エンジン
現在残高の計算と目標残高への調整を行う
"""

import os
from datetime import datetime, date, timedelta
from typing import Optional, Dict, Tuple
from .client import ZaimClient


class BalanceManager:
    """残高管理と調整を行うクラス"""
    
    def __init__(self, client: ZaimClient):
        """
        初期化
        
        Args:
            client: ZaimAPIクライアント
        """
        self.client = client
        self.adjustment_category_name = "残高調整"
        self._accounts_cache = None
        self._categories_cache = None
        self._genres_cache = None
    
    def get_accounts(self) -> Dict:
        """アカウント一覧を取得（キャッシュ付き）"""
        if self._accounts_cache is None:
            self._accounts_cache = self.client.get_accounts()
        return self._accounts_cache
    
    def get_categories(self) -> Dict:
        """カテゴリ一覧を取得（キャッシュ付き）"""
        if self._categories_cache is None:
            self._categories_cache = self.client.get_categories()
        return self._categories_cache
    
    def get_genres(self) -> Dict:
        """ジャンル一覧を取得（キャッシュ付き）"""
        if self._genres_cache is None:
            self._genres_cache = self.client.get_genres()
        return self._genres_cache
    
    def find_account_by_name(self, account_name: str) -> Optional[Dict]:
        """
        名前でアカウントを検索
        
        Args:
            account_name: アカウント名
            
        Returns:
            アカウント情報またはNone
        """
        accounts = self.get_accounts()
        
        for account in accounts['accounts']:
            if (account_name.lower() in account['name'].lower() or 
                account['name'].lower() in account_name.lower()):
                return account
        return None
    
    def calculate_current_balance(self, account_id: int, days_back: int = 365) -> Tuple[int, int]:
        """
        指定アカウントの現在残高を計算
        
        Args:
            account_id: アカウントID
            days_back: 過去何日分を計算するか
            
        Returns:
            (残高変動, 取引件数)
        """
        # 計算期間を設定
        end_date = date.today()
        start_date = end_date - timedelta(days=days_back)
        
        # 取引データを取得
        all_transactions = []
        page = 1
        
        while True:
            result = self.client.get_money(
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d'),
                page=page,
                limit=100
            )
            
            if not result['money']:
                break
                
            all_transactions.extend(result['money'])
            page += 1
            
            if len(result['money']) < 100:
                break
        
        # アカウントに関連する取引をフィルタリング
        balance_change = 0
        transaction_count = 0
        
        for transaction in all_transactions:
            involved = False
            
            if transaction['mode'] == 'income':
                if transaction.get('to_account_id') == account_id:
                    balance_change += transaction['amount']
                    involved = True
                    
            elif transaction['mode'] == 'payment':
                if transaction.get('from_account_id') == account_id:
                    balance_change -= transaction['amount']
                    involved = True
                    
            elif transaction['mode'] == 'transfer':
                if transaction.get('from_account_id') == account_id:
                    balance_change -= transaction['amount']
                    involved = True
                elif transaction.get('to_account_id') == account_id:
                    balance_change += transaction['amount']
                    involved = True
            
            if involved:
                transaction_count += 1
        
        return balance_change, transaction_count
    
    def find_adjustment_category_and_genre(self) -> Tuple[Optional[int], Optional[int]]:
        """
        残高調整用のカテゴリとジャンルを検索または作成
        
        Returns:
            (category_id, genre_id)
        """
        categories = self.get_categories()
        genres = self.get_genres()
        
        # 既存のカテゴリから検索
        adjustment_category = None
        for category in categories['categories']:
            if (self.adjustment_category_name in category['name'] or 
                'adjustment' in category['name'].lower() or
                'adjust' in category['name'].lower()):
                adjustment_category = category
                break
        
        # カテゴリが見つからない場合は、適当なカテゴリを使用
        if not adjustment_category:
            # 収入カテゴリの最初のものを使用
            income_categories = [c for c in categories['categories'] if c['mode'] == 'income']
            if income_categories:
                adjustment_category = income_categories[0]
        
        if not adjustment_category:
            return None, None
        
        # 関連ジャンルを検索
        related_genres = [g for g in genres['genres'] 
                         if g['category_id'] == adjustment_category['id']]
        
        genre_id = related_genres[0]['id'] if related_genres else None
        
        return adjustment_category['id'], genre_id
    
    def create_adjustment_transaction(self, account_id: int, amount: int, 
                                    comment: str = "CLI残高調整") -> Dict:
        """
        残高調整用の取引を作成
        
        Args:
            account_id: 調整対象アカウントID
            amount: 調整金額（正数=収入、負数=支出）
            comment: コメント
            
        Returns:
            作成された取引情報
        """
        today = date.today().strftime('%Y-%m-%d')
        
        if amount > 0:
            # 収入として追加
            category_id, genre_id = self.find_adjustment_category_and_genre()
            if not category_id:
                raise Exception("残高調整用の収入カテゴリが見つかりません")
            
            return self.client.create_income(
                category_id=category_id,
                amount=abs(amount),
                date=today,
                to_account_id=account_id,
                comment=comment
            )
        else:
            # 支出として減少
            categories = self.get_categories()
            genres = self.get_genres()
            
            # 適当な支出カテゴリを使用
            payment_categories = [c for c in categories['categories'] if c['mode'] == 'payment']
            if not payment_categories:
                raise Exception("支出用カテゴリが見つかりません")
            
            category = payment_categories[0]
            related_genres = [g for g in genres['genres'] if g['category_id'] == category['id']]
            genre_id = related_genres[0]['id'] if related_genres else None
            
            if not genre_id:
                raise Exception("支出用ジャンルが見つかりません")
            
            return self.client.create_payment(
                category_id=category['id'],
                genre_id=genre_id,
                amount=abs(amount),
                date=today,
                from_account_id=account_id,
                comment=comment
            )
    
    def set_balance(self, account_name: str, target_amount: int, 
                   comment: Optional[str] = None, dry_run: bool = False) -> Dict:
        """
        アカウント残高を指定額に設定
        
        Args:
            account_name: アカウント名
            target_amount: 目標金額
            comment: コメント
            dry_run: 実行せずにプレビューのみ
            
        Returns:
            実行結果情報
        """
        # アカウントを検索
        account = self.find_account_by_name(account_name)
        if not account:
            raise Exception(f"アカウント '{account_name}' が見つかりません")
        
        # 現在残高を計算
        current_balance, transaction_count = self.calculate_current_balance(account['id'])
        
        # 調整が必要な金額を計算
        adjustment = target_amount - current_balance
        
        result = {
            'account_name': account['name'],
            'account_id': account['id'],
            'current_balance': current_balance,
            'target_balance': target_amount,
            'adjustment_needed': adjustment,
            'transaction_count': transaction_count,
            'action': None,
            'transaction_id': None
        }
        
        if adjustment == 0:
            result['action'] = 'no_change'
            return result
        
        # 調整コメントを生成
        if not comment:
            if adjustment > 0:
                comment = f"CLI: 残高調整 (+{adjustment:,}円)"
            else:
                comment = f"CLI: 残高調整 ({adjustment:,}円)"
        
        result['comment'] = comment
        
        if dry_run:
            result['action'] = 'dry_run'
            if adjustment > 0:
                result['planned_action'] = f"{adjustment:,}円の収入取引を作成予定"
            else:
                result['planned_action'] = f"{abs(adjustment):,}円の支出取引を作成予定"
            return result
        
        # 実際の調整取引を実行
        try:
            transaction_result = self.create_adjustment_transaction(
                account['id'], adjustment, comment
            )
            
            result['action'] = 'completed'
            result['transaction_id'] = transaction_result['money']['id']
            result['transaction_type'] = 'income' if adjustment > 0 else 'payment'
            
        except Exception as e:
            result['action'] = 'error'
            result['error'] = str(e)
        
        return result
    
    def add_balance(self, account_name: str, amount: int, 
                   comment: Optional[str] = None, dry_run: bool = False) -> Dict:
        """
        アカウント残高に指定額を追加
        
        Args:
            account_name: アカウント名
            amount: 追加金額
            comment: コメント
            dry_run: 実行せずにプレビューのみ
            
        Returns:
            実行結果情報
        """
        # アカウントを検索
        account = self.find_account_by_name(account_name)
        if not account:
            raise Exception(f"アカウント '{account_name}' が見つかりません")
        
        # 現在残高を計算
        current_balance, transaction_count = self.calculate_current_balance(account['id'])
        target_balance = current_balance + amount
        
        return self.set_balance(account_name, target_balance, comment, dry_run)
    
    def subtract_balance(self, account_name: str, amount: int, 
                        comment: Optional[str] = None, dry_run: bool = False) -> Dict:
        """
        アカウント残高から指定額を減算
        
        Args:
            account_name: アカウント名
            amount: 減算金額
            comment: コメント
            dry_run: 実行せずにプレビューのみ
            
        Returns:
            実行結果情報
        """
        # アカウントを検索
        account = self.find_account_by_name(account_name)
        if not account:
            raise Exception(f"アカウント '{account_name}' が見つかりません")
        
        # 現在残高を計算
        current_balance, transaction_count = self.calculate_current_balance(account['id'])
        target_balance = current_balance - amount
        
        return self.set_balance(account_name, target_balance, comment, dry_run)
    
    def show_balance(self, account_name: Optional[str] = None) -> Dict:
        """
        残高情報を表示
        
        Args:
            account_name: アカウント名（Noneの場合は全アカウント）
            
        Returns:
            残高情報
        """
        if account_name:
            # 特定アカウントの残高
            account = self.find_account_by_name(account_name)
            if not account:
                raise Exception(f"アカウント '{account_name}' が見つかりません")
            
            balance, transaction_count = self.calculate_current_balance(account['id'])
            
            return {
                'accounts': [{
                    'name': account['name'],
                    'id': account['id'],
                    'balance': balance,
                    'transaction_count': transaction_count
                }]
            }
        else:
            # 全アカウントの残高
            accounts = self.get_accounts()
            result = {'accounts': []}
            
            for account in accounts['accounts']:
                if account['active'] == 1:
                    balance, transaction_count = self.calculate_current_balance(account['id'])
                    result['accounts'].append({
                        'name': account['name'],
                        'id': account['id'],
                        'balance': balance,
                        'transaction_count': transaction_count
                    })
            
            return result