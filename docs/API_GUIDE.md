# Zaim API完全ガイド

このドキュメントは、実際にZaim APIを使用して得られた知見をまとめたものです。

## 📋 目次

1. [基本情報](#基本情報)
2. [認証とセットアップ](#認証とセットアップ)
3. [API機能一覧](#API機能一覧)
4. [制限事項と注意点](#制限事項と注意点)
5. [実装のベストプラクティス](#実装のベストプラクティス)
6. [トラブルシューティング](#トラブルシューティング)
7. [実用的な使用例](#実用的な使用例)

---

## 基本情報

### API仕様
- **認証方式**: OAuth 1.0a（HMAC-SHA1署名）
- **プロトコル**: HTTPS必須
- **データ形式**: JSON のみ
- **ベースURL**: `https://api.zaim.net/v2`
- **文字エンコード**: UTF-8

### 対象データ
- ✅ ユーザーが手動入力したデータのみアクセス可能
- ❌ 自動取得された銀行データ等はAPI経由では取得不可

### 料金
- **個人利用**: 無料
- **法人利用**: 要相談

---

## 認証とセットアップ

### 必要な認証情報
Zaim Developers Centerで取得する4つの情報：

```bash
ZAIM_CONSUMER_KEY=your_consumer_key_here
ZAIM_CONSUMER_SECRET=your_consumer_secret_here
ZAIM_ACCESS_TOKEN=your_access_token_here
ZAIM_ACCESS_TOKEN_SECRET=your_access_token_secret_here
```

### 認証フロー

#### 1. アプリケーション登録
[Zaim Developers Center](https://dev.zaim.net/)でアプリケーション登録してConsumer Key/Secretを取得

#### 2. OAuth 1.0a 3-legged認証フロー

```
1. リクエストトークン取得
   POST https://api.zaim.net/v2/auth/request
   
2. ユーザー認証
   GET https://auth.zaim.net/users/auth?oauth_token={request_token}
   
3. アクセストークン取得  
   POST https://api.zaim.net/v2/auth/access
```

#### 詳細な認証手順

**Step 1: リクエストトークン取得**
```python
import requests
from requests_oauthlib import OAuth1

# Consumer Key/Secretでリクエストトークン取得
auth = OAuth1(
    consumer_key,
    client_secret=consumer_secret,
    signature_method='HMAC-SHA1'
)

response = requests.post(
    'https://api.zaim.net/v2/auth/request',
    auth=auth
)

# レスポンスからリクエストトークンを解析
request_token = parse_qs(response.text)
oauth_token = request_token['oauth_token'][0]
oauth_token_secret = request_token['oauth_token_secret'][0]
```

**Step 2: ユーザー認証（ブラウザでアクセス）**
```python
# ユーザーをこのURLにリダイレクト
auth_url = f"https://auth.zaim.net/users/auth?oauth_token={oauth_token}"
print(f"以下のURLにアクセスして認証してください: {auth_url}")

# ユーザー認証後、oauth_verifierが返される
oauth_verifier = input("oauth_verifierを入力してください: ")
```

**Step 3: アクセストークン取得**
```python
# リクエストトークン + verifierでアクセストークン取得
auth = OAuth1(
    consumer_key,
    client_secret=consumer_secret,
    resource_owner_key=oauth_token,
    resource_owner_secret=oauth_token_secret,
    verifier=oauth_verifier,
    signature_method='HMAC-SHA1'
)

response = requests.post(
    'https://api.zaim.net/v2/auth/access',
    auth=auth
)

# 最終的なアクセストークンを取得
access_token = parse_qs(response.text)
final_oauth_token = access_token['oauth_token'][0]
final_oauth_token_secret = access_token['oauth_token_secret'][0]

# これらの値を保存して今後のAPI呼び出しに使用
```

#### 認証後のAPI利用
```python
# 取得したアクセストークンでAPI呼び出し
auth = OAuth1(
    consumer_key,
    client_secret=consumer_secret, 
    resource_owner_key=final_oauth_token,
    resource_owner_secret=final_oauth_token_secret,
    signature_method='HMAC-SHA1'
)

# 以降、このauthオブジェクトを使ってAPI呼び出し
response = requests.get(
    'https://api.zaim.net/v2/home/user/verify',
    auth=auth
)
```

### 実装時の注意点
```python
# ❌ 間違った実装
response = requests.get(url, auth=oauth, data=some_data)  # GETにdataは不可

# ✅ 正しい実装  
if method == 'GET':
    response = requests.get(url, auth=oauth, params=params)
else:
    response = requests.post(url, auth=oauth, data=data)
```

### 🛠️ CLI自動OAuth認証の使用

CLIの自動OAuth認証機能を使用することを推奨します：

```bash
# Consumer Key/Secretを環境変数に設定
export ZAIM_CONSUMER_KEY=your_consumer_key
export ZAIM_CONSUMER_SECRET=your_consumer_secret

# 自動OAuth認証（ブラウザが自動で開きます）
zaim-cli auth login
```

この方法は以下を自動化します：
1. リクエストトークンの取得
2. 認証URLをブラウザで開く
3. アクセストークンの取得
4. API接続テスト
5. `.env`ファイルへの認証情報保存

---

## API機能一覧

### 🔐 ユーザー認証
| エンドポイント | メソッド | 説明 | 実装済み |
|---|---|---|---|
| `/v2/home/user/verify` | GET | ユーザー情報確認 | ✅ |

**レスポンス例**:
```json
{
  "me": {
    "id": 123456,
    "name": "Sample User", 
    "input_count": 8,
    "currency_code": "JPY"
  }
}
```

### 💰 家計簿データ操作

#### 📖 データ取得
| エンドポイント | メソッド | 説明 | 実装済み |
|---|---|---|---|
| `/v2/home/money` | GET | 家計簿データ取得 | ✅ |

**主要パラメータ**:
- `mapping`: 必須（常に1）
- `start_date`, `end_date`: 日付範囲（YYYY-MM-DD形式）
- `category_id`, `genre_id`: カテゴリ・ジャンル絞り込み
- `mode`: タイプ絞り込み（payment/income/transfer）
- `page`, `limit`: ページング（limit最大100）

#### ✏️ データ作成
| エンドポイント | メソッド | 説明 | 実装済み |
|---|---|---|---|
| `/v2/home/money/payment` | POST | 支出データ作成 | ✅ |
| `/v2/home/money/income` | POST | 収入データ作成 | ✅ |
| `/v2/home/money/transfer` | POST | 振替データ作成 | ✅ |

**支出データ作成例**:
```python
client.create_payment(
    category_id=101,
    genre_id=10101,
    amount=500,
    date='2024-01-01',
    from_account_id=1,  # オプション
    comment='昼食代',    # オプション（100文字まで）
    name='弁当',        # オプション（100文字まで）
    place='コンビニ'     # オプション（100文字まで）
)
```

#### 🔄 データ更新・削除
| エンドポイント | メソッド | 説明 | 実装済み |
|---|---|---|---|
| `/v2/home/money/{type}/{id}` | PUT | データ更新 | ✅ |
| `/v2/home/money/{type}/{id}` | DELETE | データ削除 | ✅ |

### 📚 マスターデータ取得

#### ユーザー固有データ
| エンドポイント | メソッド | 説明 | 実装済み |
|---|---|---|---|
| `/v2/home/category` | GET | ユーザーカテゴリ | ✅ |
| `/v2/home/genre` | GET | ユーザージャンル | ✅ |
| `/v2/home/account` | GET | ユーザーアカウント | ✅ |

#### システムデフォルトデータ
| エンドポイント | メソッド | 説明 | 実装済み |
|---|---|---|---|
| `/v2/category` | GET | デフォルトカテゴリ | ✅ |
| `/v2/genre` | GET | デフォルトジャンル | ✅ |
| `/v2/account` | GET | デフォルトアカウント | ✅ |
| `/v2/currency` | GET | 通貨リスト | ✅ |

---

## 制限事項と注意点

### ❌ 提供されていない機能

1. **残高取得API**
   - 残高の絶対値は取得不可
   - 取引履歴から変動計算のみ可能

2. **アカウント作成API**
   - API経由でのアカウント作成不可
   - Web画面での手動作成が必要

3. **カテゴリ・ジャンル作成API**
   - マスターデータの追加・変更不可

4. **一括データ操作**
   - 複数レコードの同時作成・更新不可

### ⚠️ データ制限

1. **文字数制限**
   - `comment`, `name`, `place`: 100文字まで

2. **日付制限**
   - 支出・振替: 過去・未来5年まで
   - 収入: 過去3ヶ月まで（APIドキュメント記載）

3. **ページング制限**
   - `limit`: 最大100件
   - 大量データ取得時は複数回リクエスト必要

4. **金額制限**
   - 負の金額は不可
   - 0円の場合はエラー

### 🚫 APIエラーパターン

| HTTPステータス | 説明 | 対応方法 |
|---|---|---|
| 400 | パラメータ不足・不正 | 必須パラメータの確認 |
| 401 | 認証失敗 | OAuth認証情報の確認 |
| 404 | 存在しないリソース | エンドポイントURLの確認 |

---

## 実装のベストプラクティス

### 🔧 リクエスト実装

```python
def _make_request(self, method, endpoint, params=None, data=None):
    """正しいHTTPリクエスト実装"""
    request_params = {
        'method': method,
        'url': f"{self.BASE_URL}{endpoint}",
        'auth': self.oauth_auth
    }
    
    # GETとPOST/PUT/DELETEで分岐
    if method.upper() == 'GET':
        if params:
            request_params['params'] = params
    else:
        if data:
            request_params['data'] = data
            request_params['headers'] = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
    
    return requests.request(**request_params)
```

### 📝 エラーハンドリング

```python
try:
    response = self._make_request('GET', '/home/user/verify')
    response.raise_for_status()
    return response.json()
except requests.exceptions.HTTPError as e:
    if response.status_code == 401:
        raise AuthenticationError("OAuth認証に失敗しました")
    elif response.status_code == 400:
        raise ValidationError("リクエストパラメータが不正です")
    else:
        raise APIError(f"API呼び出しに失敗しました: {e}")
```

### 🧪 テストデータ管理

```python
class TestDataManager:
    def __init__(self):
        self.created_records = []
    
    def create_and_track(self, create_func, **kwargs):
        """データ作成と追跡"""
        result = create_func(**kwargs)
        self.created_records.append({
            'id': result['money']['id'],
            'type': kwargs.get('type', 'unknown')
        })
        return result
    
    def cleanup_all(self):
        """全テストデータの削除"""
        for record in self.created_records:
            try:
                self.client.delete_money(record['id'], record['type'])
            except Exception as e:
                print(f"削除失敗: {e}")
```

---

## トラブルシューティング

### 🚨 よくあるエラーと解決方法

#### 1. "GET/HEAD requests should not include body"
**原因**: GETリクエストに`data`パラメータを指定
```python
# ❌ 間違い
requests.get(url, auth=oauth, data=data)

# ✅ 正解  
requests.get(url, auth=oauth, params=params)
```

#### 2. OAuth認証失敗（401エラー）
**確認項目**:
- Consumer Key/Secretが正しいか
- Access Token/Secretが正しいか
- 署名生成が適切か（HMAC-SHA1）
- システム時刻のずれはないか

#### 3. 必須パラメータ不足（400エラー）
**支出作成時の必須項目**:
- `mapping: 1`
- `category_id`
- `genre_id`
- `amount`
- `date`

#### 4. 文字数制限エラー
```python
# 自動的に制限内に切り詰める実装
def safe_string(text, max_length=100):
    return text[:max_length] if text else None

client.create_payment(
    comment=safe_string(long_comment, 100),
    name=safe_string(long_name, 100),
    place=safe_string(long_place, 100)
)
```

---

## 実用的な使用例

### 💡 残高計算の実装

```python
def calculate_balance_change(client, account_id, start_date, end_date):
    """指定期間の残高変動を計算"""
    transactions = client.get_money(
        start_date=start_date,
        end_date=end_date,
        limit=100
    )
    
    balance_change = 0
    for transaction in transactions['money']:
        if transaction['mode'] == 'income':
            if transaction.get('to_account_id') == account_id:
                balance_change += transaction['amount']
        elif transaction['mode'] == 'payment':
            if transaction.get('from_account_id') == account_id:
                balance_change -= transaction['amount']
        elif transaction['mode'] == 'transfer':
            if transaction.get('from_account_id') == account_id:
                balance_change -= transaction['amount']
            elif transaction.get('to_account_id') == account_id:
                balance_change += transaction['amount']
    
    return balance_change
```

### 📊 月次レポート生成

```python
def generate_monthly_report(client, year, month):
    """月次家計簿レポートを生成"""
    start_date = f"{year}-{month:02d}-01"
    end_date = f"{year}-{month:02d}-31"  # 簡易実装
    
    transactions = client.get_money(
        start_date=start_date,
        end_date=end_date,
        limit=100
    )
    
    report = {
        'income_total': 0,
        'payment_total': 0,
        'transfer_total': 0,
        'category_breakdown': {}
    }
    
    for trans in transactions['money']:
        amount = trans['amount']
        category_id = trans.get('category_id', 0)
        
        if trans['mode'] == 'income':
            report['income_total'] += amount
        elif trans['mode'] == 'payment':
            report['payment_total'] += amount
            report['category_breakdown'][category_id] = \
                report['category_breakdown'].get(category_id, 0) + amount
    
    return report
```

### 🔄 定期データ同期

```python
def sync_external_data(client, external_transactions):
    """外部システムからのデータ同期"""
    categories = client.get_categories()
    accounts = client.get_accounts()
    
    # マッピング辞書作成
    category_map = {c['name']: c['id'] for c in categories['categories']}
    account_map = {a['name']: a['id'] for a in accounts['accounts']}
    
    created_count = 0
    for ext_trans in external_transactions:
        try:
            # 外部データをZaim形式に変換
            zaim_data = {
                'category_id': category_map.get(ext_trans['category']),
                'amount': ext_trans['amount'],
                'date': ext_trans['date'],
                'comment': f"[外部連携] {ext_trans['description']}"
            }
            
            if ext_trans['type'] == 'expense':
                client.create_payment(**zaim_data)
            elif ext_trans['type'] == 'income':
                client.create_income(**zaim_data)
                
            created_count += 1
            
        except Exception as e:
            print(f"同期失敗: {ext_trans} - {e}")
    
    return created_count
```

---

## 🔗 関連リソース

### 公式リソース
- [Zaim Developers Center](https://dev.zaim.net/) - アプリケーション登録
- [Zaim API ドキュメント](https://dev.zaim.net/home/api) - API仕様詳細
- [OAuth 1.0a仕様](https://tools.ietf.org/html/rfc5849) - 認証プロトコル

### 認証関連エンドポイント
- **リクエストトークン取得**: `POST https://api.zaim.net/v2/auth/request`
- **ユーザー認証**: `GET https://auth.zaim.net/users/auth?oauth_token={token}`
- **アクセストークン取得**: `POST https://api.zaim.net/v2/auth/access`

### このプロジェクトのファイル
- `zaim_client/` - コアAPIクライアントライブラリ
- `zaim_cli/` - コマンドラインインターフェース
- `examples/basic_usage.py` - ライブラリ使用例
- `tests/` - 各種テストスクリプト
- `docs/` - API仕様とCLI使用方法

---

## ⚠️ 免責事項

- このドキュメントは非公式のものです
- Zaim APIの仕様変更により内容が古くなる可能性があります
- 実際の利用前は公式ドキュメントも併せて確認してください
- 本番環境での利用は自己責任でお願いします
