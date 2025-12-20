from __future__ import annotations
from dataclasses import dataclass
from typing import Literal, Optional

# Для совместимости:
# - старые значения: "USN6", "USN15", "NPD", "CUSTOM"
# - новые режимы: "REV" (налог с выручки), "PROFIT" (налог с прибыли)
TaxMode = Literal["REV", "PROFIT", "USN6", "USN15", "NPD", "CUSTOM"]
AdsMode = Literal["PER_SALE", "DRR"]
CommissionMode = Literal["PCT", "RUB"]


@dataclass
class CalcInputs:
    price: float
    cogs: float
    commission_mode: CommissionMode
    commission_value: float   # pct as fraction (0.18) or rub
    logistics: float
    storage: float
    returns_pct: float        # 0..1
    return_cost: float
    ads_mode: AdsMode
    ads_value: float          # rub per sale OR drr fraction
    other_fees: float
    opex_var: float
    tax_mode: TaxMode
    tax_rate: float           # fraction


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _core_compute(inputs: CalcInputs) -> dict:
    P = inputs.price
    C = inputs.cogs

    # Комиссия
    if inputs.commission_mode == "PCT":
        K = P * inputs.commission_value
    else:
        K = inputs.commission_value

    # Реклама
    if inputs.ads_mode == "PER_SALE":
        A = inputs.ads_value
        DRR = (A / P) if P > 0 else 0.0
    else:
        A = P * inputs.ads_value
        DRR = inputs.ads_value

    L = inputs.logistics
    S = inputs.storage
    F_other = inputs.other_fees
    Opex = inputs.opex_var

    # Возвраты — ожидаемый расход на 1 продажу
    ret_rate = _clamp(inputs.returns_pct, 0.0, 1.0)
    Ret = ret_rate * inputs.return_cost

    profit_before_tax = P - (C + K + L + S + A + F_other + Ret + Opex)

    # Режим налога:
    # REV / USN6 / NPD / CUSTOM — с выручки
    # PROFIT / USN15           — с прибыли
    if inputs.tax_mode in ("REV", "USN6", "NPD", "CUSTOM"):
        tax_base = max(0.0, P)
    elif inputs.tax_mode in ("PROFIT", "USN15"):
        tax_base = max(0.0, profit_before_tax)
    else:
        tax_base = max(0.0, P)

    tax = tax_base * inputs.tax_rate
    net_profit = profit_before_tax - tax
    margin_pct = (net_profit / P) if P > 0 else 0.0

    # Макс. допустимая реклама, чтобы net_profit >= 0
    fixed_costs = C + L + S + F_other + Ret + Opex
    if inputs.commission_mode == "PCT":
        fixed_costs += P * inputs.commission_value
    else:
        fixed_costs += inputs.commission_value

    if inputs.tax_mode in ("REV", "USN6", "NPD", "CUSTOM"):
        tax_fixed = inputs.tax_rate * P
        max_ads = P - fixed_costs - tax_fixed
    elif inputs.tax_mode in ("PROFIT", "USN15"):
        # net = (P - fixed_costs - A) * (1 - t) >= 0 → A_max = P - fixed_costs
        max_ads = P - fixed_costs
    else:
        tax_fixed = inputs.tax_rate * P
        max_ads = P - fixed_costs - tax_fixed

    max_ads = max(0.0, max_ads)
    max_drr = (max_ads / P) if P > 0 else 0.0

    return {
        "profit_before_tax": round(profit_before_tax, 2),
        "tax": round(tax, 2),
        "net_profit": round(net_profit, 2),
        "margin_pct": round(margin_pct * 100, 2),
        "ads_rub": round(A, 2),
        "drr_pct": round(DRR * 100, 2),
        "max_ads_rub": round(max_ads, 2),
        "max_drr_pct": round(max_drr * 100, 2),
        "commission_rub": round(K, 2),
        "returns_cost_expected": round(Ret, 2),
    }


def _net_profit_for_price(price: float, inputs: CalcInputs) -> float:
    # Важно: используем _core_compute, а НЕ compute → нет рекурсии
    tmp = CalcInputs(**{**inputs.__dict__, "price": price})
    res = _core_compute(tmp)
    return res["net_profit"]


def _breakeven_price(inputs: CalcInputs) -> Optional[float]:
    lo = 0.01
    hi = max(inputs.price * 3.0, 1000.0)

    # расширяем верхнюю границу, пока прибыль не станет положительной
    for _ in range(10):
        if _net_profit_for_price(hi, inputs) > 0:
            break
        hi *= 2.0
        if hi > 1e7:
            return None

    f_lo = _net_profit_for_price(lo, inputs)
    f_hi = _net_profit_for_price(hi, inputs)

    if f_lo > 0 and f_hi > 0:
        return lo
    if f_lo < 0 and f_hi < 0:
        return None

    for _ in range(60):
        mid = (lo + hi) / 2.0
        f_mid = _net_profit_for_price(mid, inputs)
        if abs(f_mid) < 0.01:
            return mid
        if f_mid > 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2.0


def compute(inputs: CalcInputs) -> dict:
    base = _core_compute(inputs)
    be = _breakeven_price(inputs)
    base["breakeven_price"] = round(be, 2) if be is not None else None
    return base
