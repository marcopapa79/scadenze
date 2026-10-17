# Gestione Scadenze — Documentazione tecnica

Questo documento spiega **come è fatto il codice**: struttura dei file, formato dei dati, flusso dell'applicazione, logica di calcolo, integrazione con Google Calendar e notifiche. In fondo c'è l'esito della **revisione del codice** con i problemi trovati.

Per l'uso quotidiano (pulsanti, colori) vedi [README.md](README.md); per configurare Google vedi [GOOGLE_CALENDAR_SETUP.md](GOOGLE_CALENDAR_SETUP.md).

---

## 1. Panoramica

Applicazione desktop in **Python + tkinter**, a finestra singola con due schede:

| Scheda | Contenuto |
|---|---|
| 🚗 **Veicoli** | Più veicoli; per ognuno km attuali, scadenze a data (Bollo, Assicurazione, Revisione…) e scadenze chilometriche (Tagliando, Freni, Gomme…) |
| 📋 **Scadenze Personali** | Quattro sezioni: *Visite prenotate*, *Visite da prenotare*, *Scadenze* (casa, ISEE, IMU, documenti…), *Feste e compleanni*. Supporta orari e ricorrenze settimanali/mensili |

Funzioni trasversali: semaforo verde/arancione/rosso, notifiche desktop (`plyer`), esportazione/importazione con Google Calendar (calendario **"Famiglia"**).

Nessun database: tutto vive in un unico file JSON, `stato_veicolo.json`.

---

## 2. Avvio

```
avvia_scadenze.bat
 ├─ verifica che "python" sia nel PATH        → altrimenti errore e pausa
 ├─ cd nella cartella dello script (%~dp0)    → importante: i file sono cercati con percorso relativo
 ├─ se esiste venv\ lo attiva, altrimenti usa il Python di sistema
 ├─ se "import plyer" fallisce → pip install -r requirements.txt
 ├─ python main.py
 └─ se l'app esce con errore → mostra messaggio e pausa (così si legge il traceback)
```

`run.bat` fa solo `cd` + `python main.py`, senza controlli.

All'interno di `main.py`:

```
inizializza_db()          crea stato_veicolo.json con dati di esempio se non esiste
tk.Tk() → ScadenzeApp     carica il JSON, eventuale migrazione, costruisce le schede
root.mainloop()
```

> ⚠️ `stato_veicolo.json`, `credentials.json` e `token.pickle` sono cercati **nella cartella corrente**, non in quella dello script. Con i `.bat` va bene perché fanno `cd`; se lanci `python C:\...\main.py` da un'altra cartella, l'app crea un **nuovo** file dati vuoto lì (vedi revisione, punto 6).

---

## 3. Struttura dei file

| File | Righe | Ruolo |
|---|---|---|
| `main.py` | ~1580 | Interfaccia grafica (classe `ScadenzeApp`), lettura/scrittura JSON, conversione date, semaforo |
| `ricorrenze.py` | ~70 | `prossima_occorrenza()`: calcola la prossima data di una scadenza ricorrente |
| `notifiche.py` | ~175 | Controllo scadenze e invio notifiche desktop con `plyer` |
| `google_calendar.py` | ~545 | OAuth Google, export eventi (singoli e in blocco, con RRULE), import eventi |
| `stato_veicolo.json` | — | Tutti i dati |
| `requirements.txt` | — | `plyer` + librerie Google |
| `credentials.json` / `client_secret_*.json` | — | Credenziali OAuth (escluse da git) |
| `token.pickle` | — | Token Google salvato dopo il primo login (escluso da git) |

Dipendenze tra moduli:

```
main.py ──► ricorrenze.py
   │  ├──► notifiche.py ──► ricorrenze.py, plyer
   │  └──► google_calendar.py ──► google-auth, googleapiclient
```

`notifiche` e `google_calendar` sono **opzionali**: se l'import fallisce, `main.py` imposta `NOTIFICHE_DISPONIBILI` / `GOOGLE_CALENDAR_DISPONIBILE = False` e semplicemente non mostra i relativi pulsanti.

---

## 4. Formato dei dati (`stato_veicolo.json`)

