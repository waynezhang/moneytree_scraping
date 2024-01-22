#!/usr/bin/python
"""moneytree scraping
moneytreeで扱われているJSONをPythonで取得します。

tokenをJSONを扱うエンドポイントのヘッダーから取得します。
"Bearer ..." として書かれている部分をコピーして、
tokenという変数へ入力します。

# Usage

## import
from moneytree_scraping import Moneytree

## トークンの取得
1．開発者ツールをF12とかで開き、[ネットワーク]のタブを開く
1. ブラウザでmoneytreeの適当なページを開く(要ログイン)
1. 開発者ツールの[フィルター]に[transaction]と打ち込む
1. HeadersタブのRequest Headersの項目の中に、
    キーが[ Authorization :] で、Bearerから始まる文字列がある。
    これがBearerトークンで、認証に必要。

## トークンのセット
token = "Bearer以降の文字列コピペ。スペース入れない。"

またはbearer_tokenというファイルなどに
トークンの文字列(Bearerなし)を書き込んだ上で


```
with open("./bearer_token", mode="r", encoding="utf-8") as f:
    token = f.readline().replace("\n", "", -1).replace("Bearer ", "")
```


または
mt = Moneytree()
で対話形式で聞いてきます。

## 口座残高の取得

```python
mt = Moneytree(token)
account_balances = mt.get_account_balances()
print(json.dumps(account_balances, indent=4, ensure_ascii=False))
```

# JSONエンドポイントの種類
* /transactions.json: 明細
* /data_snapshot.json: アカウントのサブスクタイプや最後の口座情報が乗っている
"""
import json
from types import SimpleNamespace
from typing import Optional
from enum import Enum
import requests


