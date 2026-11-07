"""Source-verified layout annotations for specific tables in the 2026/27 PDF.

Annotations belong to the chunk section label and are not verbatim quotations.
They preserve page-bounded source text while expressing lost table relationships.
The caller must verify the reviewed PDF and baseline extraction hashes first.
"""

ANNOTATIONS = {
    "sec8_H_002": (
        "PDF table layout: UGC-funded bachelor's degree fees are: local full-time "
        "HK$47,000/academic year, local part-time HK$1,570/credit; non-local "
        "full-time HK$200,000/academic year, non-local part-time HK$6,670/credit."
    ),
    "sec8_I_001": (
        "PDF admission-fee table: for applications not processed through JUPAS, "
        "taught postgraduate MBA HK$800, Faculty of Business doctoral programmes "
        "HK$1,200, and other taught postgraduate programmes HK$500."
    ),
    "sec8_I_002": (
        "PDF footnote layout: 'footnote 11' is footnote 1, on gown hiring; "
        "'100/copy2' means HK$100/copy with footnote 2, not 100 per copy squared."
    ),
    "sec12_C_008": (
        "PDF contact layout: the counselling email address is "
        "stud.counselling@polyu.edu.hk (the source line wrap splits the address)."
    ),
    "sec12_C_009": (
        "PDF table layout: when days and times are grouped separately within a "
        "facility row, pair them in their displayed order. Global Student Hub: "
        "Monday to Sunday 9.00 am–11.00 pm; other general holidays closed. "
        "The Kwong On Jubilee Sports Centre row continues on PDF page 117 (printed page 98)."
    ),
    "sec12_C_010": (
        "PDF table layout: the first squash-court row continues the Kwong On "
        "Jubilee Sports Centre venue from printed page 97. In the opening-hours "
        "table, each facility's first hours block is opening hours and its second "
        "is booking sessions; the duplicated Block X and X202 blocks belong to "
        "those two respective columns. Statutory holidays are closed, and counter "
        "service stops at 10.00 pm."
    ),
    "sec12_D_002": (
        "PDF clinic contact table: Medical Clinic: 2766 5433, Room A001; "
        "Traditional Chinese Medicine Clinic: 2766 5553, Room A125; "
        "Dental Clinic: 2330 9414, Room GH020."
    ),
    "sec12_F_001": (
        "PDF catering table, day-to-hours pairs: Block Y Outlet: Monday–Friday "
        "8.00 am–8.00 pm, Saturday 9.00 am–6.00 pm, Sunday and public holiday closed; "
        "Communal Student Canteen: Monday–Friday 7.30 am–8.30 pm, Saturday "
        "7.30 am–7.30 pm, Sunday and public holiday 9.00 am–7.00 pm; "
        "Communal Staff Restaurant: Monday–Sunday and public holiday 11.00 am–10.30 pm; "
        "Communal Student Restaurant: Monday–Friday 10.30 am–8.00 pm, Saturday "
        "10.30 am–5.00 pm, Sunday and public holiday closed; Gourmet Shop: "
        "Monday–Friday 8.00 am–7.30 pm, Saturday, Sunday and public holiday closed."
    ),
    "sec12_F_002": (
        "PDF catering table, day-to-hours pairs: H Cafe: Monday–Friday 8.00 am–10.00 pm, "
        "Saturday 8.00 am–6.00 pm, Sunday and public holiday 10.00 am–6.00 pm; "
        "Staff Club Restaurant: Monday–Saturday 11.00 am–9.30 pm, Sunday and public holiday closed; "
        "Theatre Lounge: Monday–Sunday and public holiday 8.00 am–9.30 pm; "
        "U Garden staff: Monday–Friday 7.30 am–8.30 pm, Saturday 7.30 am–7.30 pm, Sunday and public holiday closed; "
        "U Garden student: Monday–Friday 7.30 am–8.30 pm, Saturday 7.30 am–7.30 pm, Sunday 9.00 am–6.00 pm, public holiday closed; "
        "VA Kiosk: Monday–Friday 7.00 am–9.00 pm, Saturday, Sunday and public holiday 9.00 am–8.00 pm; "
        "V Cafe: Monday–Saturday 8.00 am–8.00 pm, Sunday and public holiday closed; "
        "VA Staff Canteen: Monday–Friday 7.30 am–8.30 pm, Saturday 7.30 am–8.30 pm, Sunday and public holiday closed; "
        "VA Student Canteen: Monday–Friday 7.30 am–8.30 pm, Saturday 11.00 am–8.30 pm, Sunday and public holiday closed; "
        "W Kiosk: Monday–Friday 8.00 am–8.00 pm, Saturday 9.00 am–6.00 pm, Sunday and public holiday closed; "
        "X Cafe: Monday–Friday 8.00 am–9.00 pm, Saturday and Sunday 9.00 am–6.00 pm, public holiday closed; "
        "Z Café: Monday–Friday 10.30 am–8.30 pm, Saturday 10.30 am–6.30 pm, Sunday and public holiday closed; "
        "Z Canteen: Monday–Friday 7.30 am–8.30 pm, Saturday 7.30 am–7.30 pm, Sunday 9.00 am–6.00 pm, public holiday closed."
    ),
    "app3_H_001": (
        "PDF emergency contact table: 24-Hour Campus Emergency Hotline: 2766 7999; "
        "Campus Control Centre: 2766 7666; Health and Safety Office: 3400 8396; "
        "University Health Service: 2766 5433."
    ),
}


def annotate(chunks: list[dict]) -> list[dict]:
    """Attach annotations exactly once; reject incomplete or unexpected input."""
    found = set()
    result = []
    for chunk in chunks:
        chunk = dict(chunk)
        identifier = chunk["chunk_id"]
        if identifier in ANNOTATIONS:
            if identifier in found or " [Source-layout annotation:" in chunk["section"]:
                raise ValueError(f"duplicate or already annotated chunk: {identifier}")
            found.add(identifier)
            chunk["section"] += " [Source-layout annotation: " + ANNOTATIONS[identifier] + "]"
        result.append(chunk)
    if found != ANNOTATIONS.keys():
        raise ValueError(f"missing expected chunks: {sorted(ANNOTATIONS.keys() - found)}")
    return result
