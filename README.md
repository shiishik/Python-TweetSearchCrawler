# Twitter search APIクローラー
Twitterの公式search APIを使い、特定のキーワードを含むtweetをクロールするPythonのスクリプトです。
データはSQLiteに保存します。
## 使い方
### 準備
Twitter Developerにアカウント登録し、 API key/API secret key/Access token/Access token secret を発行します。
コードの CONSUMER_KEY/CONSUMER_SECRET_KEY/ACCESS_TOKEN/ACCESS_TOKEN_SECRET に発行した各値を入れます。
### クロール実行
`
$ python tweet_search_crowler.py  --query 'yahooooo' --dbpath 'yahooooo.db'
`
