INT = r"\d+"
HEX = r"[0-9a-z]+"
UUID = r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}"
KEY = "[a-z_]+"
STR = r"[A-Za-z0-9_\-]+"

def get_path_pk(name: str, reg: str) -> str:
    return fr"(?P<{name}>{reg})"

def get_path(name: str, reg: str) -> str:
    return fr"(?P<{name}>{reg})"
