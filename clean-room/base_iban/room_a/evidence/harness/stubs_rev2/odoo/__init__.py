# Minimal fake 'odoo' package (rev 2): enough to load BOTH the base
# res_bank.py and base_iban's res_partner_bank.py unmodified.
# The parent of the base model is a plain recorder: create/write return the
# vals they receive. No ORM, no compute, no DB.
from . import api, fields, models, exceptions, tools  # noqa
