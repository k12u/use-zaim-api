#!/usr/bin/env python3
"""
Zaim CLI - コマンドライン家計簿管理ツール
"""

import os
import sys
import json
import csv
from io import StringIO
from pathlib import Path
from typing import Optional, Dict, Any

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Confirm
import yaml

from zaim_client import ZaimClient, BalanceManager, ZaimAuthManager

console = Console()

# 設定ディレクトリのパス
CONFIG_DIR = Path.home() / '.zaim-cli'
CONFIG_FILE = CONFIG_DIR / 'config.yaml'
AUTH_FILE = CONFIG_DIR / 'auth.json'

# デフォルト設定
DEFAULT_CONFIG = {
    'display': {
        'currency_format': 'yen',
        'show_transaction_count': True,
        'table_style': 'simple'
    },
    'behavior': {
        'confirm_transactions': True,
        'auto_backup': False,
        'default_comment_prefix': 'CLI'
    }
}


class CLIContext:
    """CLI実行コンテキスト"""
    def __init__(self):
        self.client: Optional[ZaimClient] = None
        self.balance_manager: Optional[BalanceManager] = None
        self.config: Dict[str, Any] = {}
        self.dry_run: bool = False
        
    def initialize(self, dry_run: bool = False):
        """クライアントとマネージャーを初期化"""
        try:
            self.dry_run = dry_run
            self.config = self.load_config()
            
            if not dry_run:
                # 自動認証機能を試行
                consumer_key = os.getenv('ZAIM_CONSUMER_KEY')
                consumer_secret = os.getenv('ZAIM_CONSUMER_SECRET')
                
                if consumer_key and consumer_secret:
                    auth_manager = ZaimAuthManager(consumer_key, consumer_secret)
                    credentials = auth_manager.get_stored_credentials()
                    
                    if credentials:
                        # 保存されたトークンを使用
                        access_token, access_token_secret = credentials
                        os.environ['ZAIM_ACCESS_TOKEN'] = access_token
                        os.environ['ZAIM_ACCESS_TOKEN_SECRET'] = access_token_secret
                
                self.client = ZaimClient()
                self.balance_manager = BalanceManager(self.client)
            
            return True
        except Exception as e:
            console.print(f"[red]❌ 初期化エラー: {e}[/red]")
            return False
    
    def load_config(self) -> Dict[str, Any]:
        """設定ファイルを読み込み"""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    user_config = yaml.safe_load(f) or {}
                
                # デフォルト設定とマージ
                config = DEFAULT_CONFIG.copy()
                for section, values in user_config.items():
                    if section in config and isinstance(values, dict):
                        config[section].update(values)
                    else:
                        config[section] = values
                
                return config
            except Exception as e:
                console.print(f"[yellow]⚠️ 設定ファイル読み込みエラー: {e}[/yellow]")
        
        return DEFAULT_CONFIG.copy()
    
    def save_config(self):
        """設定ファイルを保存"""
        try:
            CONFIG_DIR.mkdir(exist_ok=True)
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)
            return True
        except Exception as e:
            console.print(f"[red]❌ 設定保存エラー: {e}[/red]")
            return False


# グローバルコンテキスト
ctx = CLIContext()


def format_amount(amount: int, config: Dict[str, Any]) -> str:
    """金額をフォーマット"""
    if config['display']['currency_format'] == 'yen':
        return f"{amount:,}円"
    else:
        return f"¥{amount:,}"


def output_data(data: Any, output_format: str, headers: Optional[list] = None):
    """データを指定された形式で出力"""
    if output_format == 'json':
        print(json.dumps(data, ensure_ascii=False, indent=2))
    elif output_format == 'csv':
        if isinstance(data, list) and data:
            # リストデータの場合
            if isinstance(data[0], dict):
                # 辞書のリストの場合
                fieldnames = headers or list(data[0].keys())
                output = StringIO()
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
                print(output.getvalue().strip())
            else:
                # 単純なリストの場合
                print(','.join(map(str, data)))
        elif isinstance(data, dict):
            # 単一の辞書の場合
            if headers:
                print(','.join(headers))
                print(','.join(str(data.get(h, '')) for h in headers))
            else:
                print(','.join(data.keys()))
                print(','.join(map(str, data.values())))
        else:
            # その他のデータ
            print(str(data))
    elif output_format == 'table':
        # Rich テーブル形式（従来の表示）
        return data  # 呼び出し側でテーブル表示を処理
    else:
        print(str(data))


