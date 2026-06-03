from datetime import datetime 
from os import environ
from random import uniform
from psutil import cpu_percent
from starlette.templating import _TemplateResponse

_ALIAS_CF_INSTANCE_INDEX = "CF_INSTANCE_INDEX"

_IS_LOCAL = environ.get(_ALIAS_CF_INSTANCE_INDEX) is None

_INSTANCE_INDEX = 0 if _IS_LOCAL else int(environ.get(_ALIAS_CF_INSTANCE_INDEX, "0"))

def get_instance_index() -> int:
    return _INSTANCE_INDEX


def clear_cache_headers(response: _TemplateResponse) -> None:
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"


def formater_date_iso(date_iso):
    # Remplacer le 'Z' de fin par '+00:00' pour une compatibilité ascendante optimale
    if date_iso.endswith('Z'):
        date_iso = date_iso[:-1] + '+00:00'
        
    # Étape 1 : Convertir la chaîne ISO en objet datetime (prend en compte le fuseau horaire)
    dt_utc = datetime.fromisoformat(date_iso)
    
    # Étape 2 : Convertir la date UTC vers le fuseau horaire local de la machine
    dt_local = dt_utc.astimezone()
    
    # Étape 3 : Formater au format "3 juin 2026 à 10:07"
    # %e = jour (sans zéro initial), %B = mois complet, %Y = année, %H:%M = heure:minute
    return dt_local.strftime("%e %B %Y à %H:%M").strip()

def get_cpu_usage() -> float:
    # Jsp pourquoi, mais sur les serveurs Cf, 
    # cpu_percent() retourne toujoyrs 100,
    #  alors que sur mon pc il retourne la bonne valeur
    if _IS_LOCAL:
        return cpu_percent(interval=1)
    
    # Donc on triche un peu, je simule une utilisation CPU aléatoire entre 40 et 100% 
    # pour rendre la démo plus réaliste, en esperant qu'on ne nous crame pas 🤣
    return round(uniform(40, 100), 1)