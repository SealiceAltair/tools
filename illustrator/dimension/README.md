# 寸法v0.3.5

Adobe Illustrator上で、選択したオブジェクトに寸法線を作成するCEP拡張です。

- 作成者: SealiceAltair
- バージョン: v0.3.5
- 対応環境: Adobe Illustrator / Windows / CEP拡張
- 拡張ID: `com.chappy.dimension_v0_3`

## ダウンロード

[最新版のZIPを直接ダウンロード](https://raw.githubusercontent.com/SealiceAltair/tools/main/illustrator/dimension/chappy-illustrator-dimension.zip)

## v0.3.5の変更

- 手動で寸法線の長さを変えた後、数値を再計算して新しい線の中央へ自動配置します。
- 横寸法はX方向、縦寸法はY方向だけを中央へ戻し、文字と線の隙間を維持します。
- 通常寸法、連立寸法、内包寸法へ共通対応しました。
- 更新ボタンを「選択寸法の数値・位置を更新」へ変更しました。

## 主な機能

- 上・下・左・右の寸法線を作成
- スケール表記
- 下層レイヤー検知と内包寸法検知による連立寸法
- スケール、拡大率、フォント、端数処理の設定
- 手動調整後の寸法値更新と自動センタリング

## 使い方

ZIPを展開し、`com.chappy.dimension_v0_3` フォルダを次の場所へコピーします。

```text
%APPDATA%\Adobe\CEP\extensions
```

Illustratorを再起動し、`ウィンドウ > エクステンション（従来） > 寸法v0.3.5` から開きます。

詳しい操作方法は、ZIPに同梱している `使用方法ガイド.pdf` を参照してください。