def show_balance_result(result: Dict[str, Any], config: Dict[str, Any]):
    """残高結果を表示"""
    if 'accounts' in result:
        # 複数アカウントの場合
        table = Table(title="アカウント残高一覧")
        table.add_column("アカウント名", style="cyan")
        table.add_column("残高", justify="right", style="green")
        if config['display']['show_transaction_count']:
            table.add_column("取引件数", justify="right", style="yellow")
        
        total_balance = 0
        for account in result['accounts']:
            total_balance += account['balance']
            row = [account['name'], format_amount(account['balance'], config)]
            if config['display']['show_transaction_count']:
                row.append(str(account['transaction_count']))
            table.add_row(*row)
        
        console.print(table)
        console.print(f"\n[bold]合計残高: {format_amount(total_balance, config)}[/bold]")
    else:
        # 単一アカウントの結果表示
        account_name = result.get('account_name', '不明')
        current_balance = result.get('current_balance', 0)
        
        panel_content = f"アカウント: {account_name}\n"
        panel_content += f"現在残高: {format_amount(current_balance, config)}"
        
        if 'transaction_count' in result and config['display']['show_transaction_count']:
            panel_content += f"\n取引件数: {result['transaction_count']}件"
        
        console.print(Panel(panel_content, title="残高情報", style="blue"))


def show_adjustment_result(result: Dict[str, Any], config: Dict[str, Any]):
    """調整結果を表示"""
    account_name = result.get('account_name', '不明')
    current_balance = result.get('current_balance', 0)
    target_balance = result.get('target_balance', 0)
    adjustment_needed = result.get('adjustment_needed', 0)
    action = result.get('action', 'unknown')
    
    panel_content = f"アカウント: {account_name}\n"
    panel_content += f"現在残高: {format_amount(current_balance, config)}\n"
    panel_content += f"目標残高: {format_amount(target_balance, config)}\n"
    
    if adjustment_needed != 0:
        if adjustment_needed > 0:
            panel_content += f"[green]調整額: +{format_amount(adjustment_needed, config)}[/green]"
        else:
            panel_content += f"[red]調整額: {format_amount(adjustment_needed, config)}[/red]"
    else:
        panel_content += "[yellow]調整不要（既に目標額です）[/yellow]"
    
    if action == 'dry_run':
        panel_content += f"\n\n[yellow]プレビューモード: {result.get('planned_action', '')}[/yellow]"
        panel_style = "yellow"
    elif action == 'completed':
        panel_content += f"\n\n[green]✅ 調整完了[/green]"
        panel_content += f"\n取引ID: {result.get('transaction_id', 'N/A')}"
        panel_content += f"\n取引タイプ: {result.get('transaction_type', 'N/A')}"
        panel_style = "green"
    elif action == 'no_change':
        panel_style = "blue"
    elif action == 'error':
        panel_content += f"\n\n[red]❌ エラー: {result.get('error', '不明')}[/red]"
        panel_style = "red"
    else:
        panel_style = "blue"
    
    console.print(Panel(panel_content, title="残高調整結果", style=panel_style))


@click.group()
@click.option('--dry-run', is_flag=True, help='実際の操作は行わず、プレビューのみ表示')
@click.option('--json', 'output_format', flag_value='json', help='JSON形式で出力')
@click.option('--table', 'output_format', flag_value='table', help='テーブル形式で出力')
@click.option('--csv', 'output_format', flag_value='csv', default=True, help='CSV形式で出力（デフォルト）')
@click.pass_context
def cli(click_ctx, dry_run, output_format):
    """Zaim家計簿管理CLI"""
    if not ctx.initialize(dry_run=dry_run):
        sys.exit(1)
    
    click_ctx.ensure_object(dict)
    click_ctx.obj['dry_run'] = dry_run
    click_ctx.obj['output_format'] = output_format


