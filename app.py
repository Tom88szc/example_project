@app.route('/merchant/<string:terminal_prdf>')
def terminal_detail_prdf(terminal_prdf):
    db_handler = get_database_handler()
    db_handler.connect()

    try:
        # Pobieranie terminu wyszukiwania z parametrów zapytania
        search_term = request.args.get('search', '')

        page, per_page, _ = get_page_args(page_parameter='page', per_page_parameter='per_page')
        per_page = per_page or 30

        # Konstruowanie zapytania SQL z klauzulą WHERE dla wyszukiwania
        prdf_query = """
            SELECT * FROM G6S.PRDF1
            WHERE RETAILER_ID = :terminal_prdf
        """
        if search_term:
            prdf_query += " AND (column_name LIKE :search_term)"  # Zastąp column_name faktyczną nazwą kolumny, którą chcesz przeszukiwać
            params = [terminal_prdf, f'%{search_term}%']
        else:
            params = [terminal_prdf]

        prdf = db_handler.fetch_ptd_data(prdf_query, params=params)
        total = len(prdf)
        prdf_page = prdf[(page - 1) * per_page: page * per_page]
        pagination = Pagination(page=page, total=total, record_name='transactions', per_page=per_page)

        # Modyfikowanie wyniku przy użyciu self.caf
        enhanced_transactions = []
        for transaction in prdf_page:
            enhanced_transaction = {}
            for key, value in transaction.items():
                description = db_handler.descriptions['PTD'].get(key, {})

                # Sprawdzenie, czy klucz istnieje w self.caf
                if key in self.caf:
                    example_caf = self.caf[key]
                    enhanced_transaction[key] = {
                        "value": value,
                        "description": description,
                        "example_caf": example_caf
                    }
                else:
                    enhanced_transaction[key] = {
                        "value": value,
                        "description": description
                    }
            enhanced_transactions.append(enhanced_transaction)

        return render_template('prdf_detail.html', prdf=enhanced_transactions, terminal_prdf=terminal_prdf,
                               pagination=pagination)

    except Exception as e:
        return str(e), 500




<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Process Detail</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='styles.css') }}">
</head>
<body>
    <div class="container">
        <span class="back-button-wrapper">
            <a href="./" class="back-button">Back to Monitoring</a>
        </span>
        <h1>Response Code: {{ resp_code }}</h1>

        <!-- Search Form -->
        <form method="GET" action="{{ url_for('terminal_detail_prdf', terminal_prdf=terminal_prdf) }}">
            <input type="text" name="search" placeholder="Search..." value="{{ request.args.get('search', '') }}">
            <button type="submit">Search</button>
        </form>

        <!-- Results Table -->
        <table>
            <thead>
                <tr>
                    <th>Key</th>
                    <th>Value</th>
                    <th>Description</th>
                    <th>Example CAF</th>
                </tr>
            </thead>
            <tbody>
                {% for transaction in transactions %}
                <tr>
                    <td>{{ transaction['key'] }}</td>
                    <td>{{ transaction['value'] }}</td>
                    <td>{{ transaction['description'] }}</td>
                    <td>{{ transaction['example_caf'] }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>

        <nav aria-label="Page navigation example">
            <ul class="pagination">
                {{ pagination.links }}
            </ul>
        </nav>
    </div>
</body>
</html>





