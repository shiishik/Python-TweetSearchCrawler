# Twitter search APIクローラー
Twitterの公式search APIを使い、特定のキーワードを含むtweetをクロールするPythonのスクリプト。  
データは指定のパスにSQLiteのDBがあればそこに追加保存、無ければ新たにDBを生成して保存する。  
クロールはAPIから取得可能な7日分取得し終わるまで実施する。  
## 使い方
### 準備
Twitter Developerにアカウント登録し、 API key/API secret key/Access token/Access token secret を発行する。  
コードの CONSUMER_KEY/CONSUMER_SECRET_KEY/ACCESS_TOKEN/ACCESS_TOKEN_SECRET に発行した各値を入れておく。  
### クロール実行
7日分取得
`
$ python tweet_search_crowler.py  --query 'yahooooo' --dbpath 'yahooooo.db'
`
### クロール確認
DB保存せず、取得データの表示のみ
`
$ python tweet_search_crowler.py  --query 'yahooooo' --dbpath 'yahooooo.db' --debug-mode true
`
