from os import environ

def get_instance_index() -> int:
    return int(environ.get("CF_INSTANCE_INDEX", "0"))
