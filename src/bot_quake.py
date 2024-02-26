import unittest
import os
from urllib.request import urlopen
from datetime import date, timedelta
from telegram.ext import Application, Updater, CommandHandler, MessageHandler, filters
import ssl


# la funzione imposta i valori temporali dei dati da scaricare in un range che va dal giorno attuale indietro di un valore d_range
def get_date_range(d_range):
    date_range = [None] * 2
    today = date.today()
    today.strftime("%m/%d/%Y")
    days_inthe_past = today - timedelta(days=d_range)
    date_range[0] = days_inthe_past
    date_range[1] = today
    return date_range


# imposto una porzione del globo terrestre dalla quale estrapolare i dati
class ZoneMap:
    def __init__(self, zona=None):
        if zona == None:
            # I dati valori ristretti alle coordinate sotto sono impostati sull'area etnea
            self.minlat = 37
            self.maxlat = 38
            self.minlon = 14.5
            self.maxlon = 15.5


# funzioni che verranno assegnate ad un gestore legate ad un certo messaggio


# questa richiamata al messaggio /recente
# async nelle nuove versioni utile per creare task parallelizzati
async def file_reader(update, context):
    # Imposto la ricerca dei dati fino a 7 giorni indietro
    intervallo_date = get_date_range(
        7
    )
    # instanzio la zona di interesse ovvero massimo e minimo di latitudine e longitudine 
    zona = (
        ZoneMap()
    )  
    comandi = update.message.text
    # Adesso il comando passato è diviso e ne posso gestire le eventuali funzionalità
    splitted_command = (
        comandi.split()
    )
    # Imposto la magnitudo massima che non deve superare 10, questa potra
    massima_magnitudo = (
        10  
    )
  
      

    if len(splitted_command) > 1:
        if splitted_command[1].isnumeric():
            if int(splitted_command[1]) < 10 and int(splitted_command[1]) > 0:
                massima_magnitudo = splitted_command[
                    1
                ]  # Impostiamo la magnitudo passata dal comando che poi passeremo all'url
            else:
                await update.message.reply_text("Inserire un numero da 1 a 10")
                return
        else:
            await update.message.reply_text(
                "Inserire un numero da 1 a 10 rilevati caratteri non numerici"
            )
            return
            

    filename = f"https://webservices.ingv.it/fdsnws/event/1/query?starttime={intervallo_date[0]}T00%3A00%3A00&endtime={intervallo_date[1]}T23%3A59%3A59&minmag=-1&maxmag={massima_magnitudo}&mindepth=-10&maxdepth=1000&minlat={zona.minlat}&maxlat={zona.maxlat}&minlon={zona.minlon}&maxlon={zona.maxlon}&minversion=100&orderby=time-asc&format=text&limit=100"

    if filename:
        context = ssl._create_unverified_context()  # serve per il certificato ssl
        with urlopen(
            filename, context=context
        ) as f:  # Ricordiamoci ce il filename è remoto
            file_lines = [x.decode("utf8").strip() for x in f.readlines()]
            if len(file_lines) == 0:
                # print("Se il file è vuoto quindi non ci sono dati in funzione dei parametri inseriti")
                await update.message.reply_text(
                    "Nell'arco di tempo rilevato non ci sono dati relativi ai parametri richiesti"
                )
            else:
                file_header_line = file_lines[0].split("|")
                file_header_line[0] = file_header_line[0].replace("#", "")
                file_body_line = file_lines[1].split("|")  # splitting sulle righe

                reply_string = "Dati relativi all'evento sismico più recente: "
                for i in range(len(file_header_line)):
                    file_header_line[i] = file_header_line[i].replace("\n", "")
                    reply_string = (
                        reply_string
                        + "\n"
                        + file_header_line[i]
                        + ": "
                        + file_body_line[i]
                    )
                await update.message.reply_text(reply_string)
                # questi di seguito sono i dati per la creazione della mappa
                await update.message.reply_venue(
                    file_body_line[2],  # latitudine
                    file_body_line[3],  # longitudine
                    file_body_line[12],  # LocationName
                    f"Profondità: {file_body_line[4]}",
                )
                await update.message.reply_text(MENU)


# questa invocata al messaggio /descrizione
async def start(update, context):
    await update.message.reply_text(
        """Benvenuto in BOTQUAKE questo è un sistema automatizzato per visualizzare l'ultimo evento sismico tra gli eventi degli ultimi 7 giorni in una zona di interesse intorno al vulcano Etna.
Inserisci un comando e un bot ti invierà le informazioni in base al comando digitato.\n"""
    )
    await update.message.reply_text(MENU)


# questa invocata al messaggio /info
async def info(update, context):
    await update.message.reply_text(
        """
I dati e i risultati pubblicati sulle pagine dall'INGV al link https://terremoti.ingv.it/
e sono distribuiti sotto licenza Creative Commons Attribution 4.0 International License,
con le condizioni al seguente link https://creativecommons.org/licenses/by/4.0
"""
    )
    await update.message.reply_text(MENU)


# funzione ausiliaria
async def handle_message(update, context):
    await update.message.reply_text(
        f"Hai scritto {update.message.text}, usa / seguito da un comando valido"
    )
    await update.message.reply_text(MENU)


MENU = """Sotto troverai la lista comandi:
/descrizione -> Descrizione del canale.
/recente -> Per visualizzare evento sismico più recente, se il comando è seguito da un numero da 1 a 10 cambia la magnitudo massima.
/info -> Mostra link utili e informazioni sui dati.
"""


def main() -> None:
    TOKEN = os.environ["TELEGRAM_BOT"]
    # con pyhton 3.12 e versione python-telegram-bot  20.8
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("info", info))
    application.add_handler(CommandHandler("recente", file_reader))
    application.add_handler(CommandHandler("descrizione", start))
    application.add_handler(MessageHandler(filters.TEXT, handle_message))
    application.run_polling()


if __name__ == "__main__":
    main()
