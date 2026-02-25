Feature: CREDENTIAL ON FILE BASIC TRANSACTIONS

  Background:
    Given bnet is logged into the process


  Scenario: TESTCASE 0001 - CREDENTIAL ON FILE PURCHASE NO CVM
    Given the card details
      | CARD_NUMBER        | PVV   | EXPIRY_DATE |
      | 5575061111100075   | 12345 | 2907        |
    Given the transaction with the following data
      | FIELD | VALUE                                               |
      | MTI   | 0100                                                |
      | DE002 | {CARD}                                              |
      | DE003 | 000000                                              |
      | DE004 | 000000000100                                        |
      | DE006 | 000000000100                                        |
      | DE007 | {TIME}                                              |
      | DE010 | 61000000                                            |
      | DE011 | {STAN}                                              |
      | DE012 | {LOCAL_TIME}                                        |
      | DE013 | {DATE}                                              |
      | DE014 | {EXPIRY_DATE}                                       |
      | DE015 | {DATE}                                              |
      | DE016 | {DATE}                                              |
      | DE018 | 5045                                                |
      | DE022 | 100                                                 |
      | DE032 | 007657                                              |
      | DE037 | {RRN}                                               |
      | DE041 | 56274012                                            |
      | DE042 | 0006600333                                          |
      | DE043 | PL AUTOM   REG COF   WARSZAWA   POL                |
      | DE048 | {"TCC":{"SE001":"T"},"SUBELEMENTS":{}}        |
      | DE049 | 985                                                 |
      | DE051 | 985                                                 |
      | DE061 | 2031104000000616902101234                          |
      | DE063 | {TRACE_ID}                                          |
    When the transaction is sent
    Then the response should contain fields
      | FIELD |
      | MTI   |
      | DE039 |

  Scenario: Transaction using provided card details
    Given the card details
      | CARD_NUMBER        | PVV   | EXPIRY_DATE |
      | 5575061111100075   | 12345 | 2907        |
    Given the transaction with the following data
      | FIELD | VALUE         |
      | MTI   | 0100          |
      | DE002 | {CARD}        |
      | DE014 | {EXPIRY_DATE} |
      | DE003 | 000000        |
      | DE004 | 000000000100  |
      | DE011 | {STAN}        |
      | DE037 | {RRN}         |
      | DE063 | {TRACE_ID}    |
    When the transaction is sent
    Then the response should be validated
      | FIELD | EXPECTED_VALUE |
      | MTI   | 0110           |
      | DE039 | 00             |

  Scenario: Transaction using DEFAULT card (no card table provided)
    Given the card details
      | CARD_NUMBER        | PVV   | EXPIRY_DATE |
      | 5575061111100075   | 12345 | 2907        |
    Given the transaction with the following data
      | FIELD | VALUE         |
      | MTI   | 0100          |
      | DE002 | {CARD}        |
      | DE014 | {EXPIRY_DATE} |
      | DE003 | 000000        |
      | DE004 | 000000000100  |
    When the transaction is sent
    Then the response should contain fields
      | FIELD |
      | MTI   |
      | DE039 |

  Scenario: Negative - should fail (wrong expected value)
    Given the card details
      | CARD_NUMBER        | PVV   | EXPIRY_DATE |
      | 5575061111100075   | 12345 | 2907        |
    Given the transaction with the following data
      | FIELD | VALUE        |
      | MTI   | 0100         |
      | DE003 | 000000       |
      | DE004 | 000000000100 |
    When the transaction is sent
    Then the response should be validated
      | FIELD | EXPECTED_VALUE |
      | MTI   | 0110           |
      | DE039 | 00             |

Scenario: Authorization + Reversal (auto DE090)
  Given the card details
    | CARD_NUMBER        | PVV   | EXPIRY_DATE |
    | 5575061111100075   | 12345 | 2907        |
  Given the transaction with the following data
    | FIELD | VALUE        |
    | MTI   | 0100         |
    | DE003 | 000000       |
    | DE004 | 000000000100 |
    | DE011 | {STAN}       |
    | DE037 | {RRN}        |
  When the transaction is sent
  Then the response should be validated
    | FIELD | EXPECTED_VALUE |
    | MTI   | 0110           |
    | DE039 | 00             |
  Then save the authorization context

  Given the transaction with the following data
    | FIELD | VALUE   |
    | MTI   | 0400    |
    | DE003 | 000000  |
    | DE004 | {DE004} |
    | DE011 | {STAN}  |
    | DE037 | {DE037} |
    | DE038 | {DE038} |
    | DE090 | {DE090} |
  When the transaction is sent
  Then the response should be validated
    | FIELD | EXPECTED_VALUE |
    | MTI   | 0410           |
    | DE039 | 00             |

Scenario: Partial Reversal (smaller amount)
  Given the card details
    | CARD_NUMBER        | PVV   | EXPIRY_DATE |
    | 5575061111100075   | 12345 | 2907        |
  Given the transaction with the following data
    | FIELD | VALUE        |
    | MTI   | 0100         |
    | DE003 | 000000       |
    | DE004 | 000000000100 |
    | DE011 | {STAN}       |
    | DE037 | {RRN}        |
  When the transaction is sent
  Then the response should be validated
    | FIELD | EXPECTED_VALUE |
    | MTI   | 0110           |
    | DE039 | 00             |
  Then save the authorization context

  Given the transaction with the following data
    | FIELD | VALUE        |
    | MTI   | 0400         |
    | DE003 | 000000       |
    | DE004 | 000000000050 |
    | DE011 | {STAN}       |
    | DE037 | {DE037}      |
    | DE038 | {DE038}      |
    | DE090 | {DE090}      |
  When the transaction is sent
  Then the response should be validated
    | FIELD | EXPECTED_VALUE |
    | MTI   | 0410           |
    | DE039 | 00             |

Scenario: Negative Reversal (no original found)
  Given the card details
    | CARD_NUMBER        | PVV   | EXPIRY_DATE |
    | 5575061111100075   | 12345 | 2907        |
  Given the transaction with the following data
    | FIELD | VALUE        |
    | MTI   | 0400         |
    | DE003 | 000000       |
    | DE004 | 000000000050 |
    | DE011 | {STAN}       |
    | DE037 | 000000000000 |
    | DE090 | 0100000000000000000000 |
  When the transaction is sent
  Then the response should be validated
    | FIELD | EXPECTED_VALUE |
    | MTI   | 0410           |
    | DE039 | 00             |