```jsonc
{
  "veicoli": {
    "Corolla (GD028MR)": {                 // chiave = "Nome (TARGA)"
      "nome_veicolo": "Corolla",
      "targa": "GD028MR",
      "km_attuali": 88375,
      "scadenze_fisse": {                  // nome → data ISO
        "Bollo": "2026-08-31"
      },
      "scadenze_chilometriche": {          // nome → km
        "Tagliando": { "ultimo_km": 0, "prossimo_km": 91400 }
      }
    }
  },
  "veicolo_selezionato": "Corolla (GD028MR)",

  "scadenze_personali": {
    "Visita Fazi": {                       // chiave = nome visualizzato (univoco)
      "data": "2026-10-16",                // ISO, per le ricorrenti è la data di partenza
      "con_orario": true,
      "ora_inizio": "16:00",               // "HH:MM" oppure null
      "ora_fine": "17:00",
      "ricorrenza": null,                  // oppure oggetto (sotto)
      "categoria": "visita_prenotata"      // facoltativo, solo per alcuni import
    },
    "Basket": {
      "data": "2026-09-22", "con_orario": true, "ora_inizio": "17:30", "ora_fine": "18:30",
      "ricorrenza": {
        "attiva": true,
        "freq": "WEEKLY",                  // "WEEKLY" | "MONTHLY"
        "intervallo": 1,                   // ogni N settimane/mesi
        "giorni": ["MO", "TH"],            // solo WEEKLY, codici RRULE
        "fino_al": "2027-06-29"            // ISO oppure null = senza fine
      }
    }
  }
}
```

Note:
- **Date sempre in ISO** (`AAAA-MM-GG`) nel file; nell'interfaccia sono mostrate e digitate in italiano (`GG-MM-AAAA`). Le conversioni sono `data_iso_a_italiana()` / `data_italiana_a_iso()`.
- **Vecchio formato** ancora supportato ovunque: una scadenza personale può essere una semplice stringa `"2027-01-15"` invece di un oggetto.
- Il codice migra anche un formato ancora più vecchio a veicolo singolo (`migra_vecchio_formato()`).

---

## 5. Come vengono classificate le scadenze personali

Non c'è un campo "tipo" affidabile: la sezione in cui compare una voce dipende **soprattutto dal nome** (`crea_tab_personali`):

| Ordine | Condizione | Sezione |
|---|---|---|
| 1 | nome contiene `visita` o `medic` **e** contiene `prenotare` | Visite da prenotare |
| 2 | `categoria == "visita_prenotata"` **oppure** nome contiene `visita`/`medic` | Visite prenotate |
| 3 | nome contiene `compleanno` o `festa` | Feste e compleanni |
| 4 | tutto il resto | Scadenze |

Il pulsante "+ Nuova Visita da Prenotare" aggiunge automaticamente il suffisso ` da prenotare` al nome. Rinominare una voce può quindi **spostarla di sezione**.

Se un nome esiste già, `_nome_personale_univoco()` aggiunge ` (2)`, ` (3)`, …

---

## 6. Semaforo e soglie

Costanti (duplicate in `main.py` e `notifiche.py`):

```python
SOGLIA_GIORNI_PREAVVISO = 30
SOGLIA_KM_PREAVVISO     = 3500
```

| Stato | Scadenza a data | Scadenza a km |
|---|---|---|
| 🟢 verde | > 30 giorni | > 3500 km residui |
| 🟠 arancione | 0–30 giorni | 1–3500 km |
| 🔴 rosso | data passata | km residui ≤ 0 |

Il calcolo avviene in `ScadenzeApp.aggiorna_visualizzazione()`, chiamata a ogni ricostruzione dell'interfaccia e dopo ogni salvataggio. Le voci di ogni sezione sono ordinate per data (o per km residui).

---

## 7. Ricorrenze (`ricorrenze.py`)

`prossima_occorrenza(data_iniziale, ricorrenza, oggi)` restituisce:
- `data_iniziale` se la voce non è ricorrente;
- la **prima occorrenza da oggi in poi** se è ricorrente;
- `None` se la ricorrenza è finita (`fino_al` superato) → l'interfaccia mostra "Ricorrenza terminata" in grigio.

**Settimanale**: scorre i giorni da `max(data_iniziale, oggi)` e prende il primo che cade in uno dei `giorni` scelti e in una settimana valida per l'`intervallo` (contando le settimane dal lunedì della data iniziale).

**Mensile**: stesso giorno del mese della data iniziale, ogni `intervallo` mesi; se il mese è più corto usa l'ultimo giorno (es. 31 → 30 o 28/29).

Effetto pratico: una voce ricorrente non diventa mai rossa, mostra sempre i giorni alla prossima occorrenza.