@cli.group()
def balance():
    """残高管理コマンド"""
    pass


@balance.command('show')
@click.argument('account_name', required=False)
@click.pass_context
def balance_show(click_ctx, account_name):
    """残高を表示"""
    try:
        output_format = click_ctx.obj['output_format']
        
        if ctx.dry_run:
            # サンプルデータを表示
            sample_result = {
                'accounts': [
                    {'id': 1, 'name': 'サンプルアカウント1', 'balance': 50000, 'transaction_count': 25},
                    {'id': 2, 'name': 'サンプルアカウント2', 'balance': -15000, 'transaction_count': 12}
                ]
            }
            
            if output_format in ['csv', 'json']:
                if 'accounts' in sample_result:
                    output_data(sample_result['accounts'], output_format, 
                               ['id', 'name', 'balance', 'transaction_count'])
                else:
                    output_data(sample_result, output_format)
            else:
                console.print("[yellow]ドライランモード: 残高表示はサンプルデータです[/yellow]")
                show_balance_result(sample_result, ctx.config)
            return
        
        result = ctx.balance_manager.show_balance(account_name)
        
        if output_format in ['csv', 'json']:
            if 'accounts' in result:
                output_data(result['accounts'], output_format, 
                           ['id', 'name', 'balance', 'transaction_count'])
            else:
                output_data(result, output_format)
        else:
            show_balance_result(result, ctx.config)
        
    except Exception as e:
        if click_ctx.obj['output_format'] in ['csv', 'json']:
            print(f"ERROR: {e}")
        else:
            console.print(f"[red]❌ 残高表示エラー: {e}[/red]")
        sys.exit(1)


@balance.command('set')
@click.argument('account_name')
@click.argument('amount', type=int)
@click.option('--comment', '-c', help='コメント')
@click.option('--force', '-f', is_flag=True, help='確認をスキップ')
@click.pass_context
def balance_set(click_ctx, account_name, amount, comment, force):
    """残高を指定額に設定"""
    try:
        dry_run = click_ctx.obj['dry_run']
        output_format = click_ctx.obj['output_format']
        
        if not dry_run and not force and ctx.config['behavior']['confirm_transactions']:
            if output_format == 'table':
                if not Confirm.ask(f"[yellow]{account_name}の残高を{format_amount(amount, ctx.config)}に設定しますか？[/yellow]"):
                    console.print("操作をキャンセルしました。")
                    return
        
        if ctx.dry_run:
            # サンプルデータでプレビュー
            sample_result = {
                'account_name': account_name,
                'account_id': 123,
                'current_balance': 30000,
                'target_balance': amount,
                'adjustment_needed': amount - 30000,
                'transaction_count': 15,
                'action': 'dry_run',
                'status': 'preview'
            }
            
            if output_format in ['csv', 'json']:
                output_data(sample_result, output_format, 
                           ['account_name', 'current_balance', 'target_balance', 
                            'adjustment_needed', 'action', 'status'])
            else:
                console.print("[yellow]ドライランモード: 実際の取引は作成されません[/yellow]")
                sample_result['planned_action'] = f"{abs(amount - 30000):,}円の{'収入' if amount > 30000 else '支出'}取引を作成予定"
                show_adjustment_result(sample_result, ctx.config)
            return
        
        result = ctx.balance_manager.set_balance(
            account_name=account_name,
            target_amount=amount,
            comment=comment,
            dry_run=dry_run
        )
        
        if output_format in ['csv', 'json']:
            output_data(result, output_format, 
                       ['account_name', 'current_balance', 'target_balance', 
                        'adjustment_needed', 'action', 'transaction_id'])
        else:
            show_adjustment_result(result, ctx.config)
        
    except Exception as e:
        if click_ctx.obj['output_format'] in ['csv', 'json']:
            print(f"ERROR: {e}")
        else:
            console.print(f"[red]❌ 残高設定エラー: {e}[/red]")
        sys.exit(1)


