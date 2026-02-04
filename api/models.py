from pydantic import BaseModel, Field
from typing import Optional, List, Dict


class PredictionRequest(BaseModel):
    marketCap: float
    volume: float
    numHolders: int
    volatility: float
    sniperCount: Optional[int] = 0
    progress: Optional[float] = 0.0
    buySellRatio: Optional[float] = 0.0
    liquidity: Optional[float] = 0.0


class PredictionResponse(BaseModel):
    prediction: str  # "BUY" nebo "NO BUY"
    confidence: float = Field(ge=0.0, le=1.0)
    features: Dict[str, float]


class SimulationTick(BaseModel):
    timestamp: str
    symbol: str
    marketCap: float
    prediction: str
    confidence: float
    features: Dict[str, float]


class TokenInfo(BaseModel):
    symbol: str
    name: str
    data_points: int
    mint: str


class TokenListResponse(BaseModel):
    tokens: List[TokenInfo]


class TokenDetailResponse(BaseModel):
    mint: str
    name: str
    symbol: str
    volume: float
    numHolders: int
    data_points: int
    time_start: Optional[str] = None
    time_end: Optional[str] = None
