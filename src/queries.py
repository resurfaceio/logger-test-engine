fetch_data = """
    SELECT request_body, request_headers, response_body
    FROM resurface.data.message WHERE request_headers LIKE '%{id_}%'
"""