@balance.command('add')
@click.argument('account_name')
@click.argument('amount', type=int)
@click.option('--comment', '-c', help='コメント')
@click.option('--force', '-f', is_flag=True, help='確認をスキップ')
@click.pass_context
def balance_add(click_ctx, account_name, amount, comment, force):
    """残高に指定額を追加"""
    try:
        dry_run = click_ctx.obj['dry_run']
        output_format = click_ctx.obj['output_format']
        
        if not dry_run and not force and ctx.config['behavior']['confirm_transactions']:
            if output_format == 'table':
                if not Confirm.ask(f"[yellow]{account_name}に{format_amount(amount, ctx.config)}を追加しますか？[/yellow]"):
                    console.print("操作をキャンセルしました。")
                    return
        
        if ctx.dry_run:
            # サンプルデータでプレビュー
            current_balance = 30000
            target_balance = current_balance + amount
            sample_result = {
                'account_name': account_name,
                'account_id': 123,
                'current_balance': current_balance,
                'target_balance': target_balance,
                'adjustment_needed': amount,
                'transaction_count': 15,
                'action': 'dry_run',
                'status': 'preview'
            }
            
            if output_format in ['csv', 'json']:
                output_data(sample_result, output_format, 
                           ['account_name', 'current_balance', 'target_balance', 
                            'adjustment_needed', 'action', 'status'])
            else:
                console.print("[yellow]ドライランモード: 実際の取引は作成されません[/yellow]")
                sample_result['planned_action'] = f"{amount:,}円の収入取引を作成予定"
                show_adjustment_result(sample_result, ctx.config)
            return
        
        result = ctx.balance_manager.add_balance(
            account_name=account_name,
            amount=amount,
            comment=comment,
            dry_run=dry_run
        )
        
        if output_format in ['csv', 'json']:
            output_data(result, output_format, 
                       ['account_name', 'current_balance', 'target_balance', 
                        'adjustment_needed', 'action', 'transaction_id'])
        else:
            show_adjustment_result(result, ctx.config)
        
    except Exception as e:
        if click_ctx.obj['output_format'] in ['csv', 'json']:
            print(f"ERROR: {e}")
        else:
            console.print(f"[red]❌ 残高追加エラー: {e}[/red]")
        sys.exit(1)


@balance.command('subtract')
@click.argument('account_name')
@click.argument('amount', type=int)
@click.option('--comment', '-c', help='コメント')
@click.option('--force', '-f', is_flag=True, help='確認をスキップ')
@click.pass_context
def balance_subtract(click_ctx, account_name, amount, comment, force):
    """残高から指定額を減算"""
    try:
        dry_run = click_ctx.obj['dry_run']
        output_format = click_ctx.obj['output_format']
        
        if not dry_run and not force and ctx.config['behavior']['confirm_transactions']:
            if output_format == 'table':
                if not Confirm.ask(f"[yellow]{account_name}から{format_amount(amount, ctx.config)}を減算しますか？[/yellow]"):
                    console.print("操作をキャンセルしました。")
                    return
        
        if ctx.dry_run:
            # サンプルデータでプレビュー
            current_balance = 30000
            target_balance = current_balance - amount
            sample_result = {
                'account_name': account_name,
                'account_id': 123,
                'current_balance': current_balance,
                'target_balance': target_balance,
                'adjustment_needed': -amount,
                'transaction_count': 15,
                'action': 'dry_run',
                'status': 'preview'
            }
            
            if output_format in ['csv', 'json']:
                output_data(sample_result, output_format, 
                           ['account_name', 'current_balance', 'target_balance', 
                            'adjustment_needed', 'action', 'status'])
            else:
                console.print("[yellow]ドライランモード: 実際の取引は作成されません[/yellow]")
                sample_result['planned_action'] = f"{amount:,}円の支出取引を作成予定"
                show_adjustment_result(sample_result, ctx.config)
            return
        
        result = ctx.balance_manager.subtract_balance(
            account_name=account_name,
            amount=amount,
            comment=comment,
            dry_run=dry_run
        )
        
        if output_format in ['csv', 'json']:
            output_data(result, output_format, 
                       ['account_name', 'current_balance', 'target_balance', 
                        'adjustment_needed', 'action', 'transaction_id'])
        else:
            show_adjustment_result(result, ctx.config)
        
    except Exception as e:
        if click_ctx.obj['output_format'] in ['csv', 'json']:
            print(f"ERROR: {e}")
        else:
            console.print(f"[red]❌ 残高減算エラー: {e}[/red]")
        sys.exit(1)


