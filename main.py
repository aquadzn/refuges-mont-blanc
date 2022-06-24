import time

from twilio.rest import Client
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException

import config


SECONDES_ATTENTE = 60*1
INFOS_REFUGES = ((0, "Refuge du Goûter"), (2, "Refuge de Tête Rousse"))
NB_PERSONNES = 1
DATE_RECHERCHE = "04/07/2022"


def get_twilio_client() -> Client:
    return Client(config.TWILIO_SID, config.TWILIO_AUTH_TOKEN)


def get_driver() -> webdriver.Chrome:
    service = Service(executable_path=config.CHROMEDRIVER_PATH)
    options = Options()
    options.headless = True

    return webdriver.Chrome(options=options, service=service)


def main():
    driver = get_driver()

    driver.get("https://montblanc.ffcam.fr/reservation-tout-public.html")

    # driver.find_element(By.ID, "tarteaucitronAllDenied2").click()
    iframe = driver.find_element(By.ID, "if_booking")
    driver.switch_to.frame(iframe)

    # Connexion au site de réservation
    driver.find_element(By.ID, "checkoutEmail").send_keys(config.FFCAM_EMAIL)
    driver.find_element(By.ID, "checkoutPasswd").send_keys(config.FFCAM_PASSWORD)
    driver.find_element(By.XPATH, "//input[@value='Valider' and @type='submit']").click()

    # File d'attente...
    time.sleep(SECONDES_ATTENTE)

    try:
        # Deux personnes
        driver.find_element(By.ID, "pax").clear()
        driver.find_element(By.ID, "pax").send_keys(NB_PERSONNES)

        # Mois de juillet
        date_picker = driver.find_element(By.ID, "date")
        date_picker.clear()
        date_picker.click()
        date_picker.send_keys(DATE_RECHERCHE)

        # Vérification pour le refuge du Gouter et celui de Tête Rousse
        for id_refuge, nom_refuge in INFOS_REFUGES:

            # Choix du refuge
            select_element = driver.find_element(By.ID, "structure")
            select_object = Select(select_element)
            select_object.select_by_index(id_refuge)

            # Rechercher
            driver.find_element(By.XPATH, "//input[@value='Rechercher' and @type='submit']").click()

            # Liste des dates disponibles
            dates_dispo = [
                [jour, int(place)] for jour, place in [
                    date.text.split("\n") for date in driver.find_elements(By.CLASS_NAME, "ui-state-DISPO")
                ]
                if int(place) >= NB_PERSONNES
            ]

            if dates_dispo:
                message = f"{nom_refuge}\n"
                for jour, place in dates_dispo:
                    message += f"{jour} juillet: {place} places\n"

                # # Connexion à Twilio
                # client = get_twilio_client()
                
                # # Envoi du SMS
                # sms = client.messages.create(
                #     messaging_service_sid=config.MESSAGING_SID,
                #     body=message,
                #     to=config.PHONE_NUMBER
                # )

                # print(sms.sid)

                print(message)

                time.sleep(10)

    except NoSuchElementException:
        print("Toujours en file d'attente...")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