La ricorrenza si imposta con il pulsante 🔁 su ogni riga (finestra `_dialog_ricorrenza`) o rispondendo "Sì" quando si crea una nuova voce. Le ricorrenze esistono **solo per le scadenze personali**.

---

## 8. Salvataggio

- `salva_dati()` riscrive **tutto** il JSON ad ogni modifica.
- Aggiunta, eliminazione, rinomina, cambio veicolo, km e ricorrenza **salvano subito**.
- Le modifiche fatte **a mano nei campi** (date, orari, km di tagliando…) vengono salvate **solo** premendo il relativo pulsante blu "Salva …". Se si cambia veicolo o si aggiunge una voce prima di aver salvato, l'interfaccia viene ricostruita dal file e quelle modifiche si perdono.
- Dopo quasi ogni operazione l'interfaccia viene distrutta e ricostruita da zero (`ricarica_interfaccia()`), riaprendo di default la scheda *Scadenze Personali* (o *Veicoli* se si è cambiato veicolo).

---

## 9. Notifiche desktop (`notifiche.py`)

Il pulsante 🔔 chiama `controlla_tutti_veicoli(dati)` che:
1. per ogni veicolo controlla scadenze a data e a km (`controlla_e_notifica`);
2. controlla le scadenze personali (`controlla_scadenze_personali`, tenendo conto delle ricorrenze);
3. per ogni voce rossa o arancione invia una notifica Windows (timeout 15 s critiche, 10 s avvisi);
4. restituisce un riepilogo mostrato poi in una finestra.

Le notifiche partono **solo premendo il pulsante**: non c'è un controllo automatico all'avvio o periodico.

Test rapido: `python notifiche.py` invia una notifica di prova.

---

## 10. Google Calendar (`google_calendar.py`)

**Autenticazione** (`autentica_google_calendar`): se c'è `token.pickle` lo usa, se è scaduto lo rinnova, se il rinnovo fallisce lo cancella e apre il browser per un nuovo login con `credentials.json`. Scope: accesso completo al calendario.

**Calendario di destinazione**: cerca un calendario chiamato **"Famiglia"** (senza distinzione maiuscole); se non lo trova usa quello principale.

**Export** — cosa produce:

| Funzione | Titolo evento | Note |
|---|---|---|
| `esporta_singola_scadenza` (📅 su una riga) | `🏥 Visita: …`, `⚠️ …`, `⚠️ … - Veicolo` | Con orari e ricorrenza (RRULE) |
| `esporta_scadenze_veicolo` (📅 in alto, tab Veicoli) | `Bollo - Corolla` | Le scadenze a km diventano eventi con **data stimata a 50 km/giorno** |
| `esporta_scadenze_personali` (📅 in alto, tab Personali) | nome della voce | Con orari e ricorrenza |

Ogni evento: tutto il giorno oppure con orario (fuso `Europe/Rome`); colore del calendario; promemoria popup:

| Evento | Promemoria |
|---|---|
| Ricorrente (🔁 attivo) | 10 minuti prima |
| Tutti gli altri | 1 giorno prima e 10 minuti prima |

Si cambiano nelle costanti `PROMEMORIA_RICORRENTI` e `PROMEMORIA_SINGOLI` in cima a `google_calendar.py` (valori in minuti). Per gli eventi *tutto il giorno* Google conta i minuti dalla mezzanotte del giorno stesso: "10 minuti prima" = 23:50 della sera prima, "1 giorno prima" = mezzanotte del giorno precedente. Valgono solo per gli eventi esportati da quel momento in poi.

> ⚠️ L'export **non controlla i duplicati**: premere due volte "Esporta" crea due copie di ogni evento su Google.

**Import** (📥 "Importa da Calendar", solo tab Personali):
1. chiede data di inizio e numero di giorni;
2. legge gli eventi del calendario "Famiglia" (ricorrenze espanse in singoli eventi);
3. ripulisce i titoli dai prefissi messi dall'export (`🏥 Visita:`, `⚠️ Scadenza:`…);
4. salta i duplicati (stesso nome, data e orario);
5. chiede conferma evento per evento (Sì / No / Annulla per fermarsi);
6. gli eventi con `Tipo: Visita` nella descrizione vengono marcati `categoria: visita_prenotata`.

---

## 11. Personalizzazioni frequenti