@cli.group()
def account():
    """アカウント管理コマンド"""
    pass


@account.command('list')
@click.option('--active-only', is_flag=True, help='アクティブなアカウントのみ表示')
@click.pass_context
def account_list(click_ctx, active_only):
    """アカウント一覧を表示"""
    try:
        output_format = click_ctx.obj['output_format']
        
        if ctx.dry_run:
            sample_accounts = [
                {"id": 1, "name": "サンプル銀行", "active": 1, "status": "active"},
                {"id": 2, "name": "サンプルカード", "active": 1, "status": "active"}
            ]
            
            if output_format in ['csv', 'json']:
                output_data(sample_accounts, output_format, ['id', 'name', 'active', 'status'])
            else:
                console.print("[yellow]ドライランモード: サンプルアカウント情報です[/yellow]")
                table = Table(title="アカウント一覧")
                table.add_column("ID", style="blue")
                table.add_column("名前", style="cyan")
                table.add_column("ステータス", style="green")
                for acc in sample_accounts:
                    table.add_row(str(acc['id']), acc['name'], "✅ アクティブ")
                console.print(table)
            return
        
        accounts = ctx.client.get_accounts()
        account_data = []
        
        for account in accounts['accounts']:
            if active_only and account['active'] != 1:
                continue
            
            account_data.append({
                'id': account['id'],
                'name': account['name'],
                'active': account['active'],
                'status': 'active' if account['active'] == 1 else 'inactive'
            })
        
        if output_format in ['csv', 'json']:
            output_data(account_data, output_format, ['id', 'name', 'active', 'status'])
        else:
            table = Table(title="アカウント一覧")
            table.add_column("ID", style="blue")
            table.add_column("名前", style="cyan")
            table.add_column("ステータス", style="green")
            
            for account_info in account_data:
                status_text = "✅ アクティブ" if account_info['active'] == 1 else "❌ 非アクティブ"
                table.add_row(str(account_info['id']), account_info['name'], status_text)
            
            console.print(table)
        
    except Exception as e:
        if click_ctx.obj['output_format'] in ['csv', 'json']:
            print(f"ERROR: {e}")
        else:
            console.print(f"[red]❌ アカウント一覧取得エラー: {e}[/red]")
        sys.exit(1)


@cli.group()
def auth():
    """認証管理コマンド"""
    pass


@auth.command('login')
@click.option('--port', type=int, help='コールバック用ポート番号')
@click.option('--print-url', is_flag=True, help='URLを出力するのみ（ブラウザを開かない）')
@click.option('--timeout', type=int, default=300, help='タイムアウト秒数')
@click.pass_context
def auth_login(click_ctx, port, print_url, timeout):
    """OAuth認証でログイン"""
    try:
        consumer_key = os.getenv('ZAIM_CONSUMER_KEY')
        consumer_secret = os.getenv('ZAIM_CONSUMER_SECRET')
        
        if not consumer_key or not consumer_secret:
            console.print("[red]❌ ZAIM_CONSUMER_KEY と ZAIM_CONSUMER_SECRET 環境変数を設定してください[/red]")
            sys.exit(1)
        
        auth_manager = ZaimAuthManager(consumer_key, consumer_secret)
        success = auth_manager.login(port=port, print_url=print_url, timeout=timeout)
        
        if not success:
            sys.exit(1)
            
    except Exception as e:
        console.print(f"[red]❌ ログインエラー: {e}[/red]")
        sys.exit(1)


