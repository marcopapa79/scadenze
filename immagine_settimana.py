"""
Crea un'immagine a colori degli impegni della settimana, divisa per sezioni
(come nella scheda Scadenze Personali), e la copia negli appunti di Windows
per incollarla su WhatsApp Web con Ctrl+V.

Richiede Pillow (pip install Pillow).
"""
import io
import os
import sys
from datetime import date

from PIL import Image, ImageDraw, ImageFont

# Scala di disegno: 2 = immagine nitida anche dopo la compressione di WhatsApp
SCALA = 2
LARGHEZZA = 760

SFONDO = "#f0f0f0"
TESTO = "#212121"
TESTO_CHIARO = "#757575"
SEPARATORE = "#E0E0E0"

GIORNI_BREVI = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"]


# ---------------------------------------------------------------- font

def _carica_font(dimensione, grassetto=False):
    """Usa Segoe UI / Arial su Windows, DejaVu su Linux, altrimenti il font base."""
    cartella_win = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")
    candidati = (
        ["segoeuib.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf"] if grassetto
        else ["segoeui.ttf", "arial.ttf", "DejaVuSans.ttf"]
    )
    percorsi = []
    for nome in candidati:
        percorsi.append(os.path.join(cartella_win, nome))
        percorsi.append(os.path.join("/usr/share/fonts/truetype/dejavu", nome))
    for percorso in percorsi:
        if os.path.exists(percorso):
            return ImageFont.truetype(percorso, dimensione * SCALA)
    try:
        return ImageFont.load_default(size=dimensione * SCALA)
    except TypeError:
        return ImageFont.load_default()


def _larghezza(draw, testo, font):
    return draw.textlength(testo, font=font)


def _accorcia(draw, testo, font, larghezza_max):
    """Taglia il testo con '…' se non entra nello spazio disponibile."""
    if _larghezza(draw, testo, font) <= larghezza_max:
        return testo
    while testo and _larghezza(draw, testo + "…", font) > larghezza_max:
        testo = testo[:-1]
    return testo.rstrip() + "…"


# ---------------------------------------------------------------- disegno

