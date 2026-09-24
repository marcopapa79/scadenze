"""Calcolo delle prossime occorrenze delle scadenze ricorrenti."""

import calendar
from datetime import date, timedelta


CODICI_GIORNI = {
    "MO": 0,
    "TU": 1,
    "WE": 2,
    "TH": 3,
    "FR": 4,
    "SA": 5,
    "SU": 6,
}


def prossima_occorrenza(data_iniziale, ricorrenza, oggi):
    """Restituisce la prossima occorrenza valida, oppure None se terminata."""
    if not ricorrenza or not ricorrenza.get("attiva"):
        return data_iniziale

    fino_al = ricorrenza.get("fino_al")
    if fino_al:
        try:
            data_fine = date.fromisoformat(fino_al)
        except ValueError:
            data_fine = None
    else:
        data_fine = None

    data_cercata = max(data_iniziale, oggi)
    freq = ricorrenza.get("freq", "WEEKLY")
    intervallo = max(1, int(ricorrenza.get("intervallo", 1) or 1))

    if freq == "WEEKLY":
        giorni = {
            CODICI_GIORNI[codice]
            for codice in ricorrenza.get("giorni", [])
            if codice in CODICI_GIORNI
        }
        if not giorni:
            giorni = {data_iniziale.weekday()}

        lunedi_iniziale = data_iniziale - timedelta(days=data_iniziale.weekday())
        for offset in range(3660):
            candidato = data_cercata + timedelta(days=offset)
            if candidato.weekday() not in giorni:
                continue
            settimane = (candidato - lunedi_iniziale).days // 7
            if settimane % intervallo == 0:
                if data_fine and candidato > data_fine:
                    return None
                return candidato
        return None

    if freq == "MONTHLY":
        mese = data_cercata.year * 12 + data_cercata.month - 1
        mese_iniziale = data_iniziale.year * 12 + data_iniziale.month - 1
        for indice in range(max(0, mese - mese_iniziale), 121):
            mese_corrente = mese_iniziale + indice * intervallo
            anno, mese_numero = divmod(mese_corrente, 12)
            giorno = min(data_iniziale.day, calendar.monthrange(anno, mese_numero + 1)[1])
            candidato = date(anno, mese_numero + 1, giorno)
            if candidato >= oggi:
                if data_fine and candidato > data_fine:
                    return None
                return candidato

    return data_iniziale