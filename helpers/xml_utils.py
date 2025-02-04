def load_template(template_path):
    """
    Ładuje szablon XML z pliku.
    """
    with open(template_path, 'r') as file:
        return file.read()

def fill_template(template, data):
    """
    Zastępuje placeholdery w szablonie XML wartościami z tabeli danych.
    """
    for key, value in data.items():
        placeholder = f"{{{{{key}}}}}"  # np. {{ReferenceNumber}}
        template = template.replace(placeholder, str(value))
    return template
