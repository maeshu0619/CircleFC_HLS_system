HLSを用いたフォビエイテッド圧縮ビデオストリーミングシステム
概要
本システムは、HLS（HTTP Live Streaming）とフォビエイテッド圧縮技術を活用し、視線情報に基づいた適応型ストリーミングを実現します。この技術により、帯域幅を効果的に節約しながら、視聴者に高品質な動画体験を提供します。また、ネットワーク環境を動的に制御することで、さまざまな条件下でのQoS（Quality of Service）を評価するフレームワークも提供します。

システム構成
本システムは以下のステップで構成されています：

・H.264圧縮
・入力動画をH.264圧縮を用いて、低解像度（640×360）、中解像度（1280×720）、高解像度（1920×1080）の3つに変換します。

・視線予測
・視線予測アルゴリズムを用いて、視聴者の注視点をリアルタイムで推定します。

・フレーム統合
・解像度の異なる動画フレームを同心円状に結合し、視線中心部は高解像度、周辺部は低解像度のフォビエイテッドフレームを生成します。

・HLSストリーミング
・フォビエイテッド動画をHLS形式に変換し、master.m3u8を生成して全体を統括します。

・ネットワーク制限
・帯域幅、遅延、パケット損失などを動的に制御する機能を提供し、異なるネットワーク条件下でのストリーミング挙動を観測します。

・QoS評価（未実装）
・今後のアップデートでQoS（Quality of Service）指標に基づく詳細な評価機能を追加予定です。

ファイル構成
以下は、システムの主要ファイルとその役割です：

・main.py
・システム全体のエントリーポイントです。以下のプロセスを実行します：
・ネットワーク設定
・H.264圧縮の実行
・MP4セグメントの生成
・HLSファイルの作成と削除選択
・ビデオストリーミングとネットワークモニタリング

・main_system.py
・各プロセスをモジュールとして管理します。ネットワーク制御、H.264圧縮、HLSストリーミングを担当します。

・directry_structure.py
・ディレクトリ構造を視覚化し、必要なフォルダの作成を補助します。

・server_function.py & hls_server.py
・フレーム数計算
・HLSファイルおよびセグメント生成

・client_operator.py
・視線予測やQoSモニタリングを制御します。

