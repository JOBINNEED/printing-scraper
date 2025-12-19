def extract_manufacturer(title: str) -> str:
    manufacturers = [
        'Heidelberg', 'Komori', 'Manroland', 'KBA', 'Bobst', 'HP', 'Canon',
        'Xerox', 'Konica', 'Ricoh', 'Roland', 'MAN', 'Mitsubishi', 'Ryobi',
        'Hamada', 'Sakurai', 'Adast', 'Planeta', 'Solna', 'Goss'
    ]

    title_upper = title.upper()
    for mfr in manufacturers:
        if mfr.upper() in title_upper:
            return mfr

    return None

def extract_model(title: str) -> str:
    parts = title.split()
    if len(parts) > 1:
        for i, part in enumerate(parts):
            if any(char.isdigit() for char in part) and len(part) > 2:
                return ' '.join(parts[i:i+2])
    return None
