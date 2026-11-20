#!/usr/bin/env python3
"""Atualiza o cache diário de OHLC via Alpha Vantage, sem expor a chave no site."""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "market-data.json"
API_URL = "https://www.alphavantage.co/query"

# Os tickers do painel são consultados no formato brasileiro .SA (não .SAO).
STOCKS = [
    "SBSP3", "BBSE3", "ISAE4", "EGIE3", "PETR4", "VALE3", "BBAS3",
    "BBDC4", "ITUB4", "ITSA4", "AXIA3", "WEGE3", "SUZB3", "B3SA3",
    "PRIO3", "BPAC11", "GGBR4",
]

EMPTY_DATA: dict[str, Any] = {
    "source": "Alpha Vantage",
    "updated_at": None,
    "assets": {},
    "asset_status": {},
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def load_data() -> dict[str, Any]:
    if not DATA_FILE.exists():
        return json.loads(json.dumps(EMPTY_DATA))
    try:
        existing = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError("O arquivo data/market-data.json está ilegível; não vou sobrescrevê-lo.") from exc
    if not isinstance(existing, dict):
        raise RuntimeError("Formato inesperado em data/market-data.json.")
    existing.setdefault("assets", {})
    existing.setdefault("asset_status", {})
    existing.setdefault("source", "Alpha Vantage")
    return existing


def fetch_json(params: dict[str, str]) -> dict[str, Any]:
    query = urlencode(params)
    request = Request(
        f"{API_URL}?{query}",
        headers={"User-Agent": "painel-alertas-bitcoin-opcoes/1.0"},
    )
    # Não imprimir a URL ou a exceção bruta: ambas podem conter a chave da API.
    try:
        with urlopen(request, timeout=35) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:  # erro de rede/HTTP/JSON, sem vazar URL ou chave
        raise RuntimeError(f"Falha de rede ou resposta inválida ({type(exc).__name__}).") from None
    if not isinstance(payload, dict):
        raise RuntimeError("Resposta inesperada da API.")
    for key in ("Error Message", "Note", "Information"):
        if key in payload:
            message = str(payload[key]).lower()
            if "rate" in message or "call frequency" in message or "requests per day" in message:
                raise RuntimeError("Limite de consultas da Alpha Vantage atingido; dados anteriores preservados.")
            if key == "Error Message":
                raise RuntimeError("A API rejeitou a consulta; verifique o símbolo e a disponibilidade do ativo.")
            raise RuntimeError("A API não entregou a série solicitada; dados anteriores preservados.")
    return payload


def as_float(row: dict[str, Any], candidates: tuple[str, ...]) -> float:
    for key in candidates:
        if key in row:
            value = float(row[key])
            if math.isfinite(value) and value > 0:
                return value
            break
    raise ValueError("Campo OHLC ausente ou inválido.")


def parse_stock(payload: dict[str, Any]) -> list[list[Any]]:
    series = payload.get("Time Series (Daily)")
    if not isinstance(series, dict):
        raise RuntimeError("A API não retornou 'Time Series (Daily)'.")
    rows: list[list[Any]] = []
    for day, values in series.items():
        if not isinstance(values, dict):
            continue
        try:
            row = [day,
                   as_float(values, ("1. open",)),
                   as_float(values, ("2. high",)),
                   as_float(values, ("3. low",)),
                   as_float(values, ("4. close",))]
        except (ValueError, TypeError):
            continue
        rows.append(row)
    if not rows:
        raise RuntimeError("A série diária veio vazia ou sem candles OHLC válidos.")
    return sorted(rows, key=lambda item: item[0])


def parse_crypto(payload: dict[str, Any]) -> list[list[Any]]:
    series = payload.get("Time Series (Digital Currency Daily)")
    if not isinstance(series, dict):
        raise RuntimeError("A API não retornou 'Time Series (Digital Currency Daily)'.")
    rows: list[list[Any]] = []
    for day, values in series.items():
        if not isinstance(values, dict):
            continue
        try:
            row = [day,
                   as_float(values, ("1a. open (USD)", "1b. open (USD)", "1. open")),
                   as_float(values, ("2a. high (USD)", "2b. high (USD)", "2. high")),
                   as_float(values, ("3a. low (USD)", "3b. low (USD)", "3. low")),
                   as_float(values, ("4a. close (USD)", "4b. close (USD)", "4. close"))]
        except (ValueError, TypeError):
            continue
        rows.append(row)
    if not rows:
        raise RuntimeError("A série diária do Bitcoin veio vazia ou sem candles OHLC válidos.")
    return sorted(rows, key=lambda item: item[0])


def merge_rows(existing: list[list[Any]], incoming: list[list[Any]]) -> tuple[list[list[Any]], int]:
    # Atualiza datas repetidas também: isso corrige candles do último pregão
    # que possam ter sido publicados inicialmente antes da revisão final.
    by_date = {row[0]: row for row in existing if isinstance(row, list) and len(row) == 5}
    changed = 0
    for row in incoming:
        if by_date.get(row[0]) != row:
            by_date[row[0]] = row
            changed += 1
    merged = [by_date[day] for day in sorted(by_date)]
    return merged, changed


def request_asset(symbol: str, api_key: str) -> list[list[Any]]:
    if symbol == "BTC":
        payload = fetch_json({
            "function": "DIGITAL_CURRENCY_DAILY",
            "symbol": "BTC",
            "market": "USD",
            "apikey": api_key,
        })
        return parse_crypto(payload)
    payload = fetch_json({
        "function": "TIME_SERIES_DAILY",
        "symbol": f"{symbol}.SA",
        "outputsize": "compact",
        "apikey": api_key,
    })
    return parse_stock(payload)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scope", choices=("stocks", "btc", "all"), default="all")
    args = parser.parse_args()

    api_key = os.environ.get("ALPHA_VANTAGE_API_KEY", "").strip()
    if not api_key:
        print("ERRO: configure o Secret ALPHA_VANTAGE_API_KEY no GitHub.", file=sys.stderr)
        return 2

    data = load_data()
    assets: dict[str, list[list[Any]]] = data["assets"]
    statuses: dict[str, dict[str, Any]] = data["asset_status"]
    symbols = STOCKS if args.scope == "stocks" else ["BTC"] if args.scope == "btc" else STOCKS + ["BTC"]

    successes = 0
    failures = 0
    for index, symbol in enumerate(symbols):
        try:
            rows = request_asset(symbol, api_key)
            merged, changed = merge_rows(assets.get(symbol, []), rows)
            assets[symbol] = merged
            statuses[symbol] = {
                "status": "ok",
                "last_attempt": utc_now(),
                "last_success": utc_now(),
                "latest_date": merged[-1][0] if merged else None,
                "rows_received": len(rows),
                "rows_changed": changed,
                "message": "",
            }
            successes += 1
            print(f"OK {symbol}: {len(rows)} candles consultados; {changed} datas novas ou revisadas; último candle {merged[-1][0]}.")
        except RuntimeError as exc:
            previous = statuses.get(symbol, {})
            statuses[symbol] = {
                **previous,
                "status": "error",
                "last_attempt": utc_now(),
                "latest_date": assets.get(symbol, [])[-1][0] if assets.get(symbol) else previous.get("latest_date"),
                "message": str(exc),
            }
            failures += 1
            print(f"FALHA {symbol}: {exc}")
        # A franquia gratuita é limitada por dia e também por frequência.
        # 13 segundos entre chamadas mantém o ritmo abaixo de 5 consultas/minuto.
        if index < len(symbols) - 1:
            time.sleep(13)

    data["updated_at"] = utc_now()
    data["last_scope"] = args.scope
    data["last_run"] = {"successes": successes, "failures": failures, "requested": len(symbols)}
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"Resumo: {successes} sucesso(s), {failures} falha(s), {len(symbols)} consulta(s).")
    # Erros parciais não apagam nem bloqueiam a publicação dos ativos bem-sucedidos.
    return 0 if successes else 1


if __name__ == "__main__":
    raise SystemExit(main())
