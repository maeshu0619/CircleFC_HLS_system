・browser_launcher.py
　・Chromeブラウザを起動し、指定されたURLを開く機能を提供します。
　・open_chrome関数を使用してブラウザを開きます。
　・close_live_stream_tabs関数を利用して、特定のタブを自動で閉じることも可能です​。
 
 ・hls_client.py
　・HLSファイルを提供するHTTPサーバーを起動します。
　・ストリーミングの進行状況をリアルタイムでログに記録する機能を備えています。
　・サーバーの停止にはCtrl+Cを使用します​。

・client_operator.py
　・クライアントでのHLS再生を管理します。
　・指定された期間再生を行い、サーバーとのデータ同期を行います​。
