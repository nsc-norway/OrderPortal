import itertools

# First element: Internal label
# Second element: Header in Excel sheet
SAMPLE_FIELDS = [
        ("sample_number",       "Number"),
        ("plate",               "Plate"),
        ("sample_name",         "Sample name"),
        ("conc",                "Conc."),
        ("a_260_280",           "A260/280"),
        ("a_260_230",           "A260/230"),
        ("volume",              "Volume provided"),
        ("total_dna_rna",       "Total DNA / RNA"),
        ("index_name",          "Index name"),
        ("index_seq",           "Index Seq"),
        ("primers",             "Primers, Linkers or RE"),
        ("num_reads",            "Approx no. Reads")
        ]


class ImportException(Exception):
    pass


def import_file(fh):
    try:
        wb = load_workbook(fh)
    except Exception as e:
        raise ImportException("Failed to import the Excel file. Please use a " +
        "file in Microsoft Excel format (xlsx). (Error: " + str() + ")")

    try:
        ws = wb.worksheets[0]
    except IndexError:
        raise ImportException("No worksheets found in the file")

    col_of = {}

    for i in range(20):
        val = ws.cell(row=1, column=i).value
        if val:
            for key, label in SAMPLE_FIELDS:
                if str(val).lower().startswith(label.lower()):
                    col_of[key] = i

    MAX_SAMP = 16000
    for i in range(MAX_SAMP):
        pass

    if ws.cell(row=i+1, column=1).value:
        raise ImportException("We only support importing {0} samples. Please "+
                "contact NSC staff if you would like to submit more samples, "+
                "and the webmaster "+
                "may be able to increase this limit (MAX_SAMP).".format(MAX_SAMP))
    
