# 音と光のインタラクティブ環境 (Light and Sound Interactive Environment)

重症心身障害児・多肢不自由児をはじめとする子どもたちが、身体の動き（iPadの傾きや触覚）を通じて、美しく心地よい光の流れと澄んだ音の響き（Cause & Effect）を直感的・身体的・情緒的に実感できるインタラクティブWebアプリケーションです。

---

## 主な機能・特徴

- **流体物理エンジン**: 3オクターブ多重 Fractal Curl Noise (FBM) と粒子間反発による自然で滑らかな光の遊泳。
- **3階層流体音響エンジン**:
  - **Macro**: 流速連動ストリームノイズ ＆ 呼吸する低音ドローン（動的エンベロープ）
  - **Meso**: 粒子の重心・速度に追従する Granular せせらぎ音
  - **Micro**: 急加速・渦突入などの高エネルギー時に響く Modal 結晶ベル（ペンタトニック調和音階）
- **スイッチインターフェース対応 (支援技術)**:
  - **Spaceキー** で右に傾ける、**Enterキー** で左に傾ける操作に対応（Bluetoothスイッチやキーボードで操作可能）。
  - 長押し連動に加え、単押し（一瞬のタップ）でも一定時間心地よく流れる **Hybridパルス維持モード** を搭載。
- **プロジェクター投影最適化**: 会議室・プレゼン用プロジェクターの黒浮き・白飛び・ディテール消失を補正する高彩度・輪郭ブーストモード。
- **iPad / PWA 完全全画面対応**: ホーム画面に追加（Standalone）または手動全画面（⛶）による額縁のない没入体験。
- **ゼロ依存アーキテクチャ**: 外部ライブラリを一切使わず Vanilla HTML5 Canvas 2D + Web Audio API のみで高速・安定動作。

---

## 公開URL (GitHub Pages)

iPadや各種端末のブラウザ（Safari等）からアクセスしてすぐに体験できます：

👉 **[https://yamaguchitoshi.github.io/lightandsound/](https://yamaguchitoshi.github.io/lightandsound/)**

※ 正規HTTPS環境のため、証明書警告なしでそのまま傾斜センサー・Web Audio・PWA（ホーム画面に追加）が利用できます。

---

## 起動方法 (ローカル開発時)

### ローカルHTTPSサーバーの起動 (ローカル検証用)

```bash
# Python 3 によるローカルHTTPSサーバー起動 (ポート 8443)
python3 serve_https.py 8443
```

### iPadでのアクセスと全画面化

1. iPadのSafariで `https://yamaguchitoshi.github.io/lightandsound/`（またはローカルIP）にアクセスします。
2. 画面中央の **「画面に触れてスタート」** をタップ（またはスイッチでSpace/Enterを押下）。
3. **完全全画面（アドレスバーなし）にする場合**:
   - Safariの共有メニュー（􀈂）から **「ホーム画面に追加」** を選択し、作成されたアイコンから起動します。

---

## ドキュメント

- [開発・技術仕様 統合ドキュメント (DOCUMENTATION.md)](DOCUMENTATION.md)
- [視覚・流体物理 リサーチレポート (deep-research-report-1.md)](deep-research-report-1.md)
- [音響・知覚工学 リサーチレポート (deep-research-report-2.md)](deep-research-report-2.md)
