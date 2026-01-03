# Crypto Meme Coins Bot s XGBoost

## Přehled
Tento projekt je obchodní bot založený na strojovém učení, který využívá XGBoost, výkonný algoritmus gradientního boostingu,
k identifikaci potenciálních příležitostí k nákupu/prodeji meme coinů na základě tržních trendů a technických indikátorů.

Kryptoměny lze obecně rozdělit do tří kategorií podle tržní kapitalizace:

- **Large-cap coiny** (např. BTC, ETH) – Zavedené, nižší volatilita.
- **Mid-cap coiny** – Vznikající projekty se střední mírou rizika a výnosů.
- **Meme coiny & small-cap coiny** (např. DOGE, SHIB, PEPE) – Vysoká volatilita, spekulativní a často řízené komunitním hype.

Tento bot se zaměřuje na meme coiny a aplikuje strojové učení k identifikaci potenciálních signálů k prodeji/nákupu na základě kolísání trhu, technických indikátorů a minulých trendů.

## Proč XGBoost?
Zpočátku jsem experimentoval s neuronovou sítí pro predikci příležitostí k nákupu a prodeji. Nicméně jsem narazil na dva klíčové problémy:
- **Dataset nebyl dostatečně "obtížný"** – Pohyby cen meme coinů jsou sice velmi volatilní, ale často sledují jednodušší vzory, které nevyžadují hluboké učení.
- **Neuronové sítě měly problémy najít jasné vzory** – Síť nedokázala konzistentně rozpoznat signály k nákupu/prodeji,
pravděpodobně kvůli nedostatku hlubokých interakcí mezi features, které by odůvodnily složitější model.

## ️ Upozornění

Tento projekt je **proof of concept** a je určen **pouze pro vzdělávací a výzkumné účely**.
**Nejedná se o finanční poradenství**, investiční doporučení nebo obchodní signály.
Minulá výkonnost **není** indikací budoucích výsledků.

**Používejte tento projekt na vlastní riziko.**
