import math

FEATURE_NAMES = [
    "amount_log",
    "previous_transfers_1h",
    "amount_to_avg_ratio",
]

def extract_features(event : dict) -> list[float]:
    # TODO: support EUR and VND (VND has no minor units)
    if event["currency"] !="USD":
        raise ValueError("MVP supports USD only")

    amount = int(event["amountMinor"])
    # TODO: platform events don't contain avgTransferMinor30d / previousTransfers1h —
    #       compute per-user history inside wallet-ai from consumed events
    avg_amount = int(event["avgTransferMinor30d"])
    count = int(event["previousTransfers1h"])

    if amount <=0 or avg_amount <=0 or count <0:
        raise ValueError("Insufficient features")

    amount_usd = amount / 100

    return [
        math.log1p(amount_usd),
        float(count),
        amount/avg_amount
    ]