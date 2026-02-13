Feature: CREDENTIAL ON FILE BASIC TRANSACTIONS

  Background:
    Given bnet is logged into the process

  Scenario: Perform transaction with CREDENTIAL ON FILE PURCHASE NO CVM (happy path)
    And the card details
      | CARD_NUMBER      | EXPIRY_DATE |
      | 5575061111100075 | 2907        |
    And the transaction with the following data
      | FIELD | VALUE          |
      | MTI   | 0100           |
      | DE002 | {CARD}         |
      | DE003 | 000000         |
      | DE004 | 000000000100   |
      | DE014 | {EXPIRE_DATE}  |
      | DE011 | {STAN}         |
      | DE037 | {RRN}          |
      | DE063 | {TRACE_ID}     |
    When the transaction is sent
    Then the response should be validated
      | FIELD | EXPECTED_VALUE |
      | MTI   | 0110           |
      | DE039 | 00             |
