import binascii


class ISO8583Parser:
    def __init__(self, message):
        self.message = message
        self.parsed_data = {}

    def parse(self):
        # 1. Pobranie nagłówka (Header)
        header_length = 12  # Nagłówek ma 12 znaków
        self.parsed_data["Header"] = self.message[:header_length]
        print(f"Header: {self.parsed_data['Header']}")

        # 2. Pobranie MTI (Message Type Indicator)
        self.parsed_data["MTI"] = self.message[header_length:header_length + 4]
        print(f"MTI: {self.parsed_data['MTI']}")

        # 3. Pobranie bitmapy pierwotnej (16 znaków HEX -> 64 bity)
        primary_bitmap_hex = self.message[header_length + 4:header_length + 20]
        primary_bitmap_bin = bin(int(primary_bitmap_hex, 16))[2:].zfill(64)
        self.parsed_data["Primary Bitmap"] = primary_bitmap_bin
        print(f"Primary Bitmap: {primary_bitmap_bin}")

        # 4. Sprawdzenie, czy występuje bitmapa wtórna
        index = header_length + 20  # Przesunięcie indeksu po bitmapie
        if primary_bitmap_bin[0] == "1":
            secondary_bitmap_hex = self.message[index:index + 16]
            secondary_bitmap_bin = bin(int(secondary_bitmap_hex, 16))[2:].zfill(64)
            self.parsed_data["Secondary Bitmap"] = secondary_bitmap_bin
            print(f"Secondary Bitmap: {secondary_bitmap_bin}")
            bitmap_bin = primary_bitmap_bin + secondary_bitmap_bin
            index += 16
        else:
            bitmap_bin = primary_bitmap_bin

        # 5. Definicja pól danych (pełen zakres ISO 8583)
        field_definitions = {
            2: ('LLVAR', 19),  # PAN (Primary Account Number)
            3: ('FIXED', 6),  # Processing Code
            4: ('FIXED', 12),  # Amount, Transaction
            7: ('FIXED', 10),  # Transmission Date & Time
            11: ('FIXED', 6),  # Systems Trace Audit Number (STAN)
            12: ('FIXED', 6),  # Local Transaction Time (hhmmss)
            13: ('FIXED', 4),  # Local Transaction Date (MMDD)
            14: ('FIXED', 4),  # Expiration Date (YYMM)
            18: ('FIXED', 4),  # Merchant Type
            22: ('FIXED', 3),  # POS Entry Mode
            32: ('LLVAR', 11),  # Acquiring Institution ID
            37: ('FIXED', 12),  # Retrieval Reference Number (RRN)
            38: ('FIXED', 6),  # Authorization Identification Response
            39: ('FIXED', 2),  # Response Code
            41: ('FIXED', 8),  # Card Acceptor Terminal ID
            42: ('FIXED', 15),  # Merchant ID
            44: ('LLVAR', 25),  # Additional Response Data
            45: ('LLVAR', 76),  # Track 1 Data (if used)
            48: ('LLLVAR', 999),  # Additional Data (Private)
            49: ('FIXED', 3),  # Currency Code
            52: ('FIXED', 16),  # Personal Identification Number (PIN)
            54: ('LLLVAR', 120),  # Additional Amounts
            55: ('LLLVAR', 255),  # EMV Data
            57: ('LLLVAR', 999),  # Custom Transaction Data
            60: ('LLLVAR', 999),  # Reserved for Private Use
            61: ('LLLVAR', 999),  # Private Field 1
            62: ('LLLVAR', 999),  # Private Field 2
            63: ('LLLVAR', 999),  # Private Reserved Field
            64: ('FIXED', 16),  # MAC (Message Authentication Code)
            102: ('LLVAR', 28),  # Account Identification 1
            103: ('LLVAR', 28),  # Account Identification 2
            123: ('LLLVAR', 999),  # POS Data Code
        }

        # 6. Parsowanie pól danych zgodnie z bitmapą
        for i in range(2, len(bitmap_bin) + 1):  # Pola 2-128
            if i <= len(bitmap_bin) and bitmap_bin[i - 1] == "1":  # Jeśli bit ustawiony
                if i in field_definitions:
                    field_type, max_length = field_definitions[i]

                    if field_type == "FIXED":
                        field_value = self.message[index:index + max_length]
                        index += max_length

                    elif field_type == "LLVAR":
                        length = int(self.message[index:index + 2])  # Pobranie długości
                        index += 2  # Przesunięcie wskaźnika po długości
                        field_value = self.message[index:index + length]
                        index += length

                    elif field_type == "LLLVAR":
                        length = int(self.message[index:index + 3])  # Pobranie długości
                        index += 3  # Przesunięcie wskaźnika po długości
                        field_value = self.message[index:index + length]
                        index += length

                    self.parsed_data[f"Field {i}"] = field_value

        return self.parsed_data


# 🔹 Przykładowa wiadomość ISO 8583 (z nagłówkiem "Header")
message = "ISO0260000000200B23CC40128E1801A0000000010009C00000000000000003100022009U047" \
          "1040470220261102259990210375117560454512686=26112061121307820000" \
          "{RRN}62286599 73091613 POS MARIUSZA Warszawa PL02776043569 " \
          "000 000985016POL BEA1+0000000019POL 0000000000472& 0000200472! B000450 " \
          "p000901001001012121250125020033023000000000101132430004 000"

parser = ISO8583Parser(message)
parsed_output = parser.parse()

# 🔹 Wyświetlenie wyniku
for field, value in parsed_output.items():
    print(f"{field}: {value}")
