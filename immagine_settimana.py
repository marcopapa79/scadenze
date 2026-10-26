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
            elif diff < 0:
                stato, col_stato = ("ieri" if diff == -1 else f"{-diff} giorni fa"), "#757575"
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


# ---------------------------------------------------------------- report medicinali

LARGHEZZA_REPORT = 900
COLORI_REPORT = {"red": "#C62828", "orange": "#E65100", "green": "#2E7D32", "gray": "#757575"}
# Colonne del report: (chiave, titolo).
COLONNE_REPORT = (
    ("nome", "Medicinale"),
    ("scadenza", "Scadenza"),
    ("apertura", "Aperto il"),
    ("durata", "Dopo apertura"),
    ("posizione", "Posizione"),
    ("stato", "Stato"),
)
# Se c'è spazio la tabella si divide in più colonne affiancate (come un giornale): quante ce ne
# stanno con "Medicinale" largo almeno LARGHEZZA_NOME_AFFIANCATE (al massimo MAX_AFFIANCATE).
# Di solito: in verticale 2 colonne con solo Medicinale, Scadenza e Posizione; in orizzontale 3.
LARGHEZZA_NOME_AFFIANCATE = 170
MAX_AFFIANCATE = 4
SPAZIO_TRA_TABELLE = 24
# Se lo spazio non basta, "Medicinale" si stringe per primo fino a questa larghezza
# (lo "Stato" fino a dove ci sta "Scade tra 999 giorni" su una riga)
LARGHEZZA_COMODA_NOME = 190
SPAZIO_COLONNE = 12


def _layout_colonne_report(colonne, larghezza_utile, livelli):
    """[(chiave, titolo, x, larghezza)] delle colonne (pixel non scalati).

    colonne:  [(chiave, titolo)] delle colonne visibili, in ordine
    livelli:  dizionari {colonna: larghezza} dal più largo al più stretto, per esempio
      1. tutto su una riga, titoli compresi
      2. titoli a capo (es. "Dopo / apertura"): non costa righe in più
      3. "Medicinale" e "Stato" a una larghezza comoda
      4. la parola più lunga (sotto non si va: i testi vanno a capo, mai tagliati)
    Si parte dal primo; se lo spazio non basta si scende di livello, stringendo le colonne
    in proporzione a quanto possono cedere. Se avanza spazio, si divide tra tutte; se non basta
    neanche l'ultimo livello, si stringono le colonne più larghe.
    """
    chiavi = [k for k, _ in colonne]
    disponibile = larghezza_utile - SPAZIO_COLONNE * (len(colonne) - 1)
    larghezze = {k: livelli[0][k] for k in chiavi}
    eccesso = sum(larghezze.values()) - disponibile
    for limite in livelli[1:]:
        if eccesso <= 0:
            break
        riducibile = {k: larghezze[k] - limite[k] for k in chiavi if larghezze[k] > limite[k]}
        totale = sum(riducibile.values())
        if totale <= 0:
            continue
        taglio = min(eccesso, totale)
        for k, margine in riducibile.items():
            larghezze[k] -= taglio * margine / totale
        eccesso -= taglio
    if eccesso < 0:
        for k in chiavi:
            larghezze[k] += -eccesso / len(chiavi)
    elif eccesso > 0:
        # Parole lunghissime: si abbassano le colonne più larghe a un tetto comune finché ci stanno;
        # le parole troppo lunghe finiscono con "…"
        basso, alto = 0.0, max(larghezze.values())
        for _ in range(40):
            tetto = (basso + alto) / 2
            if sum(min(v, tetto) for v in larghezze.values()) > disponibile:
                alto = tetto
            else:
                basso = tetto
        for k in chiavi:
            larghezze[k] = min(larghezze[k], basso)
    x, layout = 0, []
    for chiave, titolo in colonne:
        layout.append((chiave, titolo, x, int(larghezze[chiave])))
        x += larghezze[chiave] + SPAZIO_COLONNE
    return layout


