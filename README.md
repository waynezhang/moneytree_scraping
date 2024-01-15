# トークンの取得
1．開発者ツールをF12とかで開き、[ネットワーク]のタブを開く
1. ブラウザでmoneytreeの適当なページを開く(要ログイン)
1. 開発者ツールの[フィルター]に[transaction]と打ち込む
1. HeadersタブのRequest Headersの項目の中に、キーが[ Authorization :] で、Bearerから始まる文字列がある。これがBearerトークンで、認証に必要。


# 認証

` requests.session() `でセッションを獲得。

```python
session = requests.session()
with open("./bearer_token", mode="r", encoding="utf-8") as f:
    token = f.read()
token = token.replace("\n", "", -1)
session.headers = {"Authorization": token}
```


# 取引情報


取得する情報に基づいたURLとGETパラメータを用意します。
以下は取引履歴(transaction.json)へアクセスし、2023年6月の取引をすべて取得するURLです。

```python
url = "https://jp-api.getmoneytree.com/v8/api/web/presenter/transactions.json"
params = {
    "end_date": "06/30/2023",
    "start_date": "06/01/2023",
    # show_transactions_details="true",
    # show_transaction = "true"とすることで以下の項目が見える
    #   "show_transactions_details": true,
    #   "transactions_count": 0,
    #   "transactions_total": 0.0
}
```

URLとパラメータが準備できたら、`session.get()`でJSONを受けます。
`json.dumps()`で任意の表示でJSONを出力します。

```python
# GETでJSONを取得します。
resp = session.get(url, params=params)

# JSONとして表示します。
json_data = resp.json()
print(json.dumps(json_data, indent=4, ensure_ascii=False))
```