@auth.command('whoami')
@click.pass_context
def auth_whoami(click_ctx):
    """現在のユーザー情報を表示"""
    try:
        consumer_key = os.getenv('ZAIM_CONSUMER_KEY')
        consumer_secret = os.getenv('ZAIM_CONSUMER_SECRET')
        
        if not consumer_key or not consumer_secret:
            console.print("[red]❌ ZAIM_CONSUMER_KEY と ZAIM_CONSUMER_SECRET 環境変数を設定してください[/red]")
            sys.exit(1)
        
        auth_manager = ZaimAuthManager(consumer_key, consumer_secret)
        output_format = click_ctx.obj.get('output_format', 'json')
        
        if output_format in ['csv', 'json']:
            # 静寂モード
            success = auth_manager.whoami()
        else:
            success = auth_manager.whoami()
        
        if not success:
            sys.exit(1)
            
    except Exception as e:
        console.print(f"[red]❌ ユーザー情報取得エラー: {e}[/red]")
        sys.exit(1)


@auth.command('logout')
def auth_logout():
    """ログアウト（保存されたトークンを削除）"""
    try:
        consumer_key = os.getenv('ZAIM_CONSUMER_KEY')
        consumer_secret = os.getenv('ZAIM_CONSUMER_SECRET')
        
        if not consumer_key or not consumer_secret:
            console.print("[red]❌ ZAIM_CONSUMER_KEY と ZAIM_CONSUMER_SECRET 環境変数を設定してください[/red]")
            sys.exit(1)
        
        auth_manager = ZaimAuthManager(consumer_key, consumer_secret)
        success = auth_manager.logout()
        
        if not success:
            sys.exit(1)
            
    except Exception as e:
        console.print(f"[red]❌ ログアウトエラー: {e}[/red]")
        sys.exit(1)


@cli.group()
def config():
    """設定管理コマンド"""
    pass


@config.command('show')
def config_show():
    """現在の設定を表示"""
    console.print(Panel(yaml.dump(ctx.config, default_flow_style=False, allow_unicode=True), 
                       title="現在の設定", style="blue"))


@config.command('set')
@click.argument('key')
@click.argument('value')
def config_set(key, value):
    """設定値を変更"""
    try:
        # ネストされたキー（display.currency_format など）をサポート
        keys = key.split('.')
        target = ctx.config
        
        # 最後のキー以外をたどってオブジェクトを作成
        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            target = target[k]
        
        # 値の型を推測して変換
        final_key = keys[-1]
        if value.lower() in ('true', 'false'):
            target[final_key] = value.lower() == 'true'
        elif value.isdigit():
            target[final_key] = int(value)
        else:
            target[final_key] = value
        
        if ctx.save_config():
            console.print(f"[green]✅ 設定を更新しました: {key} = {value}[/green]")
        else:
            console.print("[red]❌ 設定の保存に失敗しました[/red]")
            
    except Exception as e:
        console.print(f"[red]❌ 設定更新エラー: {e}[/red]")
        sys.exit(1)


@config.command('reset')
@click.option('--force', '-f', is_flag=True, help='確認をスキップ')
def config_reset(force):
    """設定をデフォルトにリセット"""
    if not force:
        if not Confirm.ask("[yellow]設定をデフォルトにリセットしますか？[/yellow]"):
            console.print("操作をキャンセルしました。")
            return
    
    ctx.config = DEFAULT_CONFIG.copy()
    if ctx.save_config():
        console.print("[green]✅ 設定をデフォルトにリセットしました[/green]")
    else:
        console.print("[red]❌ 設定のリセットに失敗しました[/red]")


@cli.command('version')
def version():
    """バージョン情報を表示"""
    console.print("[blue]Zaim CLI v1.0.0[/blue]")
    console.print("Zaim API Python Client with CLI interface")


if __name__ == '__main__':
    cli()