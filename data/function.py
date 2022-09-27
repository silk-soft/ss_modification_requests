from odoo.http import request


def do_update(query, val, key):
    request.env.cr.execute(query, (val, key))


def insert_data(self, check_in, check_out, employee_id):
    attendance_val = {
        'check_in': check_in,
        'check_out': check_out,
        'employee_id': employee_id
    }
    self.env['hr.attendance'].sudo().create(attendance_val)
