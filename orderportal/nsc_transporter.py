import itertools

def any_val(v):
    return v

def int_req(v):
    return i

def str_req(v):
    return ""

def float_req(v):
    return 0.0

def float_opt(v):
    return 0.0

def str_opt(v):
    return 0.0




# First element: Internal label
# Second element: Header in Excel sheet
SAMPLE_FIELDS = [
        ("sample_number",       "Number",           int_req),
        ("plate",               "Plate",            any_val),
        ("sample_name",         "Sample name",      str_req),
        ("conc",                "Conc.",            float_req),
        ("a_260_280",           "A260/280",         float_opt),
        ("a_260_230",           "A260/230",         float_opt),
        ("volume",              "Volume provided",  float_opt),
        ("total_dna_rna",       "Total DNA / RNA",  float_opt),
        ("index_name",          "Index name",       str_opt),
        ("index_seq",           "Index Seq",        str_opt),
        ("primers",             "Primers, Linkers or RE", str_opt),
        ("num_reads",            "Approx no. Reads", str_opt)
        ]


class ImportException(Exception):
    pass


def import_file(fh):
    """Simple importer which reads the sample table Excel file and
    produces a list of dicts, one for each sample (identical to the
    format stored in the DB and exported to the LIMS, etc.)

    Only minimal validation is done. On error, an ImportException
    is raised, with a message indicating the cause.
    """
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
            for key, label, _ in SAMPLE_FIELDS:
                if str(val).lower().startswith(label.lower()):
                    col_of[key] = i

    MAX_SAMP = 16000
    samples = []
    for i in range(3, MAX_SAMP):
        name = ws.cell(row=i, column=col_of['sample_name'])
        if name:
            sample = {}
            for key, _, _ in SAMPLE_FIELDS:
                sample[key] = ws.cell(row=i, column=col_of[key]).value
        else:
            break

    if ws.cell(row=i+1, column=1).value:
        raise ImportException("We only support importing {0} samples. Please "+
                "contact NSC staff if you would like to submit more samples, "+
                "and the webmaster "+
                "may be able to increase this limit (MAX_SAMP).".format(MAX_SAMP))

    return samples


def validate_table(samples_raw):
    """Main sample table validation.

    Return value:
        (validation, table)

    validation: A list of tuples, one for each sample:
        validation = [
            ({'sample_name': ..., ...}, error_level, 'Validation message')
        ]
    The first element contains the


    """

    notes = []
    samples = []
    for sample_raw in samples_raw:
        note = {}
        sample = {}
        for key,_,fn in SAMPLE_FIELDS:
            try:
                sample[k] = fn(sample_raw[key])
            except ValidationError, e:
                note[k] = (sample_raw[k], e)