def _dividi_in_colonne(elementi, n):
    """Divide le righe (in ordine) in n colonne con l'altezza della più alta il più bassa possibile.

    elementi: lista di (…, altezza, …) con altezze intere. Le colonne di sinistra si riempiono
    per prime (a parità sono loro le più lunghe). Restituisce (colonne, altezza della più alta).
    """
    def riempi(tetto):
        colonne, colonna, alta = [], [], 0
        for e in elementi:
            if colonna and alta + e[1] > tetto:
                colonne.append(colonna)
                colonna, alta = [], 0
            colonna.append(e)
            alta += e[1]
        colonne.append(colonna)
        return colonne

    basso, alto = max((e[1] for e in elementi), default=0), sum(e[1] for e in elementi)
    while basso < alto:
        medio = (basso + alto) // 2
        if len(riempi(medio)) <= n:
            alto = medio
        else:
            basso = medio + 1
    colonne = riempi(basso)
    colonne += [[] for _ in range(n - len(colonne))]
    return colonne, max(sum(e[1] for e in c) for c in colonne)


def crea_report_medicinali(righe, oggi=None, titolo="Medicinali di casa", sottotitolo="",
                           riepilogo=None, altezza_pagina=None, mostra_stato=True, mostra_durata=True,
                           mostra_apertura=True, ingrandimento=1.0, larghezza=LARGHEZZA_REPORT,
                           colonne_affiancate=None):
    """
    Report a tabella dei medicinali, adatto a WhatsApp e alla stampa.

    righe:     lista di dict {"nome", "scadenza", "apertura", "durata", "posizione", "stato", "colore"}
               (testi già pronti; "stato" può avere due righe separate da \\n; "colore" = red/orange/green/gray)
    riepilogo: lista di (testo, colore) mostrati sotto il titolo, es. [("9 medicinali", "gray"), ...]
    altezza_pagina: se indicata (pixel non scalati), divide le righe in più immagini (pagine)
                    alte al massimo così; altrimenti restituisce una sola immagine.
    larghezza:       larghezza dell'immagine (pixel non scalati); per il foglio orizzontale
                     vedi pagina_report_a4(orizzontale=True).
    mostra_stato:    False = senza colonna Stato e senza colori di stato (elenco semplice da stampare).
    mostra_durata:   False = senza la colonna "Dopo apertura".
    mostra_apertura: False = senza la colonna "Aperto il".
    ingrandimento:   moltiplica la grandezza dei caratteri (es. 1.15 per la stampa).
    colonne_affiancate: in quante colonne affiancate dividere la tabella (si legge giù nella prima,
                     poi giù nella seconda...). Con più di una, "Posizione" diventa "Piano" e
                     "Piano sotto" diventa "Sotto". None (predefinito) = quante ce ne stanno.
    Restituisce una lista di immagini PIL.
    """
    oggi = oggi or date.today()
    s = SCALA
    k = ingrandimento

    def misura(n):
        return int(round(n * k))

    f_titolo = _carica_font(misura(26), True)
    f_sotto = _carica_font(misura(14))
    f_riepilogo = _carica_font(misura(15), True)
    f_intest = _carica_font(misura(13), True)
    f_nome = _carica_font(misura(15), True)
    f_testo = _carica_font(misura(14))
    f_stato = _carica_font(misura(13), True)
    f_piede = _carica_font(misura(12))

    margine = 24
    alt_riga_testo = misura(20)
    visibili = {c[0] for c in COLONNE_REPORT}
    if not mostra_stato:
        visibili.discard("stato")
    if not mostra_durata:
        visibili.discard("durata")
    if not mostra_apertura:
        visibili.discard("apertura")

    prova = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    grigio = "#9E9E9E"

    # Larghezze: "naturale" = tutto su una riga; "minima" = la parola più lunga (titolo compreso)
    def larghezza_testo(testo, font):
        return max((prova.textlength(parte, font=font) for parte in testo.split("\n")), default=0) / s

    def parola_piu_lunga(testo, font):
        return max((prova.textlength(p, font=font) for p in testo.split()), default=0) / s

    def prepara(affiancate):
        """Titoli, testi delle celle (prima di andare a capo) e livelli di larghezza delle colonne."""
        titoli = dict(COLONNE_REPORT)
        if affiancate:
            titoli["posizione"] = "Piano"   # e nelle celle "Sotto" invece di "Piano sotto"

        def testo_posizione(testo):
            if affiancate and testo.lower().startswith("piano "):
                testo = testo[6:]
                return testo[:1].upper() + testo[1:]
            return testo

        celle_testo = []
        for r in righe:
            celle_testo.append({
                "nome": (r["nome"], f_nome, "#212121"),
                "scadenza": (r.get("scadenza") or "", f_testo, "#212121"),
                "apertura": (r.get("apertura") or "—", f_testo, "#212121" if r.get("apertura") else grigio),
                "durata": (r.get("durata") or "—", f_testo, "#212121" if r.get("durata") else grigio),
                "posizione": (testo_posizione(r.get("posizione") or "—"), f_testo,
                              "#212121" if r.get("posizione") else grigio),
                "stato": (r.get("stato") or "", f_stato, COLORI_REPORT.get(r.get("colore"), "#212121")),
            })
        naturali, celle_su_una_riga, comode, minime = {}, {}, {}, {}
        for chiave, titolo_col in titoli.items():
            celle = [larghezza_testo(*c[chiave][:2]) for c in celle_testo]
            minime[chiave] = 4 + max([parola_piu_lunga(titolo_col, f_intest)] +
                                     [parola_piu_lunga(*c[chiave][:2]) for c in celle_testo])
            celle_su_una_riga[chiave] = max(minime[chiave], 4 + max(celle, default=0))
            naturali[chiave] = max(celle_su_una_riga[chiave], 4 + larghezza_testo(titolo_col, f_intest))
            comode[chiave] = celle_su_una_riga[chiave]
        comode["nome"] = max(minime["nome"], min(comode["nome"], LARGHEZZA_COMODA_NOME))
        comode["stato"] = max(minime["stato"], min(comode["stato"],
                                                   4 + larghezza_testo("Scade tra 999 giorni", f_stato)))
        return titoli, celle_testo, [naturali, celle_su_una_riga, comode, minime]

    def larghezza_tabella(n):
        return (larghezza - 2 * margine - (n - 1) * SPAZIO_TRA_TABELLE) / n

    if colonne_affiancate is None:
        # Quante tabelle affiancate ci stanno, con le colonne "comode" e il nome largo almeno
        # LARGHEZZA_NOME_AFFIANCATE
        _, _, (_, su_una_riga, comode, minime) = prepara(True)
        serve = (max(minime["nome"], min(su_una_riga["nome"], LARGHEZZA_NOME_AFFIANCATE)) +
                 sum(comode[c] for c in visibili if c != "nome") + SPAZIO_COLONNE * (len(visibili) - 1))
        colonne_affiancate = next((n for n in range(MAX_AFFIANCATE, 1, -1)
                                   if larghezza_tabella(n) - 16 >= serve), 1)
    n_colonne = max(1, int(colonne_affiancate))
    titoli, celle_testo, livelli = prepara(n_colonne > 1)
    # Con più colonne affiancate le righe sono un po' più fitte, per stare in un foglio
    pad_riga = misura(6 if n_colonne > 1 else 10)
    alt_minima_riga = misura(32 if n_colonne > 1 else 42)
    larghezza_tab = larghezza_tabella(n_colonne)
    colonne = _layout_colonne_report([(c, titoli[c]) for c, _ in COLONNE_REPORT if c in visibili],
                                     larghezza_tab - 16, livelli)
    # Titoli delle colonne, anche loro a capo se la colonna è stretta
    titoli_a_capo = [_a_capo(prova, t, f_intest, w * s, 3) for _, t, _, w in colonne]
    alt_riga_intest = misura(17)

    # A capo dentro le colonne e altezza di ogni riga
    impaginate = []
    for r, valori in zip(righe, celle_testo):
        celle = []
        for chiave, _, _, w in colonne:
            testo, font, colore_testo = valori[chiave]
            testi = []
            for parte in testo.split("\n"):
                testi += _a_capo(prova, parte, font, w * s, 8) or [""]
            celle.append((testi, font, colore_testo))
        n_righe = max(len(c[0]) for c in celle) or 1
        impaginate.append((celle, max(alt_minima_riga, n_righe * alt_riga_testo + 2 * pad_riga),
                           r.get("colore") if mostra_stato else None))

    alt_testata = misura(108 if riepilogo else 84)
    alt_intest = max(misura(34), max(len(t) for t in titoli_a_capo) * alt_riga_intest + misura(14))
    alt_piede = misura(40)

    # Suddivisione in pagine; ogni pagina = lista di colonne affiancate, ognuna con le sue righe
    limite = (altezza_pagina - alt_testata - alt_intest - alt_piede - 20) if altezza_pagina else None
    pagine, resto = [], list(impaginate)
    while True:
        parti, alta = _dividi_in_colonne(resto, n_colonne)
        if limite is None or alta <= limite:
            pagine.append(parti)  # ultima pagina: colonne bilanciate
            break
        # Pagina piena: si riempie una colonna dopo l'altra
        parti = []
        for _ in range(n_colonne):
            colonna, alta = [], 0
            while resto and (not colonna or alta + resto[0][1] <= limite):
                alta += resto[0][1]
                colonna.append(resto.pop(0))
            parti.append(colonna)
        pagine.append(parti)

    immagini = []
    for numero, parti in enumerate(pagine, start=1):
        alt_righe = max(sum(e[1] for e in colonna) for colonna in parti) or 50
        altezza = alt_testata + alt_intest + alt_righe + alt_piede + 20
        img = Image.new("RGB", (int(larghezza * s), int(altezza * s)), "white")
        d = ImageDraw.Draw(img)

        # Titolo, sottotitolo e riepilogo
        d.text((margine * s, misura(16) * s), titolo, font=f_titolo, fill="#212121")
        d.text((margine * s, misura(52) * s), sottotitolo or f"Situazione al {oggi.strftime('%d/%m/%Y')}",
               font=f_sotto, fill=TESTO_CHIARO)
        if riepilogo:
            x = margine * s
            for i, (testo, colore) in enumerate(riepilogo):
                if i:
                    d.text((x, misura(78) * s), "  ·  ", font=f_riepilogo, fill="#9E9E9E")
                    x += _larghezza(d, "  ·  ", f_riepilogo)
                d.text((x, misura(78) * s), testo, font=f_riepilogo, fill=COLORI_REPORT.get(colore, colore))
                x += _larghezza(d, testo, f_riepilogo)

        for indice, colonna in enumerate(parti):
            if indice and not colonna:
                continue  # colonna vuota a destra: niente intestazione
            sinistra = margine + indice * (larghezza_tab + SPAZIO_TRA_TABELLE)
            destra = sinistra + larghezza_tab
            x_tabella = sinistra + 8

            # Intestazione della tabella
            y = alt_testata
            d.rectangle((sinistra * s, y * s, destra * s, (y + alt_intest) * s), fill="#ECEFF1")
            for righe_titolo, (_, _, x0, _) in zip(titoli_a_capo, colonne):
                yt = y + (alt_intest - len(righe_titolo) * alt_riga_intest) / 2 + alt_riga_intest / 2
                for riga_titolo in righe_titolo:
                    d.text(((x_tabella + x0) * s, yt * s), riga_titolo, font=f_intest, fill="#455A64",
                           anchor="lm")
                    yt += alt_riga_intest
            y += alt_intest

            # Righe
            if not colonna:
                d.text((x_tabella * s, (y + 25) * s), "Nessun medicinale inserito", font=f_testo,
                       fill=TESTO_CHIARO, anchor="lm")
            for i, (celle, alt, colore) in enumerate(colonna):
                if i % 2:
                    d.rectangle((sinistra * s, y * s, destra * s, (y + alt) * s), fill="#FAFAFA")
                # barretta colorata a sinistra con lo stato
                d.rectangle((sinistra * s, (y + 4) * s, (sinistra + 4) * s, (y + alt - 4) * s),
                            fill=COLORI_REPORT.get(colore, "#BDBDBD"))
                for (testi, font, colore_testo), (_, _, x0, _) in zip(celle, colonne):
                    yt = y + pad_riga
                    for t in testi:
                        d.text(((x_tabella + x0) * s, yt * s), t, font=font, fill=colore_testo)
                        yt += alt_riga_testo
                y += alt
                d.line((sinistra * s, y * s, destra * s, y * s), fill=SEPARATORE, width=s)

        # Piede
        piede = f"Gestione Scadenze  ·  creato il {oggi.strftime('%d/%m/%Y')}"
        if len(pagine) > 1:
            piede += f"  ·  pagina {numero} di {len(pagine)}"
        d.text(((larghezza - margine) * s, (altezza - alt_piede / 2) * s), piede, font=f_piede,
               fill=TESTO_CHIARO, anchor="rm")
        immagini.append(img)
    return immagini


