Feature: Testowanie endpointu GetCardRate

  Scenario: Weryfikacja poprawności odpowiedzi dla GetCardRateRequest
    Given przygotowano żądanie SOAP z szablonu w pliku "steps/request_getCardRate.xml" dla endpointu "https://example.com/pos/dcc/v1/GetCardRate"
      | ReferenceNumber | CardId | MerchantId       | Acquirer | BaseAmount |
      | 000000000000003 | 494050 | ABC9876543210001 | ACQ      | 100000     |
    When wysyłam żądanie SOAP
    Then odpowiedź powinna zawierać status "200 OK"
    And odpowiedź powinna zawierać poprawny kurs wymiany
