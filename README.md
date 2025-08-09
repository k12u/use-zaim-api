# Zaim API Client

PythonでZaimの家計簿データを操作するためのAPIクライアントライブラリとCLIツールです。

## 特徴

- **自動OAuth認証**: ブラウザでのワンクリック認証
- **CLI提供**: 残高管理や取引操作のコマンドラインツール
- **CSV/JSON出力**: 自動化に適した出力フォーマット
- **支出・収入・振替**: 全ての取引タイプに対応
- **環境変数管理**: 安全な認証情報管理

## インストール

```bash
# 依存関係をインストール
pip install -r requirements.txt

# CLI コマンドをインストール（推奨）
pip install -e .
```

## クイックスタート

### 1. Consumer KeyとSecretを設定
```bash
export ZAIM_CONSUMER_KEY="your_consumer_key"
export ZAIM_CONSUMER_SECRET="your_consumer_secret"
```

### 2. 自動OAuth認証
```bash
# ブラウザで認証（初回のみ）
zaim-cli auth login

# ユーザー情報確認
zaim-cli auth whoami
```

### 3. CLI使用例
```bash
# 残高確認（CSV形式）
zaim-cli balance show

# 残高調整
zaim-cli balance set crypto_account 50000

# JSON形式で出力
zaim-cli --json balance show
```

## 基本的な使用方法

```python
from zaim_client import ZaimClient

# クライアントの初期化
client = ZaimClient()

# ユーザー情報の確認
user_info = client.verify_user()
print(user_info['me']['name'])

# 支出データの登録
payment = client.create_payment(
    category_id=101,  # 食費カテゴリ
    genre_id=10101,   # 食料品ジャンル
    amount=500,       # 金額
    date='2024-01-01',
    comment='お昼ご飯'
)

# データの取得
money_records = client.get_money(limit=10)
```

## API メソッド

### 認証
- `verify_user()` - ユーザー情報の取得

### 家計簿データ
- `get_money()` - 家計簿データの取得
- `create_payment()` - 支出データの作成
- `create_income()` - 収入データの作成  
- `create_transfer()` - 振替データの作成
- `update_money()` - データの更新
- `delete_money()` - データの削除

### マスターデータ
- `get_categories()` - ユーザーのカテゴリ一覧
- `get_genres()` - ユーザーのジャンル一覧
- `get_accounts()` - ユーザーのアカウント一覧
- `get_default_categories()` - デフォルトカテゴリ一覧
- `get_default_genres()` - デフォルトジャンル一覧
- `get_currencies()` - 通貨一覧

## エラーハンドリング

```python
try:
    client = ZaimClient()
    result = client.create_payment(...)
except ValueError as e:
    print(f"設定エラー: {e}")
except Exception as e:
    print(f"API エラー: {e}")
```

## ファイル構造

```
use-zaim-api/
├── zaim_client/              # コアライブラリ
│   ├── client.py            # ZaimClient
│   ├── auth.py              # OAuth認証
│   └── balance.py           # 残高管理
├── zaim_cli/                # CLI
│   ├── main.py              # メインCLI
│   └── config.example.yaml  # 設定例
├── tests/                   # テスト
├── docs/                    # ドキュメント
├── examples/                # 使用例
└── scripts/                 # ユーティリティ
```

## 実行例

```bash
# ライブラリ使用例
python examples/basic_usage.py

# CLI使用例  
zaim-cli balance show
```

## 詳細ドキュメント

- [CLI使用方法](docs/CLI_USAGE.md) - コマンドライン詳細ガイド
- [API ガイド](docs/API_GUIDE.md) - ライブラリAPI詳細
- [認証改善仕様](docs/auth_improvement.md) - OAuth自動化の技術仕様

## 注意事項

- OAuth認証情報は適切に管理してください
- APIの利用制限にご注意ください
- トークンは `~/.zaim-cli/tokens.json` に安全保存されます