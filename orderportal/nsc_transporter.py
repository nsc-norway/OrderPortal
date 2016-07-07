import itertools


class ValidationError(Exception):
    """Used internally for validation functions"""
    pass

def int_req(v):
    if isinstance(v, int) or str(v).isdigit():
        return int(v)
    else:
        raise ValidationError("Enter a number")

def int_opt(v):
    return "" if v == "" else int_opt(v)

def str_req(v):
    if v is None or v == "": raise ValidationError("Enter a value")
    return str(v)

str_opt = str

def float_req(v):
    try:
        return float(str(v).replace(",","."))
    except ValueError:
        raise ValidationError("Enter a decimal number")

def float_opt(v):
    return "" if v == "" else float_req(v)

class Field(object):
    def __init__(self, id, label, validator, width):
        self.id = id
        self.label = label
        self.validator = validator
        self.width = width

# First arg:  Internal label
# Second arg: Header in spreadsheet / CSV / table
SAMPLE_FIELDS = [
#        Field("sample_number",       "Number",           int_req,       4),
        Field("plate",               "Plate",            str_opt,       4),
        Field("sample_name",         "Sample name",      str_req,       10),
        Field("conc",                "Conc.",            float_req,     4),
        Field("a_260_280",           "A260/280",         float_opt,     4),
        Field("a_260_230",           "A260/230",         float_opt,     4),
        Field("volume",              "Volume provided",  float_opt,     4),
        Field("total_dna_rna",       "Total DNA / RNA",  float_opt,     4),
        Field("index_name",          "Index name",       str_opt,       8),
        Field("index_seq",           "Index Seq",        str_opt,       15),
        Field("primers",             "Primers, Linkers or RE sites present?", str_opt, 10),
        Field("num_reads",           "Approx no. Reads, Gb or lanes requested", str_opt,       8)
        ]

MAX_SAMPLES = 4 # TODO 16000

class ImportException(Exception):
    pass


def import_excel_file(wb):
    """Simple importer which reads the sample table Excel file and
    produces a list of dicts, one for each sample (identical to the
    format stored in the DB and exported to the LIMS, etc.)

    Only minimal validation is done. On error, an ImportException
    is raised, with a message indicating the cause.
    """
    try:
        ws = wb.worksheets[0]
    except IndexError:
        raise ImportException("No worksheets found in the file")

    col_of = {}

    for i in range(20):
        val = ws.cell(row=1, column=i).value
        if val:
            for field in SAMPLE_FIELDS:
                if str(val).lower().startswith(field.label.lower()):
                    col_of[field.id] = i

    samples = []
    for i in range(3, MAX_SAMPLES):
        name = ws.cell(row=i, column=col_of['sample_name'])
        if name:
            sample = {}
            for field in SAMPLE_FIELDS:
                sample[key] = ws.cell(row=i, column=col_of[field.id]).value
        else:
            break

    if ws.cell(row=i+1, column=1).value:
        raise ImportException("We only support importing {0} samples. Please "+
                "contact NSC staff if you would like to submit more samples, "+
                "and the webmaster may be able to increase this limit "+
                "(MAX_SAMPLES).".format(MAX_SAMPLES))

    return samples

def check_csv_header(self):



def import_csv(wb):
    """CSV"""
    return ffff

def import_file(file_data):
    is_csv = check_csv_header(file_data)

    try:
        wb = load_workbook(fh)
    except Exception as e:
        raise ImportException("Failed to import the Excel file. (Error: " + str(e) + ")")



class Cell(object):
    def __init__(self, field, valid, value, message):
        self.field = field
        self.valid = valid
        self.value = value
        self.message = message


def validate_table(samples_raw):
    """Main sample table validation.

    Takes a preliminary grid, from either file import or direct user import.
    Input format: list of dict objects, each dict object representing one
    sample, containing the sample field names as keys, and values as values.

    Returns:
        (validation_table, sample_list)

    validation_table: A list containing feedback to the user. Contains a
    list of lists of Cell objects. The first dimension is the row, nested
    dimension is the column.

    sample_list: list similar to samples_raw, but only contains valid data
    (input cells which fail validation are not included). All data in
    sample_list have the specified data types.
    """

    validation_table = []
    sample_list = []
    for sample_raw in samples_raw:
        sample = {}
        row = []
        for field in SAMPLE_FIELDS:
            value = sample_raw.get(field.id, '')
            try:
                value = field.validator(value)
                if value is not None:
                    sample[field.id] = value
                row.append(Cell(field, True, str(value), None))
            except ValidationError, e:
                row.append(Cell(field, False, str(value), str(e)))
        sample_list.append(sample)
        validation_table.append(row)

    return (validation_table, sample_list)