class API(Enum):
    """Moneytree API
    ACCOUNT = "/accounts.json"
    ACCOUNT_BALANCES = "/web/presenter/account_balances.json"
    CATEGORY = "/presenter/categories.json"
    SNAPSHOT = "/web/presenter/guests/data_snapshot.json"
    SPENDING = "/web/presenter/spending.json"
    TRANSACTIONS = "/web/presenter/transactions.json"
    """
    # ペイロード(パラメータ)なし
    # 強いて言えば locate=ja だけは指定されていました。
    SNAPSHOT = "/web/presenter/guests/data_snapshot.json"
    """
    前回のログインセッションだろうか。パラメータが多すぎてなんと説明したら良いかわからない。
    以下にJSONで取得できた情報の型を記載します。

    .
    └── guest
        ├── id <int>
        ├── locale_identifier <string>
        ├── email <string>
        ├── unconfirmed_email <null>
        ├── uid <string>
        ├── confirmed_at <string>
        ├── confirmation_sent_at <string>
        ├── updated_at <string>
        ├── created_at <string>
        ├── base_currency <string>
        ├── subscription_level <string>
        ├── country <string>
        ├── payment_provider <null>
        ├── subscriptions [].
        │     ├── category <string>
        │     ├── subscription_level <string>
        │     ├── subscription_interval <null>
        │     ├── subscription_period_ends_at <null>
        │     ├── subscription_trial_expires_at <null>
        │     ├── payment_source <null>
        │     └── payment_provider <null>
        ├── institutions []null
        └── credentials [].
              ├── id <int>
              ├── last_success <string>
              ├── status_set_at <string>
              ├── institution_name <string>
              ├── institution_id <int>
              ├── auth_type <int>
              ├── status <string>
              ├── error_info
              │   ├── reason <string>
              │   ├── localized_reason <string>
              │   ├── localized_description <string>
              │   ├── url <null>
              │   ├── actionable <bool>
              │   └── input_fields []null
              ├── force_refreshable <bool>
              ├── foreground_refreshable <bool>
              ├── auto_run <bool>
              ├── uses_certificate <bool>
              ├── background_refresh_frequency <int>
              ├── institution
              │   └── id <int>
              └── accounts [].
                    ├── id <int>
                    ├── account_type <string>
                    ├── currency <string>
                    ├── institution_account_number <null>
                    ├── institution_account_name <string>
                    ├── branch_name <null>
                    ├── nickname <string>
                    ├── status <string>
                    ├── credential_id <int>
                    ├── sub_type <string>
                    ├── detail_type <string>
                    ├── group <string>
                    ├── current_balance <float>
                    └── current_balance_in_base <float>

          └── accounts [].
                ├── id <int>
                ├── account_type <string>
                ├── currency <string>
    このあたりで口座残高を取得できそうです。
    """

    CASHFLOW = "/web/presenter/cash-flow.json"
    """キャッシュフローを取得します。
    パラメータ泊、全年数に渡る支出と収入とその合計を算出します。
    ただし、カテゴリーは口座IDの形式で表示されますので、
    口座名を知るためにはaccounts.jsonと照会しなれけばなりません。。

    .
    └── cash_flow [].
          ├── month <string>
          ├── amount_in <float>
          ├── amount_out <float>
          ├── amount_total <float>
          └── categories
              ├── 88 <float>
              ├── 89 <float>
              ├── 90 <float>
              ├── 184186 <float>
              ├── 195532 <float>
              ├── 11 <float>
              ├── 12 <float>
              ├── 21 <float>
              ├── 27 <float>
              ├── 34 <float>
              ├── 35 <float>
              ├── 40 <float>
              ├── 46 <float>
              ├── 50 <float>
              ├── 52 <float>
              ├── 63 <float>
              ├── 71 <float>
              ├── 78 <float>
              ├── 160258 <float>
              └── 96 <float>
    """

    SPENDING = "/web/presenter/spending.json"
    """支出を取得します。
    日付形式はMM/DD/YYYYあるいはYYYY-MM-DD

    ```usage
    from datetime import datetime
    get_spending(
        start_date=datetime(2022, 1, 1).date().isoformat(),
        end_date=datetime(2022, 12, 31).date().isoformat(),
        group_by="monthly_period"  # or "yearly_period"
    )
    ```

    Params
    ---
    params = {
        "start_date": "01/01/2020",
        "end_date": "12/31/2022",
        "group_by": "monthly_period",
        "locale":"ja",
    }

    Returns
    ---
    .
    ├── start_date <string>
    ├── end_date <string>
    └── category_totals [].
          ├── start_date <string>
          ├── end_date <string>
          ├── total <float>
          └── categories
              ├── 9 <float>
              ├── 11 <float>
              ├── 12 <float>
              ├── 14 <float>
              ├── 15 <float>
              ├── 17 <float>
              ├── 24 <float>
              ├── 25 <float>
              ├── 27 <float>
              ├── 28 <float>
              ├── 31 <float>
              ├── 38 <float>
              ├── 40 <float>
              ├── 41 <float>
              ├── 42 <float>
              ├── 44 <float>
              ├── 46 <float>
              ├── 47 <float>
              ├── 49 <float>
              ├── 52 <float>
              ├── 53 <float>
              ├── 71 <float>
              ├── 73 <float>
              ├── 75 <float>
              ├── 76 <float>
              ├── 77 <float>
              └── 95 <float>

    カテゴリーはカテゴリIDが表示されているので、
    別途カテゴリーテーブルを参照する
    `get_categories()`により照会してください。
    """

    TRANSACTIONS = "/web/presenter/transactions.json"
    """トランザクション　入出金を取得します。

    ペイロード例
    params = {
        end_date: 06/30/2023
        exclude_corporate: true
        locale: ja
        show_spending_transactions: true
        show_transactions_details: true
        start_date: 06/01/2023
        transaction: {}
    }

    .
    ├── transactions [].
    │     ├── id <int>
    │     ├── amount <float>
    │     ├── date <string>
    │     ├── description_guest <null>
    │     ├── description_pretty <string>
    │     ├── description_raw <string>
    │     ├── raw_transaction_id <int>
    │     ├── created_at <string>
    │     ├── updated_at <string>
    │     ├── expense_type <int>
    │     ├── predicted_expense_type <int>
    │     ├── category_id <int>
    │     ├── account_id <int>
    │     ├── claim_id <null>
    │     ├── attachments []null
    │     ├── receipts []null
    │     └── attributes
    │         └── installment_count <int>
    └── transactions_details
        ├── page <int>
        ├── per_page <int>
        ├── start_date <string>
        └── end_date <string>
    """

    ACCOUNT_BALANCES = "/web/presenter/account_balances.json"
    """口座の残高を時系列で取得します。

    .
    └── account_balances [].
          ├── account_id <string>
          ├── account_type <string>
          ├── currency <string>
          ├── years []int
          └── monthly_balances [].
                ├── month <string>
                ├── balance <float>
                └── balance_in_base <null>

    """

    ACCOUNT = "/accounts.json"
    """口座テーブルを取得します。
    主に口座IDと口座名の照会に使います。
    アカウントのリストを取得します。
    アカウントIDは口座一つ一つに対応する7桁くらいの数字です。

    .
    └── accounts [].
          ├── id <int>
          ├── guest_id <int>
          ├── nickname <string>
          ├── currency <string>
          ├── credential_id <int>
          ├── account_type <string>
          ├── institution_account_number <string>
          ├── institution_account_name <string>
          ├── branch_name <null>
          ├── status <string>
          ├── last_success_at <string>
          ├── group <string>
          ├── detail_type <string>
          ├── sub_type <string>
          ├── current_balance <float>
          ├── current_balance_in_base <float>
          ├── current_unclosed_balance <float>
          ├── current_closed_balance <null>
          └── current_revolving_balance <float>

    id, nicknameのペアで口座名の特定ができる。
    institution_account_name は正式名称が出るようだが、
    複数の銀行の口座を持っていると、
    口座名がみんな"普通"になってしまうので、区別がつかなくなる。
    institutionは公共施設の意味。
    どこの銀行のなんの口座名かわかるようにnicknameを付ける必要がある。
    """

    CATEGORY = "/presenter/categories.json"
    """カテゴリテーブルを取得します。
    カテゴリIDとカテゴリ名の照会に使います。

    .
    └── categories [].
          ├── id <int>
          ├── parent_id <int>
          ├── guest_id <int>
          ├── category_type <string>
          ├── updated_at <string>
          ├── created_at <string>
          ├── entity_key <null>
          ├── name <string>
          ├── icon_key <string>
          ├── parent
          │   └── id <int>
          └── guest
              └── id <int>

    id, nameでカテゴリの照会ができます。
    """

    # AVAILABILITY =
    # """不明
    # url = "https://app.getmoneytree.com/static/data-availability.json"
    # """


