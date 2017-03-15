"OrderPortal: Table processors."

from __future__ import print_function, absolute_import

import collections
import logging
import re

from .baseprocessor import BaseProcessor


class NscSampleTableCheck(BaseProcessor):
    "The value must be a list of lists."

    def run(self, value, **kwargs):
        """Copy of the basic table checker, with additional 
        validation.
        
        Check first the entire value using 'check_table'.
        Then check each row using the member function 'check_row'.
        These functions must raise ValueError if anything is wrong.
        When more than 4 different errors have been detected,
        no further tests are made."""
        errors = set()
        try:
            self.check_table(value)
        except ValueError, msg:
            errors.add(str(msg))
        for i, row in enumerate(value):
            try:
                self.check_row(row)
            except ValueError, msg:
                errors.add("row %i: %s" % (i+1, msg))
            if len(errors) >= 4:
                break
        if errors:
            raise ValueError('; '.join(errors))

    def check_table(self, table):
        if not isinstance(table, collections.Sequence):
            raise ValueError('value is not a table (list of lists)')

    def check_row(self, row):
        if not isinstance(row, collections.Sequence):
            raise ValueError('row in value is not a list')
        if len(row) < 3:
            raise ValueError('not enough data in row')
        position = row[1]
        if not re.match(r"[A-H]([1-9]|1[0-2])$", position):
            raise ValueError('positiion must be in the format A1, A2, ... B1, B2,...')

