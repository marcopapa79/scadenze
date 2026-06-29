"""
Sistema di notifiche desktop per le scadenze veicoli
"""
from plyer import notification
from datetime import datetime

SOGLIA_KM_PREAVVISO = 3500
SOGLIA_GIORNI_PREAVVISO = 30


def controlla_e_notifica(dati_veicolo):
    """
    Controlla tutte le scadenze e invia notifiche per quelle critiche
    """
    nome_veicolo = dati_veicolo.get("nome_veicolo", "Veicolo")
    targa = dati_veicolo.get("targa", "")
    km_attuali = dati_veicolo.get("km_attuali", 0)
    
    notifiche_inviate = []
    
    # Controlla scadenze temporali
    oggi = datetime.now().date()
    for voce, data_str in dati_veicolo.get("scadenze_fisse", {}).items():
        try:
            data_scadenza = datetime.strptime(data_str, "%Y-%m-%d").date()
            giorni_rimasti = (data_scadenza - oggi).days
            
            if giorni_rimasti < 0:
                # ROSSO - SCADUTO
                invia_notifica_critica(
                    f"⚠️ SCADENZA SUPERATA - {nome_veicolo}",
                    f"{voce} SCADUTO da {abs(giorni_rimasti)} giorni!\nTarga: {targa}"
                )
                notifiche_inviate.append(f"{voce} - SCADUTO")
                
            elif giorni_rimasti <= SOGLIA_GIORNI_PREAVVISO:
                # GIALLO - IN SCADENZA
                invia_notifica_avviso(
                    f"⚠️ Attenzione Scadenza - {nome_veicolo}",
                    f"{voce} in scadenza tra {giorni_rimasti} giorni\nTarga: {targa}"
                )
                notifiche_inviate.append(f"{voce} - {giorni_rimasti} giorni")
        except:
            pass
    
    # Controlla scadenze chilometriche
    for voce, info in dati_veicolo.get("scadenze_chilometriche", {}).items():
        km_residui = info["prossimo_km"] - km_attuali
        
        if km_residui <= 0:
            # ROSSO - SUPERATO
            invia_notifica_critica(
                f"⚠️ MANUTENZIONE SUPERATA - {nome_veicolo}",
                f"{voce} SUPERATO di {abs(km_residui)} km!\nKm attuali: {km_attuali}\nTarga: {targa}"
            )
            notifiche_inviate.append(f"{voce} - SUPERATO")
            
        elif km_residui <= SOGLIA_KM_PREAVVISO:
            # GIALLO - PROSSIMO
            invia_notifica_avviso(
                f"⚠️ Attenzione Manutenzione - {nome_veicolo}",
                f"{voce} tra {km_residui} km\nKm attuali: {km_attuali}\nTarga: {targa}"
            )
            notifiche_inviate.append(f"{voce} - {km_residui} km")
    
    return notifiche_inviate


def invia_notifica_critica(titolo, messaggio):
    """Invia una notifica critica (rossa)"""
    try:
        notification.notify(
            title=titolo,
            message=messaggio,
            app_name="Gestione Scadenze",
            timeout=15,  # 15 secondi
        )
    except Exception as e:
        print(f"Errore invio notifica: {e}")


def invia_notifica_avviso(titolo, messaggio):
    """Invia una notifica di avviso (gialla)"""
    try:
        notification.notify(
            title=titolo,
            message=messaggio,
            app_name="Gestione Scadenze",
            timeout=10,  # 10 secondi
        )
    except Exception as e:
        print(f"Errore invio notifica: {e}")


def controlla_tutti_veicoli(dati_completi):
    """
    Controlla tutti i veicoli e le scadenze personali e invia notifiche
    Restituisce un riepilogo delle notifiche inviate
    """
    riepilogo = {}
    
    # Controlla veicoli
    for nome_veicolo, dati in dati_completi.get("veicoli", {}).items():
        notifiche = controlla_e_notifica(dati)
        if notifiche:
            riepilogo[nome_veicolo] = notifiche
    
    # Controlla scadenze personali
    notifiche_personali = controlla_scadenze_personali(dati_completi.get("scadenze_personali", {}))
    if notifiche_personali:
        riepilogo["📋 Scadenze Personali"] = notifiche_personali
    
    return riepilogo


def controlla_scadenze_personali(scadenze_personali):
    """
    Controlla le scadenze personali e invia notifiche
    Gestisce sia il vecchio formato (stringhe) che il nuovo (dict con orari)
    """
    notifiche_inviate = []
    oggi = datetime.now().date()
    
    for voce, data_obj in scadenze_personali.items():
        try:
            # Gestisci sia il vecchio formato (stringa) che il nuovo (dict)
            if isinstance(data_obj, str):
                data_str = data_obj
            else:
                data_str = data_obj.get('data', '')
            
            data_scadenza = datetime.strptime(data_str, "%Y-%m-%d").date()
            giorni_rimasti = (data_scadenza - oggi).days
            
            if giorni_rimasti < 0:
                # ROSSO - SCADUTO
                invia_notifica_critica(
                    f"⚠️ SCADENZA PERSONALE SUPERATA",
                    f"{voce} SCADUTO da {abs(giorni_rimasti)} giorni!"
                )
                notifiche_inviate.append(f"{voce} - SCADUTO")
                
            elif giorni_rimasti <= SOGLIA_GIORNI_PREAVVISO:
                # GIALLO - IN SCADENZA
                invia_notifica_avviso(
                    f"⚠️ Attenzione Scadenza Personale",
                    f"{voce} in scadenza tra {giorni_rimasti} giorni"
                )
                notifiche_inviate.append(f"{voce} - {giorni_rimasti} giorni")
        except:
            pass
    
    return notifiche_inviate


if __name__ == "__main__":
    # Test delle notifiche
    print("Test notifiche desktop...")
    
    invia_notifica_avviso(
        "Test Notifica Avviso",
        "Questa è una notifica di test gialla"
    )
    
    print("Notifica di test inviata!")
