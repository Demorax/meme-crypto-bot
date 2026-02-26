# Crypto Meme Coins Bot

ML bot pro obchodování meme coinů postavený na XGBoost. Zkouší identifikovat nákupní/prodejní příležitosti na základě tržních dat a technických indikátorů.

Zaměřuje se na meme coiny (DOGE, SHIB, PEPE a podobné) - ty jsou sice extrémně volatilní, ale zároveň tím pádem nejzajímavější pro ML experimenty.

## Proč XGBoost?

Začínal jsem s neuronovou sítí, ale narazil jsem na dva problémy:
- Data meme coinů nejsou dostatečně "složitá" na to, aby neuronky přidaly hodnotu
- XGBoost na tomhle datasetu prostě funguje lépe a je interpretovatelný

Neuronka skončila s průměrnou precizí kolem 0.17, XGBoost dává 0.19. Není to obrovský rozdíl, ale je konzistentní.

---

## PyTorch Experiment

Reimplementace buy modelu v PyTorchi - hlavně jako cvičení frameworku.

### Výsledky (TimeSeriesSplit)

| Metrika | XGBoost | PyTorch |
|---------|---------|---------|
| Average Precision | 0.193 | 0.168 |
| F1 Score (Buy) | 0.44 | 0.29 |
| Recall (Buy) | 0.52 | 0.24 |
| Precision (Buy) | 0.38 | 0.35 |

XGBoost vede. PyTorch notebook je v `pytorch.ipynb`.

Směry zlepšení které jsem ještě nezkoušel: Focal Loss, class weights, jiná labelovací strategie.

---

## Web App (FastAPI + Streamlit)

Jednoduchá webovka pro vizualizaci predikcí v reálném čase.

### Screenshots

![Dashboard - simulace běží](docs/images/frontend_1.png)

![Dashboard - detail predikcí](docs/images/frontend_2.png)

### Spuštění

```bash
pip install -r requirements.txt
```

Backend:
```bash
uvicorn api.main:app --reload --port 8000
```

Frontend (druhý terminál):
```bash
streamlit run frontend/app.py
```

Frontend: http://localhost:8501 | API docs: http://localhost:8000/docs

### Endpointy

| Endpoint | Popis |
|----------|-------|
| `GET /` | Health check |
| `POST /predict` | Predikce pro jeden vzorek |
| `GET /simulate` | SSE stream simulace |
| `GET /tokens` | Seznam tokenů |
| `GET /token/{mint}` | Detail tokenu |

---

## Upozornění

Tohle je proof of concept pro učení, **ne finanční poradenství**. Minulá výkonnost nezaručuje nic.