# Foglio A4 a 200 dpi (verticale; in orizzontale le misure si scambiano)
A4_DPI = 200
A4_PIXEL = (1654, 2339)
MARGINE_A4 = 70


def _foglio_a4(orizzontale=False):
    return (A4_PIXEL[1], A4_PIXEL[0]) if orizzontale else A4_PIXEL


def pagina_report_a4(orizzontale=False):
    """Misure di una pagina del report per un foglio A4 (pixel non scalati), da passare a
    crea_report_medicinali(): {"larghezza": ..., "altezza_pagina": ...}.

    I caratteri vengono stampati della stessa grandezza nei due versi: in orizzontale la pagina
    è più larga e meno alta.
    """
    pixel_per_unita = (A4_PIXEL[0] - 2 * MARGINE_A4) / LARGHEZZA_REPORT
    larghezza, altezza = _foglio_a4(orizzontale)
    return {"larghezza": int((larghezza - 2 * MARGINE_A4) / pixel_per_unita),
            "altezza_pagina": int((altezza - 2 * MARGINE_A4) / pixel_per_unita)}


def altezza_pagina_report_a4():
    """Altezza massima (pixel non scalati) di una pagina del report su un foglio A4 verticale."""
    return pagina_report_a4()["altezza_pagina"]


def salva_pdf_a4(pagine, percorso, orizzontale=False):
    """Mette ogni immagine su un foglio A4 (adattata al foglio, con margini) e salva un PDF."""
    foglio_pixel = _foglio_a4(orizzontale)
    larghezza_utile = foglio_pixel[0] - 2 * MARGINE_A4
    altezza_utile = foglio_pixel[1] - 2 * MARGINE_A4
    fogli = []
    for img in pagine:
        rapporto = min(larghezza_utile / img.width, altezza_utile / img.height)
        ridotta = img.resize((int(img.width * rapporto), int(img.height * rapporto)), Image.LANCZOS)
        foglio = Image.new("RGB", foglio_pixel, "white")
        foglio.paste(ridotta, (MARGINE_A4, MARGINE_A4))
        fogli.append(foglio)
    fogli[0].save(percorso, "PDF", resolution=A4_DPI, save_all=True, append_images=fogli[1:])
    return percorso


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
