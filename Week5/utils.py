from flask import request

def get_json_or_400():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValueError("Invalid JSON body")
    return data

def paginate_query_offset_limit(query, offset, limit):
    total = query.count()
    items = query.offset(offset).limit(limit).all()
    return total, items

def parse_offset_limit():
    try:
        offset = int(request.args.get("offset", 0))
        limit = int(request.args.get("limit", 10))
    except ValueError:
        raise ValueError("Invalid pagination")
    offset = 0 if offset < 0 else offset
    limit = 1 if limit < 1 else limit
    return offset, limit
