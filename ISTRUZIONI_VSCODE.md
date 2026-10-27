# Istruzioni per VS Code: togliere i dati da git

Questo file serve a far fare a VS Code (o a te nel terminale) i passaggi per **smettere di salvare i dati su git**, senza perderli.

## Come usarlo

**Con l'assistente di VS Code (Copilot Chat)**
1. In VS Code apri la cartella del programma (`C:\My_Designs\scadenze`).
2. Apri la chat di Copilot e scegli la modalità **Agent**.
3. Scrivi: `Segui le istruzioni in #file:ISTRUZIONI_VSCODE.md`
4. Approva i comandi che propone, uno alla volta, controllando che siano quelli elencati qui sotto.

**A mano**: apri il terminale di VS Code (menu *Terminale → Nuovo terminale*) e scrivi i comandi della sezione "Passi" uno alla volta.

---

## Prima di cominciare (nel programma, non in VS Code)

1. Apri il programma Gestione Scadenze.
2. In fondo alla finestra premi **📁 Cambia cartella dati…** e scegli la cartella su Google Drive, Dropbox, OneDrive o NAS.
3. Controlla che la scritta **💾 Dati:** in fondo alla finestra mostri la nuova cartella.

Se salti questo passo i dati restano solo su questo PC: non più su git, ma neanche su Drive.

---

## Contesto (per l'assistente)

- Progetto Python/tkinter "Gestione Scadenze" nella cartella `C:\My_Designs\scadenze`, sotto git.
- Il file dei dati `stato_veicolo.json` era tracciato da git e cambia a ogni appuntamento o scadenza aggiunta: ogni volta bisognava fare un commit.
- Ora il programma salva i dati in una cartella esterna scelta dall'utente (Drive, Dropbox, NAS), ricordata in `impostazioni_locali.json`. Ogni 7 giorni ne mette anche una copia in `backup/` nella cartella del programma.
- `.gitignore` contiene già `stato_veicolo.json`, `impostazioni_locali.json` e `backup/`. Ma `stato_veicolo.json` è ancora tracciato, quindi va tolto dall'indice di git.
- **Obiettivo**: smettere di tracciare `stato_veicolo.json` **senza cancellarlo dal disco** e fare il commit delle modifiche al codice e alla documentazione.

## Passi

1. Controlla la situazione:
   ```
   git status
   ```
2. Togli il file dati da git, lasciandolo sul disco (`--cached` è fondamentale):
   ```
   git rm --cached stato_veicolo.json
   ```
3. Aggiungi le modifiche al programma e alla documentazione:
   ```
   git add .gitignore main.py immagine_settimana.py README.md DOCUMENTAZIONE.md ISTRUZIONI_VSCODE.md
   ```
4. Controlla di nuovo:
   ```
   git status
   ```
   Tra le modifiche da salvare ("Changes to be committed") deve esserci `deleted: stato_veicolo.json`, ma il file deve **esistere ancora** nella cartella.
5. Fai il commit:
   ```
   git commit -m "Dati fuori da git: cartella dati scelta dal programma (Drive/Dropbox/NAS) e backup locale ogni 7 giorni"
   ```
6. Se il repository ha un remoto (il comando `git remote -v` mostra qualcosa), invialo:
   ```
   git push
   ```

## Controllo finale

- `git ls-files stato_veicolo.json` non deve stampare niente: il file non è più tracciato.
- `dir stato_veicolo.json` deve trovare il file: è ancora sul disco.
- `git status` deve dire che non c'è niente da salvare (al massimo qualche file non tracciato).
- Da adesso aggiungere appuntamenti o scadenze **non cambia più niente in git**.

## Regole per l'assistente

- **Non** cancellare `stato_veicolo.json` dal disco e **non** usare `git rm` senza `--cached`.
- **Non** aggiungere a git questi file: `impostazioni_locali.json`, `credentials.json`, `client_secret_*.json`, `token.pickle`, `backup/`, `report_medicinali.png`, `report_medicinali.pdf`, `riepilogo_settimana.png`.
- **Non** riscrivere la cronologia: niente `git filter-repo`, `git filter-branch`, `git reset --hard` o `git push --force`.
- **Non** modificare i file Python.
- Se `git status` mostra modifiche inattese, o se un comando dà errore, **fermati e chiedi** prima di continuare.

## Nota sulla cronologia di git

Le versioni vecchie di `stato_veicolo.json` restano nella cronologia di git, e su GitHub se il repository è stato inviato lì. Se il repository è **pubblico**, conviene renderlo **privato** dalle impostazioni di GitHub. Si possono anche cancellare dalla cronologia, ma vuol dire riscriverla: va fatto solo se serve davvero, e non con queste istruzioni.
