from __future__ import annotations

from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException

from shared.moneywise_common import (
    AssetType,
    InvestmentPosition,
    InvestmentPositionCreateRequest,
    QuoteUpdateRequest,
    Settings,
    mean_return,
    portfolio_volatility,
    position_market_value,
    position_return_pct,
)

settings = Settings(service_name="investment-service", service_port=8405)
app = FastAPI(title="MoneyWise Investment Service", version="1.0.0")

positions: dict[str, InvestmentPosition] = {}


def _seed_demo() -> None:
    demo_positions = [
        InvestmentPosition(
            position_id="POS-DEMO-1",
            user_id="USR-DEMO",
            asset_type=AssetType.STOCK,
            ticker="SBER",
            quantity=120,
            average_price=265,
            current_price=291,
            currency="RUB",
        ),
        InvestmentPosition(
            position_id="POS-DEMO-2",
            user_id="USR-DEMO",
            asset_type=AssetType.BOND,
            ticker="OFZ26238",
            quantity=40,
            average_price=950,
            current_price=972,
            currency="RUB",
        ),
    ]
    for position in demo_positions:
        positions[position.position_id] = position


_seed_demo()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}


@app.post("/investments/positions")
async def create_position(request: InvestmentPositionCreateRequest) -> dict[str, Any]:
    position = InvestmentPosition(
        position_id=str(uuid4()),
        user_id=request.user_id,
        asset_type=request.asset_type,
        ticker=request.ticker.upper(),
        quantity=request.quantity,
        average_price=request.average_price,
        current_price=request.current_price,
        currency=request.currency,
    )
    positions[position.position_id] = position
    return position.model_dump(mode="json")


@app.get("/investments/positions")
async def list_positions(user_id: str | None = None) -> dict[str, Any]:
    items = []
    for position in positions.values():
        if user_id and position.user_id != user_id:
            continue
        payload = position.model_dump(mode="json")
        payload["market_value"] = position_market_value(position.quantity, position.current_price)
        payload["return_pct"] = position_return_pct(position.quantity, position.average_price, position.current_price)
        items.append(payload)
    return {"items": items, "count": len(items)}


@app.post("/investments/quotes")
async def update_quote(request: QuoteUpdateRequest) -> dict[str, Any]:
    matched = [position for position in positions.values() if position.ticker.upper() == request.ticker.upper()]
    if not matched:
        raise HTTPException(status_code=404, detail="Ticker not found in portfolio")
    for position in matched:
        position.current_price = request.current_price
    return {"updated": len(matched), "ticker": request.ticker.upper(), "current_price": request.current_price}


@app.get("/investments/portfolio/{user_id}")
async def portfolio(user_id: str) -> dict[str, Any]:
    user_positions = [position for position in positions.values() if position.user_id == user_id]
    items = []
    returns = []
    total_value = 0.0
    for position in user_positions:
        market_value = position_market_value(position.quantity, position.current_price)
        ret_pct = position_return_pct(position.quantity, position.average_price, position.current_price)
        returns.append(ret_pct)
        total_value += market_value
        items.append({
            **position.model_dump(mode="json"),
            "market_value": market_value,
            "return_pct": ret_pct,
        })

    return {
        "user_id": user_id,
        "items": items,
        "positions": len(items),
        "total_market_value": round(total_value, 2),
        "average_return_pct": mean_return(returns),
    }


@app.get("/investments/portfolio/{user_id}/risk")
async def risk_report(user_id: str) -> dict[str, Any]:
    user_positions = [position for position in positions.values() if position.user_id == user_id]
    returns = [position_return_pct(item.quantity, item.average_price, item.current_price) for item in user_positions]
    volatility = portfolio_volatility(returns)
    risk_level = "low"
    if volatility >= 9:
        risk_level = "high"
    elif volatility >= 4:
        risk_level = "medium"

    stock_share = 0.0
    total_value = 0.0
    for item in user_positions:
        value = position_market_value(item.quantity, item.current_price)
        total_value += value
        if item.asset_type == AssetType.STOCK:
            stock_share += value
    stock_share_pct = round((stock_share / total_value) * 100, 2) if total_value else 0.0

    return {
        "user_id": user_id,
        "volatility": volatility,
        "risk_level": risk_level,
        "stock_share_pct": stock_share_pct,
        "recommendation": "Increase bonds and cash share" if risk_level == "high" else "Risk profile is balanced",
    }


@app.post("/investments/broker/connect")
async def connect_broker(user_id: str, broker_name: str) -> dict[str, Any]:
    return {
        "status": "connected",
        "user_id": user_id,
        "broker_name": broker_name,
        "synced_positions": len([item for item in positions.values() if item.user_id == user_id]),
    }
