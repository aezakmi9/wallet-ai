def detect_anomalies(event: dict)-> list[str]:
    anomalies = []

    if event["eventType"] != "TRANSFER_COMPLETED":
        return anomalies

    if(event["currency"] == "USD"
        and event["amountMinor"]>=500_000):
       anomalies.append("Unusually large transfer")

    if event["balanceAfterMinor"] < 0:
        anomalies.append("Negative account balance")

    return anomalies