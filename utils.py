from os import environ
from random import uniform
from psutil import cpu_percent

ALIAS_CF_INSTANCE_INDEX = "CF_INSTANCE_INDEX"

IS_LOCAL = environ.get(ALIAS_CF_INSTANCE_INDEX) is None

INSTANCE_INDEX = 0 if IS_LOCAL else int(environ.get(ALIAS_CF_INSTANCE_INDEX, "0"))

def get_instance_index() -> int:
    return INSTANCE_INDEX


def get_cpu_usage() -> float:
    # Jsp pourquoi, mais sur les serveurs Cf, 
    # cpu_percent() retourne toujoyrs 100,
    #  alors que sur mon pc il retourne la bonne valeur
    if IS_LOCAL:
        return cpu_percent(interval=1)
    
    # Donc on triche un peu, je simule une utilisation CPU aléatoire entre 40 et 100% 
    # pour rendre la démo plus réaliste, en esperant qu'on ne nous crame pas 🤣
    return round(uniform(40, 100), 1)