# Zaim CLI 使用方法

Zaim家計簿管理のためのコマンドラインインターフェース

## インストール

```bash
# 依存関係をインストール
pip install -r requirements.txt

# CLIコマンドをインストール（推奨）
pip install -e .

# インストール後は zaim-cli コマンドが使用可能
zaim-cli --help

# インストールしない場合は直接実行も可能
python -m zaim_cli.main --help
```

## 基本的な使用方法

### 認証設定

#### 自動OAuth認証（推奨）

Consumer KeyとSecretのみ設定し、Access Tokenは自動取得します：

```bash
export ZAIM_CONSUMER_KEY="your_consumer_key"
export ZAIM_CONSUMER_SECRET="your_consumer_secret"
```

その後、初回ログイン：
```bash
# ブラウザでOAuth認証を実行
zaim-cli auth login

# ユーザー情報確認
zaim-cli auth whoami
```

#### 手動設定（従来方式）

全ての認証情報を手動で設定：

```bash
export ZAIM_CONSUMER_KEY="your_consumer_key"
export ZAIM_CONSUMER_SECRET="your_consumer_secret"
export ZAIM_ACCESS_TOKEN="your_access_token"
export ZAIM_ACCESS_TOKEN_SECRET="your_access_token_secret"
```

### コマンド一覧

#### 認証管理

```bash
# OAuth認証でログイン（ブラウザが自動で開きます）
zaim-cli auth login

# 固定ポートでログイン
zaim-cli auth login --port 8080

# URLのみ表示（ブラウザを開かない）
zaim-cli auth login --print-url

# タイムアウト時間を指定
zaim-cli auth login --timeout 600

# 現在のユーザー情報を表示
zaim-cli auth whoami

# ログアウト（保存されたトークンを削除）
zaim-cli auth logout
```

#### 残高管理

```bash
# 全アカウントの残高を表示
zaim-cli balance show

# 特定アカウントの残高を表示
zaim-cli balance show crypto_account

# 残高を指定額に設定
zaim-cli balance set crypto_account 50000

# 残高に指定額を追加
zaim-cli balance add crypto_account 10000

# 残高から指定額を減算
zaim-cli balance subtract crypto_account 5000

# コメント付きで実行
zaim-cli balance set crypto_account 50000 -c "月末残高調整"

# 確認をスキップして実行
zaim-cli balance set crypto_account 50000 --force
```

#### アカウント管理

```bash
# 全アカウント一覧を表示
zaim-cli account list

# アクティブなアカウントのみ表示
zaim-cli account list --active-only
```

#### 設定管理

```bash
# 現在の設定を表示
zaim-cli config show

# 設定値を変更
zaim-cli config set display.currency_format symbol
zaim-cli config set behavior.confirm_transactions false

# 設定をリセット
zaim-cli config reset
```

#### その他

```bash
# バージョン情報
zaim-cli version

# ドライランモード（実際の操作は行わない）
zaim-cli --dry-run balance set crypto_account 50000

# 出力フォーマット指定
zaim-cli --json balance show          # JSON形式
zaim-cli --csv balance show           # CSV形式（デフォルト）
zaim-cli --table balance show         # テーブル形式（Rich表示）
```

## 設定ファイル

`~/.zaim-cli/config.yaml` で設定をカスタマイズできます：

```yaml
# 表示設定
display:
  currency_format: yen  # "yen" または "symbol"
  show_transaction_count: true
  table_style: simple

# 動作設定
behavior:
  confirm_transactions: true  # 取引作成前に確認
  auto_backup: false
  default_comment_prefix: CLI
```

## 使用例

### 月末の残高調整

```bash
# 現在の残高を確認
zaim-cli balance show crypto_account

# 実際の口座残高に合わせて調整
zaim-cli balance set crypto_account 152340 -c "月末残高調整"
```

### 定期収入の記録

```bash
# 給与を追加
zaim-cli balance add crypto_account 250000 -c "給与振込"
```

### 一括支払いの記録

```bash
# 大きな支出を記録
zaim-cli balance subtract crypto_account 50000 -c "家賃支払い"
```

### プレビューモード

実際の取引を作成する前に結果をプレビューできます：

```bash
# ドライランで実行内容を確認
zaim-cli --dry-run balance set crypto_account 100000

# 問題なければ実際に実行
zaim-cli balance set crypto_account 100000
```

## トラブルシューティング

### 認証エラー

```bash
# 環境変数が設定されているか確認
echo $ZAIM_CONSUMER_KEY
echo $ZAIM_ACCESS_TOKEN
```

### アカウントが見つからない

```bash
# 利用可能なアカウント一覧を確認
zaim-cli account list
```

### 設定の確認

```bash
# 現在の設定を確認
zaim-cli config show
```

## セキュリティ

- 環境変数を使用してAPIキーを管理してください
- 設定ファイルに認証情報を保存しないでください
- ドライランモードを使用して操作を事前確認してください