def crea_immagine(sezioni, inizio, fine, oggi=None):
    """
    sezioni: lista di (titolo, colore, righe) nell'ordine di visualizzazione.
             righe: lista di dict {"giorno": date, "ora": "17:30-18:30" o "", "nome": str}
    Restituisce un'immagine PIL.
    """
    oggi = oggi or date.today()
    s = SCALA
    f_titolo = _carica_font(24, True)
    f_sottotitolo = _carica_font(13)
    f_sezione = _carica_font(17, True)
    f_giorno = _carica_font(14, True)
    f_testo = _carica_font(14)
    f_ora = _carica_font(13, True)
    f_stato = _carica_font(12, True)

    margine = 16 * s
    alt_riga = 34 * s
    alt_titolo_sez = 40 * s
    spazio_sez = 14 * s
    alt_testata = 78 * s
    alt_piede = 34 * s

    sezioni = [sez for sez in sezioni if sez[2]]
    altezza = alt_testata + alt_piede
    if sezioni:
        for _, _, righe in sezioni:
            altezza += alt_titolo_sez + len(righe) * alt_riga + 8 * s + spazio_sez
    else:
        altezza += 60 * s

    larghezza = LARGHEZZA * s
    img = Image.new("RGB", (larghezza, altezza), SFONDO)
    d = ImageDraw.Draw(img)

    # Testata
    d.text((margine, 14 * s), "Impegni della settimana", font=f_titolo, fill=TESTO)
    sottotitolo = f"dal {inizio.strftime('%d/%m')} al {fine.strftime('%d/%m/%Y')}"
    d.text((margine, 48 * s), sottotitolo, font=f_sottotitolo, fill=TESTO_CHIARO)

    y = alt_testata
    if not sezioni:
        d.text((margine, y + 10 * s), "Nessun impegno in programma.", font=f_testo, fill=TESTO_CHIARO)
        y += 60 * s

    x_giorno = margine + 22 * s
    x_ora = x_giorno + 104 * s
    x_nome = x_ora + 116 * s
    x_stato_dx = larghezza - margine - 14 * s

    for titolo, colore, righe in sezioni:
        alt_box = alt_titolo_sez + len(righe) * alt_riga + 8 * s
        # Riquadro bianco con barra colorata a sinistra
        d.rounded_rectangle((margine, y, larghezza - margine, y + alt_box),
                            radius=10 * s, fill="white", outline=SEPARATORE, width=s)
        d.rounded_rectangle((margine, y, margine + 7 * s, y + alt_box), radius=3 * s, fill=colore)
        d.text((x_giorno, y + 10 * s), titolo, font=f_sezione, fill=colore)

        yr = y + alt_titolo_sez
        for i, riga in enumerate(righe):
            if i > 0:
                d.line((x_giorno, yr, larghezza - margine - 14 * s, yr), fill=SEPARATORE, width=s)
            centro = yr + alt_riga // 2
            giorno = riga["giorno"]

            # Giorno
            etichetta = f"{GIORNI_BREVI[giorno.weekday()]} {giorno.strftime('%d/%m')}"
            d.text((x_giorno, centro), etichetta, font=f_giorno, fill=TESTO, anchor="lm")

            # Orario in un'etichetta colorata
            ora = riga.get("ora") or "tutto il giorno"
            f_o = f_ora if riga.get("ora") else f_stato
            l_ora = _larghezza(d, ora, f_o)
            d.rounded_rectangle((x_ora - 6 * s, centro - 11 * s, x_ora + l_ora + 6 * s, centro + 11 * s),
                                radius=11 * s, fill=colore)
            d.text((x_ora, centro), ora, font=f_o, fill="white", anchor="lm")

            # Stato a destra (oggi / domani / tra N giorni)
            diff = (giorno - oggi).days
            if diff == 0:
                stato, col_stato = "OGGI", "#D32F2F"
            elif diff == 1:
                stato, col_stato = "domani", "#EF6C00"
            else:
                stato, col_stato = f"tra {diff} giorni", "#2E7D32"
            l_stato = _larghezza(d, stato, f_stato)
            d.text((x_stato_dx, centro), stato, font=f_stato, fill=col_stato, anchor="rm")

            # Nome (accorciato se troppo lungo)
            spazio_nome = max(x_stato_dx - l_stato - 14 * s, x_ora + l_ora + 14 * s) - max(x_nome, x_ora + l_ora + 14 * s)
            x_n = max(x_nome, x_ora + l_ora + 14 * s)
            nome = _accorcia(d, riga["nome"], f_testo, spazio_nome)
            d.text((x_n, centro), nome, font=f_testo, fill=TESTO, anchor="lm")

            yr += alt_riga
        y += alt_box + spazio_sez

    # Piede
    piede = f"Gestione Scadenze • creato il {oggi.strftime('%d/%m/%Y')}"
    d.text((larghezza - margine, altezza - alt_piede // 2), piede, font=f_sottotitolo,
           fill=TESTO_CHIARO, anchor="rm")
    return img


# ---------------------------------------------------------------- vista calendario

LARGHEZZA_CALENDARIO = 1100
ALTEZZA_ORA = 64            # pixel (non scalati) per ogni ora della griglia
BLU_OGGI = "#1A73E8"


def _scurisci(colore, fattore=0.82):
    """Rende un colore #RRGGBB un po' più scuro, per far risaltare la scritta bianca."""
    colore = colore.lstrip("#")
    r, g, b = (int(colore[i:i + 2], 16) for i in (0, 2, 4))
    return "#%02X%02X%02X" % (int(r * fattore), int(g * fattore), int(b * fattore))


def _minuti(hhmm):
    ore, minuti = hhmm.split(":")
    return int(ore) * 60 + int(minuti)


def _orario_evento(ora):
    """'17:30-18:30' → (1050, 1110); '17:30' → (1050, 1110); '' → None (tutto il giorno)."""
    if not ora:
        return None
    try:
        if "-" in ora:
            inizio, fine = ora.split("-", 1)
            a, b = _minuti(inizio.strip()), _minuti(fine.strip())
        else:
            a = _minuti(ora.strip())
            b = a + 60
    except ValueError:
        return None
    if b <= a:
        b = a + 30
    return a, b


def _a_capo(draw, testo, font, larghezza_max, max_righe):
    """Divide il testo in righe che stanno nella larghezza; l'ultima riga finisce con '…' se serve."""
    if max_righe <= 0:
        return []
    parole = testo.split()
    righe, corrente = [], ""
    for parola in parole:
        prova = f"{corrente} {parola}".strip()
        if _larghezza(draw, prova, font) <= larghezza_max:
            corrente = prova
        else:
            if corrente:
                righe.append(corrente)
            corrente = parola
    if corrente:
        righe.append(corrente)
    if len(righe) > max_righe:
        righe = righe[:max_righe]
        righe[-1] = righe[-1] + " …"
    return [_accorcia(draw, r, font, larghezza_max) for r in righe]


def _disponi_sovrapposti(eventi_giorno):
    """Assegna a ogni evento (con orario) una colonna, affiancando quelli che si sovrappongono.

    eventi_giorno: lista di dict con 'inizio_min' e 'fine_min'. Aggiunge 'colonna' e 'colonne'.
    """
    eventi_giorno.sort(key=lambda e: (e["inizio_min"], -e["fine_min"]))
    gruppo, fine_gruppo = [], -1
    fine_colonne = []

    def chiudi_gruppo():
        # Affianca solo se due impegni sovrapposti iniziano a meno di 30 minuti di distanza
        # (altrimenti verrebbe coperto il titolo); se no li sovrappone a cascata come Google.
        affianca = any(
            abs(a["inizio_min"] - b["inizio_min"]) < 30
            for i, a in enumerate(gruppo) for b in gruppo[i + 1:]
            if a["inizio_min"] < b["fine_min"] and b["inizio_min"] < a["fine_min"]
        )
        for e in gruppo:
            e["colonne"] = len(fine_colonne)
            e["affianca"] = affianca

    for e in eventi_giorno:
        if gruppo and e["inizio_min"] >= fine_gruppo:
            chiudi_gruppo()
            gruppo, fine_colonne = [], []
        for i, fine_col in enumerate(fine_colonne):
            if fine_col <= e["inizio_min"]:
                e["colonna"] = i
                fine_colonne[i] = e["fine_min"]
                break
        else:
            e["colonna"] = len(fine_colonne)
            fine_colonne.append(e["fine_min"])
        gruppo.append(e)
        fine_gruppo = max(fine_gruppo, e["fine_min"])
    if gruppo:
        chiudi_gruppo()


def crea_immagine_calendario(eventi, inizio, giorni=7, oggi=None, legenda=None):
    """
    Vista a calendario settimanale (stile Google Calendar).

    eventi:  lista di dict {"giorno": date, "ora": "17:30-18:30" | "17:30" | "", "nome": str, "colore": "#RRGGBB"}
    legenda: lista di (titolo, colore) da mostrare in fondo (solo le sezioni usate)
    """
    from datetime import timedelta

    oggi = oggi or date.today()
    s = SCALA
    f_titolo = _carica_font(30, True)
    f_sottotitolo = _carica_font(16)
    f_giorno_sett = _carica_font(15, True)
    f_numero = _carica_font(28, True)
    f_ore = _carica_font(14, True)
    f_evento = _carica_font(15, True)
    f_evento_ora = _carica_font(13, True)
    f_legenda = _carica_font(15)

    margine = 16 * s
    gutter = 62 * s
    larghezza = LARGHEZZA_CALENDARIO * s
    larg_col = (larghezza - 2 * margine - gutter) / giorni
    giorni_lista = [inizio + timedelta(days=i) for i in range(giorni)]
    fine = giorni_lista[-1]

    # Separa eventi con orario e "tutto il giorno"
    con_orario = {g: [] for g in giorni_lista}
    tutto_giorno = {g: [] for g in giorni_lista}
    for ev in eventi:
        if ev["giorno"] not in con_orario:
            continue
        orario = _orario_evento(ev.get("ora", ""))
        if orario:
            e = dict(ev, inizio_min=orario[0], fine_min=orario[1])
            con_orario[ev["giorno"]].append(e)
        else:
            tutto_giorno[ev["giorno"]].append(ev)
    for g in giorni_lista:
        _disponi_sovrapposti(con_orario[g])

    tutti_orari = [e for g in giorni_lista for e in con_orario[g]]
    if tutti_orari:
        ora_inizio = max(0, min(e["inizio_min"] for e in tutti_orari) // 60)
        ora_fine = min(24, -(-max(e["fine_min"] for e in tutti_orari) // 60))
        if ora_fine - ora_inizio < 4:
            ora_fine = min(24, ora_inizio + 4)
    else:
        ora_inizio = ora_fine = 0

    # Altezze delle fasce
    alt_testata = 92 * s
    alt_giorni = 78 * s
    alt_chip = 28 * s
    max_tutto_giorno = max((len(v) for v in tutto_giorno.values()), default=0)
    alt_tutto_giorno = (max_tutto_giorno * (alt_chip + 3 * s) + 6 * s) if max_tutto_giorno else 0
    alt_griglia = (ora_fine - ora_inizio) * ALTEZZA_ORA * s + (22 * s if tutti_orari else 0)
    alt_vuoto = 50 * s if not tutti_orari and not max_tutto_giorno else 0
    alt_legenda = 44 * s if legenda else 0
    alt_piede = 30 * s
    altezza = alt_testata + alt_giorni + alt_tutto_giorno + alt_griglia + alt_vuoto + alt_legenda + alt_piede + 10 * s

    img = Image.new("RGB", (larghezza, altezza), SFONDO)
    d = ImageDraw.Draw(img)

    # Testata
    d.text((margine, 14 * s), "Impegni della settimana", font=f_titolo, fill=TESTO)
    d.text((margine, 56 * s), f"dal {inizio.strftime('%d/%m')} al {fine.strftime('%d/%m/%Y')}",
           font=f_sottotitolo, fill=TESTO_CHIARO)

    # Riquadro bianco del calendario
    x0 = margine + gutter
    y_cal = alt_testata
    y_fondo_cal = y_cal + alt_giorni + alt_tutto_giorno + alt_griglia + alt_vuoto
    d.rounded_rectangle((margine, y_cal, larghezza - margine, y_fondo_cal),
                        radius=12 * s, fill="white", outline=SEPARATORE, width=s)

    def x_col(i):
        return x0 + i * larg_col

    # Colonna di oggi leggermente evidenziata
    for i, g in enumerate(giorni_lista):
        if g == oggi:
            d.rectangle((x_col(i) + s, y_cal + s, x_col(i + 1) - s, y_fondo_cal - s), fill="#F1F6FE")

    # Intestazioni dei giorni
    for i, g in enumerate(giorni_lista):
        cx = x_col(i) + larg_col / 2
        col_testo = BLU_OGGI if g == oggi else TESTO_CHIARO
        d.text((cx, y_cal + 18 * s), GIORNI_BREVI[g.weekday()].upper(), font=f_giorno_sett,
               fill=col_testo, anchor="mm")
        cy = y_cal + 50 * s
        if g == oggi:
            r = 21 * s
            d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=BLU_OGGI)
            d.text((cx, cy), str(g.day), font=f_numero, fill="white", anchor="mm")
        else:
            d.text((cx, cy), str(g.day), font=f_numero, fill=TESTO, anchor="mm")

    # Linee verticali tra i giorni
    for i in range(giorni + 1):
        d.line((x_col(i), y_cal + alt_giorni - 6 * s, x_col(i), y_fondo_cal - 2 * s), fill=SEPARATORE, width=s)
    d.line((margine, y_cal + alt_giorni, larghezza - margine, y_cal + alt_giorni), fill="#BDBDBD", width=s)

    # Fascia "tutto il giorno"
    y = y_cal + alt_giorni
    if max_tutto_giorno:
        d.text((x0 - 6 * s, y + 6 * s + alt_chip / 2), "tutto il\ngiorno", font=f_ore,
               fill=TESTO_CHIARO, anchor="rm", align="right")
        for i, g in enumerate(giorni_lista):
            yc = y + 6 * s
            for ev in tutto_giorno[g]:
                d.rounded_rectangle((x_col(i) + 3 * s, yc, x_col(i + 1) - 3 * s, yc + alt_chip),
                                    radius=6 * s, fill=_scurisci(ev["colore"]))
                nome = _accorcia(d, ev["nome"], f_evento, larg_col - 14 * s)
                d.text((x_col(i) + 8 * s, yc + alt_chip / 2), nome, font=f_evento, fill="white", anchor="lm")
                yc += alt_chip + 3 * s
        y += alt_tutto_giorno
        d.line((margine, y, larghezza - margine, y), fill="#BDBDBD", width=s)

    # Griglia oraria ed eventi
    if tutti_orari:
        y_griglia = y + 8 * s
        alt_ora = ALTEZZA_ORA * s
        for h in range(ora_inizio, ora_fine + 1):
            yl = y_griglia + (h - ora_inizio) * alt_ora
            if h < ora_fine:
                d.line((x0, yl, larghezza - margine - s, yl), fill=SEPARATORE, width=s)
            d.text((x0 - 6 * s, yl), f"{h:02d}:00", font=f_ore, fill=TESTO_CHIARO, anchor="rm")

        def y_minuti(m):
            return y_griglia + (m - ora_inizio * 60) / 60 * alt_ora

        for i, g in enumerate(giorni_lista):
            for e in con_orario[g]:
                if e["affianca"]:
                    larg_sub = (larg_col - 6 * s) / e["colonne"]
                    bx0 = x_col(i) + 3 * s + e["colonna"] * larg_sub
                    bx1 = bx0 + larg_sub - 2 * s
                else:
                    # A cascata: chi inizia dopo sta sopra, spostato un po' a destra
                    bx0 = x_col(i) + 3 * s + e["colonna"] * 12 * s
                    bx1 = x_col(i + 1) - 3 * s
                by0 = y_minuti(e["inizio_min"]) + s
                by1 = max(y_minuti(e["fine_min"]) - s, by0 + 46 * s)  # minimo: 2 righe di nome
                d.rounded_rectangle((bx0, by0, bx1, by1), radius=6 * s, fill=_scurisci(e["colore"]),
                                    outline="white", width=s)

                # Testo: nome in grassetto (a capo se serve) e orario sotto, se c'è spazio
                spazio_testo = bx1 - bx0 - 10 * s
                alt_riga_nome = 19 * s
                alt_riga_ora = 17 * s
                # Parte visibile: se un impegno successivo gli si sovrappone sopra (a cascata),
                # il testo deve stare prima dell'inizio di quello
                fine_visibile = by1
                if not e["affianca"]:
                    for altro in con_orario[g]:
                        if (altro["colonna"] > e["colonna"]
                                and e["inizio_min"] <= altro["inizio_min"] < e["fine_min"]):
                            fine_visibile = min(fine_visibile, y_minuti(altro["inizio_min"]))
                alt_visibile = max(fine_visibile - by0, 46 * s)
                righe_disp = int((alt_visibile - 4 * s) // alt_riga_nome)
                mostra_ora = (alt_visibile - 4 * s) >= alt_riga_nome + alt_riga_ora
                # Se il nome non entra insieme all'orario, meglio il nome intero senza orario
                # (l'orario si capisce comunque dalla posizione nella griglia)
                righe_necessarie = len(_a_capo(d, e["nome"], f_evento, spazio_testo, 99))
                spazio_con_ora = (alt_visibile - 4 * s - alt_riga_ora) // alt_riga_nome
                if mostra_ora and righe_necessarie > spazio_con_ora:
                    mostra_ora = False
                righe_nome = _a_capo(d, e["nome"], f_evento, spazio_testo,
                                     max(1, righe_disp - (1 if mostra_ora else 0)))
                yt = by0 + 4 * s
                for riga in righe_nome:
                    d.text((bx0 + 6 * s, yt), riga, font=f_evento, fill="white")
                    yt += alt_riga_nome
                if mostra_ora:
                    testo_ora = e["ora"].replace("-", " - ")
                    testo_ora = _accorcia(d, testo_ora, f_evento_ora, spazio_testo)
                    d.text((bx0 + 6 * s, yt), testo_ora, font=f_evento_ora, fill="white")
    elif not max_tutto_giorno:
        d.text((larghezza / 2, y + alt_vuoto / 2), "Nessun impegno in programma.",
               font=f_sottotitolo, fill=TESTO_CHIARO, anchor="mm")

    # Legenda
    if legenda:
        xl = margine + 4 * s
        yl = y_fondo_cal + 14 * s
        for titolo, colore in legenda:
            d.rounded_rectangle((xl, yl, xl + 18 * s, yl + 18 * s), radius=4 * s, fill=_scurisci(colore))
            d.text((xl + 24 * s, yl + 9 * s), titolo, font=f_legenda, fill=TESTO, anchor="lm")
            xl += 24 * s + _larghezza(d, titolo, f_legenda) + 22 * s

    piede = f"Gestione Scadenze • creato il {oggi.strftime('%d/%m/%Y')}"
    d.text((larghezza - margine, altezza - alt_piede // 2 - 4 * s), piede, font=f_sottotitolo,
           fill=TESTO_CHIARO, anchor="rm")
    return img


# ---------------------------------------------------------------- appunti (Windows)

def copia_immagine_negli_appunti(img):
    """Copia l'immagine negli appunti di Windows (formati PNG e DIB).

    Restituisce (True, "") se riesce, altrimenti (False, messaggio).
    """
    if sys.platform != "win32":
        return False, "La copia di immagini negli appunti è disponibile solo su Windows."

    import ctypes
    from ctypes import wintypes

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
    kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
    kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalFree.argtypes = [wintypes.HGLOBAL]
    user32.OpenClipboard.argtypes = [wintypes.HWND]
    user32.OpenClipboard.restype = wintypes.BOOL
    user32.EmptyClipboard.restype = wintypes.BOOL
    user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
    user32.SetClipboardData.restype = wintypes.HANDLE
    user32.CloseClipboard.restype = wintypes.BOOL
    user32.RegisterClipboardFormatW.argtypes = [wintypes.LPCWSTR]
    user32.RegisterClipboardFormatW.restype = wintypes.UINT

    GMEM_MOVEABLE = 0x0002
    CF_DIB = 8

    # DIB = file BMP senza i primi 14 byte di intestazione
    buf = io.BytesIO()
    img.convert("RGB").save(buf, "BMP")
    dati_dib = buf.getvalue()[14:]
    buf = io.BytesIO()
    img.save(buf, "PNG")
    dati_png = buf.getvalue()

    def _memoria_globale(dati):
        handle = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(dati))
        if not handle:
            raise OSError("GlobalAlloc fallita")
        puntatore = kernel32.GlobalLock(handle)
        ctypes.memmove(puntatore, dati, len(dati))
        kernel32.GlobalUnlock(handle)
        return handle

    # Gli appunti possono essere occupati da un'altra app: qualche tentativo
    import time
    for _ in range(10):
        if user32.OpenClipboard(None):
            break
        time.sleep(0.05)
    else:
        return False, "Gli appunti sono occupati da un'altra applicazione. Riprova."

    try:
        user32.EmptyClipboard()
        h_dib = _memoria_globale(dati_dib)
        if not user32.SetClipboardData(CF_DIB, h_dib):
            kernel32.GlobalFree(h_dib)
            return False, "Impossibile copiare l'immagine negli appunti."
        # Formato PNG: lo usano i browser (WhatsApp Web) per una qualità migliore
        formato_png = user32.RegisterClipboardFormatW("PNG")
        if formato_png:
            h_png = _memoria_globale(dati_png)
            if not user32.SetClipboardData(formato_png, h_png):
                kernel32.GlobalFree(h_png)
        return True, ""
    except OSError as e:
        return False, str(e)
    finally:
        user32.CloseClipboard()
