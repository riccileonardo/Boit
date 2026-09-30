import os
import json
from datetime import datetime, timezone

FILE_RANKING = "ranking_voz.json"

def carregar_ranking():
    if os.path.exists(FILE_RANKING):
        with open(FILE_RANKING, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def salvar_ranking(dados):
    with open(FILE_RANKING, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4)

def registrar_tempo_voz(user_id: str, horario_entrada: datetime) -> int:
    duracao_segundos = (datetime.now(timezone.utc) - horario_entrada).total_seconds()
    ranking = carregar_ranking()
    ranking[user_id] = ranking.get(user_id, 0) + int(duracao_segundos)
    salvar_ranking(ranking)
    return int(duracao_segundos // 60)