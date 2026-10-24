def detect_anomalies(event: dict)-> list[str]:
    anomalies = []

    # TODO: match platform event naming (wallet.transfer / Completed) and read fields from envelope payload
    if event["eventType"] != "TRANSFER_COMPLETED":
        return anomalies

    # TODO: support EUR and VND; take threshold from config (ANOMALY_THRESHOLD_MINOR) instead of hardcoding
    if(event["currency"] == "USD"
        and event["amountMinor"]>=500_000):
       anomalies.append("Unusually large transfer")

    # TODO: platform guarantees balance >= 0 and doesn't send balanceAfterMinor — drop this rule
    #       or rename it to an invariant-violation alert
    if event["balanceAfterMinor"] < 0:
        anomalies.append("Negative account balance")

    return anomalies