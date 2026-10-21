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
