import sys
import os
import requests
from pytest_bdd import scenarios, given, when, then
from helpers.logger import setup_logger
from helpers.xml_utils import load_template, fill_template

# Dynamiczne dodanie ścieżki do głównego katalogu projektu
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

# Ładowanie scenariuszy z pliku feature
scenarios('../features/getCardRate.feature')

# Logger
logger = setup_logger("GetCardRate Steps")

# Zmienna globalna na odpowiedź
response = None


@given('przygotowano żądanie SOAP z szablonu w pliku "<template_path>" dla endpointu "<endpoint>"', target_fixture="soap_request")
def prepare_soap_request(template_path, endpoint, table):
    """
    Przygotowuje żądanie SOAP na podstawie szablonu XML i danych z tabeli w Gherkin.
    """
    # Pobranie danych z tabeli
    data = table[0]  # Zakładamy jedną linię w tabeli danych

    # Wczytanie szablonu XML
    template_path = os.path.join(os.path.dirname(__file__), template_path)  # Ustawienie poprawnej ścieżki
    template = load_template(template_path)

    # Wypełnienie szablonu danymi
    request_xml = fill_template(template, data)

    logger.info(f"Przygotowywanie żądania SOAP dla endpointu: {endpoint}")
    return {"endpoint": endpoint, "xml": request_xml}


@when('wysyłam żądanie SOAP')
def send_soap_request(soap_request):
    """
    Wysyła żądanie SOAP do endpointu i zapisuje odpowiedź.
    """
    global response
    logger.info(f"Wysyłanie żądania SOAP do: {soap_request['endpoint']}")
    headers = {"Content-Type": "text/xml; charset=utf-8"}
    response = requests.post(soap_request["endpoint"], data=soap_request["xml"], headers=headers)
    logger.info(f"Otrzymano odpowiedź: {response.status_code}")
    return response


@then('odpowiedź powinna zawierać status "200 OK"')
def verify_response_status():
    """
    Weryfikuje, czy odpowiedź ma status 200.
    """
    assert response.status_code == 200, f"Status odpowiedzi: {response.status_code}"


@then('odpowiedź powinna zawierać poprawny kurs wymiany')
def verify_exchange_rate():
    """
    Weryfikuje, czy odpowiedź zawiera dane kursu wymiany.
    """
    assert "<ExchangeRate>" in response.text, "Brak elementu ExchangeRate w odpowiedzi"