| Cosa | Dove |
|---|---|
| Soglie di preavviso | `SOGLIA_*` in `main.py` **e** in `notifiche.py` |
| Nome del calendario Google | stringa `'Famiglia'` in `google_calendar.py` (3 punti) e `main.py` (import) |
| Promemoria degli eventi | `PROMEMORIA_RICORRENTI` / `PROMEMORIA_SINGOLI` in `google_calendar.py` |
| Stima km/giorno | `km_medi_al_giorno = 50` in `esporta_scadenze_veicolo()` |
| Parole chiave per le sezioni | `_is_visita_personale`, `_is_visita_da_prenotare`, `_is_festa_compleanno` in `main.py` |
| Dati iniziali di esempio | `inizializza_db()` in `main.py` |

---

## 12. Revisione del codice

Verificata il 17/10/2026. I punti 1 e 2 sono stati **riprodotti con un test**.

### 🔴 Bug

**1. Le notifiche delle scadenze a data dei veicoli non partono mai.**
`notifiche.py`, `controlla_e_notifica()`, riga 28: usa la variabile `data_obj`, che in quella funzione non esiste. Ne nasce un `NameError`, nascosto dal `except: pass`, quindi Bollo, Assicurazione e Revisione **non generano mai notifiche**, nemmeno se scadute. (Le scadenze a km e quelle personali funzionano.)
Correzione: passare `None` al posto di `data_obj.get("ricorrenza")`.

**2. Ricorrenza mensile con intervallo > 1 salta occorrenze.**
`ricorrenze.py`, riga 60: l'indice di partenza è il numero di mesi trascorsi, ma viene poi moltiplicato per l'intervallo. Esempio: "ogni 2 mesi dal 15/01", oggi 01/03 → restituisce 15/05 invece di 15/03.
Correzione: partire da `(mese - mese_iniziale) // intervallo`.

**3. Il campo `categoria` viene perso al salvataggio.**
`salva_scadenze_personali()` riscrive ogni voce con solo `data/con_orario/ora_inizio/ora_fine/ricorrenza`. Una visita importata da Google con `categoria: visita_prenotata`, ma senza "visita" nel nome, dopo il primo "Salva Scadenze Personali" finisce nella sezione *Scadenze*.

**4. "+ Nuova Visita Prenotata" non registra la categoria.**
La voce viene messa tra le visite solo se il nome contiene "visita" o "medic". Una visita chiamata, per esempio, "Controllo oculistico" finisce tra le *Scadenze*; "Controllo oculistico da prenotare" non va tra le *Visite da prenotare*. Stesso discorso per le feste.

### 🟠 Rischi

**5. Scrittura del JSON non sicura.** `salva_dati()` sovrascrive direttamente il file: se il PC si spegne o l'app va in crash durante la scrittura, `stato_veicolo.json` può restare vuoto o corrotto e l'app non riparte più. Meglio scrivere su un file temporaneo e poi sostituire (`os.replace`), tenendo una copia `.bak`.

**6. Percorsi relativi.** Lanciando `main.py` da un'altra cartella si crea un nuovo file dati vuoto e non si trovano le credenziali Google. Meglio basare i percorsi su `os.path.dirname(__file__)`.

**7. Salvataggio parziale in memoria.** In `salva_scadenze_personali()` / `salva_scadenze_temp()`, se una riga a metà lista ha una data sbagliata, le righe precedenti sono già state modificate in memoria; non vengono scritte subito, ma lo saranno al prossimo salvataggio di qualsiasi altra cosa.

**8. Export duplicati su Google** (vedi §10): nessun controllo sugli eventi già presenti.

**9. `except:` generici** in `notifiche.py` e nelle conversioni di data nascondono gli errori (è così che il bug 1 è rimasto invisibile).

### 🟡 Manutenibilità

- Soglie duplicate in due file: se ne cambi una sola, semaforo e notifiche non coincidono.
- Il blocco "Modulo Google Calendar non disponibile…" è copiato 5 volte in `main.py`.
- Il riconoscimento "è una visita?" nell'export singolo usa `"Visita" in nome` (maiuscolo) mentre la classificazione usa la `categoria` e le parole chiave minuscole: due regole diverse per la stessa cosa.
- `avvia_scadenze.bat` controlla solo `plyer`: se mancano le librerie Google l'app parte ma senza i pulsanti Calendar, senza avvisare.
- `README.md` in parte non aggiornato: non cita feste, import da Calendar e ricorrenze (promemoria e colori corretti il 17/10/2026).
- Il nome del veicolo è anche la chiave del dizionario: rinominarlo ricrea la chiave (gestito correttamente, ma fragile).
