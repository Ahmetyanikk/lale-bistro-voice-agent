import secrets

# no O/0/I/1: avoids ambiguous characters when read aloud or typed back
CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def generate_confirmation_code() -> str:
    suffix = "".join(secrets.choice(CODE_ALPHABET) for _ in range(4))
    return f"LBL-{suffix}"
