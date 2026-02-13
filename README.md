# bnet_iss_automation_sit (Behave + TCP/IP localhost server)

Ten projekt to szkielet automatyzacji w stylu BDD (Behave), gdzie testy wysyłają "transakcje" jako pola ISO (dict)
do lokalnego serwera TCP (`localhost`) i walidują odpowiedź.

## Struktura
- `features/` – pliki `.feature`, hooki `environment.py`, kroki w `features/steps/`
- `src/` – klient TCP i helpery (budowanie, wysyłka, walidacja)
- `server/` – prosty serwer TCP do testów (mock systemu "bnet")

## Szybki start

### 1) Instalacja
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate

pip install -r requirements.txt
```

### 2) Uruchom serwer TCP (w osobnym terminalu)
```bash
python -m server.tcp_server
```

Domyślnie serwer słucha na `127.0.0.1:5000`.

### 3) Uruchom testy Behave
```bash
ENV=SIT BN_HOST=127.0.0.1 BN_PORT=5000 behave -f progress
```

## Protokół (dla testów)
Klient wysyła jedną linię JSON zakończoną `\n`:
```json
{"MTI":"0100","DE002":"...","DE004":"000000000100", "...":"..."}
```

Serwer odpowiada też jedną linią JSON zakończoną `\n`, np.:
```json
{"MTI":"0110","DE039":"00","ECHO":{"MTI":"0100",...}}
```

## Tagowanie scenariuszy
- `@no-login` – pomija logowanie w hooku
- `@keep-session` – utrzymuje sesję między scenariuszami
