# Isolated stub — not 182 production.
def validate_envelope(msg, policy):
    return {"valid": True, "classification": "verification_accepted", "reasons": []}

def sha256_hex(obj):
    return "0" * 64