class Response(requests.Response):
    """Custom Response Class

    # Usage:
        resp = requests.get(url=self.origin + api.value,
                            headers=self._header,
                            timeout=400,
                            params=params)
        custom_resp = Response()
        custom_resp.__dict__.update(resp.__dict__)
    """

    def __init__(self, resp: requests.Response):
        super().__init__()
        self.__dict__.update(resp.__dict__)

    def indented_json(self):
        """tab indent JSON"""
        return json.dumps(self.json(), indent=4, ensure_ascii=False)

    def object(self):
        """property accessable object"""
        return self.json(object_hook=lambda x: SimpleNamespace(**x))


class Moneytree:
    """Moneytree API"""
    origin = "https://jp-api.getmoneytree.com/v8/api"
    _header = {"Content-Type": "application/json"}

    def __init__(self, token: Optional[str] = None):
        if token is None:
            token = input("Input Bearer token (Without 'Bearer ' string): ")\
                .replace("\n", "").replace("Bearer ", "")  # 不要な文字列削除
        Moneytree._header.update({"Authorization": f"Bearer {token}"})
        self.categories = self.get(API.CATEGORY).object().categories
        self.category_table = {c.id: c.name for c in self.categories}
        self.accounts = self.get(API.ACCOUNT).object().accounts
        self.account_table = {a.id: a.nickname for a in self.accounts}

    def get(self,
            api: API,
            group_by="monthly_period",
            per_page=500,
            **params) -> Response:
        """get data from moneytree API"""
        # REQUIRE params
        if api == API.SPENDING:
            params.update({
                "start_date": params["start_date"],
                "end_date": params["end_date"],
                "group_by": group_by,
            })

        elif api == API.TRANSACTIONS:
            params.update({
                "start_date": params["start_date"],
                "end_date": params["end_date"],
                "per_page": per_page,
            })

        elif api == API.ACCOUNT_BALANCES:
            # アカウントIDは口座一つ一つに対応する7桁くらいの数字
            # account_ids はアカウントIDのリスト
            accounts_keys = [a.id for a in self.accounts]
            params.update({"account_ids[]": accounts_keys})

        # GET data from moneytree API
        resp = requests.get(url=self.origin + api.value,
                            headers=self._header,
                            timeout=400,
                            params=params)
        if resp.status_code == 401:
            raise requests.HTTPError("tokenの有効期限が切れました。Bearerトークンを再設定してください。")
        resp.raise_for_status()  # status_code 200番台以外のときにエラー
        # if prop_access:
        #     return resp.json(object_hook=lambda x: SimpleNamespace(**x))

        # success response
        custom_resp = Response(resp)
        return custom_resp

    # def inquiry_category(self, spending_dict: dict[str,
    #                                                float]) -> dict[str, float]:
    #     """ カテゴリIDをカテゴリ名に変換します。 """
    #     categories = self.get_categories()["categories"]
    #     category_table = {c["id"]: c["name"] for c in categories}
    #     new_category = {
    #         category_table[int(k)]: v
    #         for k, v in spending_dict.items()
    #     }
    #     return new_category

    def rename_category(self, spending):
        """get_spending()で取得できるJSONのcategory idをnameに変換します。
        usage:
            spending = get_spending(
                start_date="01/01/2023",
                end_date="06/30/2023",
                group_by="monthly_period",
                )
            renamed = rename_category(spending)

        # dev
            spending.rename_category()
        としたい

        そのためにはSpengingクラスを作るか。
        """
        for i, cat in enumerate(spending["category_totals"]):
            new_category = self.inquiry_category(cat["categories"])
            spending["category_totals"][i] = new_category
        return spending


if __name__ == "__main__":
    # json_data = get_transaction(
    #     end_date="06/30/2023",
    #     start_date="06/01/2023",
    #     per_page=500,  # 500より大きい数値を入れると400エラー
    # )
    # print(json.dumps(json_data, indent=4, ensure_ascii=False))
    # print(len(json_data["transactions"]))

    # login
    with open("./bearer_token", mode="r", encoding="utf-8") as f:
        token = f.readline().replace("\n", "", -1).replace("Bearer ", "")

    money = Moneytree(token)
    cashflow = money.get(API.CASHFLOW)
    # nomal JSON
    print(cashflow.json())

    # indented JSON
    print(cashflow.indented_json())

    # object JSON
    print(cashflow.object())
