# Crypto meme coins bot using  XGboost
## Overview
This project is a machine learning-based trading bot that leverages XGBoost, a powerful gradient boosting algorithm, 
to identify potential buy/sell opportunities in meme coins based on market trends and technical indicators.

Cryptocurrencies can generally be categorized into three market cap tiers:

 - Large-cap coins (e.g., BTC, ETH) – Established, lower volatility.
 - Mid-cap coins – Emerging projects with moderate risk and reward.
 - Meme coins & small-cap coins (e.g., DOGE, SHIB, PEPE) – High volatility, speculative, and often driven by community hype.

This bot focuses on meme coins and applies machine learning to identify potential sell signals based on market fluctuations, technical indicators, and past trends.


## Why XGBoost?
Initially, I experimented with a neural network to predict buy and sell opportunities. However, I encountered two key challenges:
 - The dataset wasn't "hard enough" – Meme coin price movements are highly volatile but often follow simpler patterns that do not require deep learning.
 - Neural networks struggled to find clear patterns – The network failed to consistently recognize buy/sell signals, 
likely due to the lack of deep feature interactions needed to justify a complex model.

## ⚠️ Disclaimer

This project is a **proof of concept** and is intended for **educational and research purposes only**.  
It **does not constitute financial advice**, investment recommendations, or trading signals.  
Past performance is **not** indicative of future results.  

**Use this project at your own risk.**
