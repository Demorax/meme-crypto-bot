import asyncio
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from functools import partial
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from .models import PredictionRequest, PredictionResponse, TokenListResponse, TokenDetailResponse
from .predictor import CryptoPredictor, DataLoader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AppState:
    predictor: CryptoPredictor = None
    data_loader: DataLoader = None


app_state = AppState()
executor = ThreadPoolExecutor(max_workers=4)


async def run_sync(func, *args):
    """Wrapper pro sync funkce - Python 3.8 kompatibilita."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, partial(func, *args))


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Loading model and data...")
    try:
        app_state.predictor = CryptoPredictor()
        app_state.data_loader = DataLoader()
        logger.info("Model and data loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load: {e}")
        raise
    yield
    executor.shutdown(wait=False)
    logger.info("Shutting down...")


app = FastAPI(
    title="Crypto Prediction API",
    description="API for predicting buy/sell signals on cryptocurrencies",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_predictor() -> CryptoPredictor:
    if app_state.predictor is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    return app_state.predictor


def get_data_loader() -> DataLoader:
    if app_state.data_loader is None:
        raise HTTPException(status_code=503, detail="Data not loaded")
    return app_state.data_loader


@app.get("/")
async def health_check():
    return {
        "status": "ok",
        "model_loaded": app_state.predictor is not None,
        "data_loaded": app_state.data_loader is not None
    }


@app.get("/tokens", response_model=TokenListResponse)
async def get_tokens(data_loader: DataLoader = Depends(get_data_loader)):
    tokens = data_loader.get_tokens()
    return TokenListResponse(tokens=tokens)


@app.post("/predict", response_model=PredictionResponse)
async def predict(
    request: PredictionRequest,
    predictor: CryptoPredictor = Depends(get_predictor)
):
    # TODO: tady by se mohly počítat features z historie, ne jen z jednoho bodu
    features = {
        "marketCap_change": 0.0,
        "marketCap_ema": request.marketCap,
        "rsi": 50.0,
        "marketCap_change_ratio": 0.0,
        "holders_growth": 0.0,
        "volatility_to_volume_ratio": request.volatility / (request.volume + 1)
    }

    prediction, confidence = predictor.predict(features)

    return PredictionResponse(
        prediction=prediction,
        confidence=confidence,
        features=features
    )


async def simulation_generator(
    mint: str,
    speed: float,
    predictor: CryptoPredictor,
    data_loader: DataLoader
) -> AsyncGenerator[str, None]:
    """SSE stream pro simulaci predikcí."""
    try:
        df = await run_sync(data_loader.get_token_data, mint)
        symbol = df['symbol'].iloc[0]
        df_with_features = await run_sync(predictor.compute_features, df, symbol)

        delay = max(0.05, 1.0 / speed)

        for _, row in df_with_features.iterrows():
            features = {f: row.get(f, 0.0) for f in predictor.FEATURES}
            prediction, confidence = predictor.predict(features)

            timestamp = row['timestamp']
            ts_str = timestamp.isoformat() if hasattr(timestamp, 'isoformat') else str(timestamp)

            tick = {
                "timestamp": ts_str,
                "symbol": row['symbol'],
                "marketCap": float(row['marketCap']),
                "prediction": prediction,
                "confidence": round(confidence, 4),
                "features": {k: round(float(v), 6) for k, v in features.items()}
            }

            yield f"data: {json.dumps(tick)}\n\n"
            await asyncio.sleep(delay)

        yield f"data: {json.dumps({'done': True})}\n\n"

    except Exception as e:
        logger.error(f"Simulation error: {e}")
        yield f"data: {json.dumps({'error': str(e)})}\n\n"


@app.get("/simulate")
async def simulate(
    mint: str = Query(..., description="Token mint address"),
    speed: float = Query(1.0, ge=0.1, le=100.0),
    predictor: CryptoPredictor = Depends(get_predictor),
    data_loader: DataLoader = Depends(get_data_loader)
):
    """SSE endpoint pro real-time simulaci."""
    if mint not in data_loader.data:
        raise HTTPException(status_code=404, detail=f"Token {mint} not found")

    return StreamingResponse(
        simulation_generator(mint, speed, predictor, data_loader),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@app.get("/token/{mint}", response_model=TokenDetailResponse)
async def get_token_details(
    mint: str,
    data_loader: DataLoader = Depends(get_data_loader)
):
    if mint not in data_loader.data:
        raise HTTPException(status_code=404, detail=f"Token {mint} not found")

    token = data_loader.data[mint]
    df = await run_sync(data_loader.get_token_data, mint)

    time_start = None
    time_end = None
    if not df.empty:
        ts_min = df['timestamp'].min()
        ts_max = df['timestamp'].max()
        if hasattr(ts_min, 'isoformat'):
            time_start = ts_min.isoformat()
            time_end = ts_max.isoformat()

    return TokenDetailResponse(
        mint=mint,
        name=token.get("name", "Unknown"),
        symbol=token.get("symbol", "Unknown"),
        volume=token.get("volume", 0),
        numHolders=token.get("numHolders", 0),
        data_points=len(df),
        time_start=time_start,
        time_end=time_end
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
