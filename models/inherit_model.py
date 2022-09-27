# -*- coding: utf-8 -*-
from odoo import models, _
from odoo.tools import format_date


class InheritHrAttendance(models.Model):
    _inherit = "hr.attendance"

    def name_get(self):
        result = []
        for attendance in self:
            result.append((attendance.id, _("%(empl_name)s in %(check_in)s") % {
                'empl_name': attendance.employee_id.name,
                'check_in': format_date(self.env, attendance.check_in.date()),
            }))
        return result
