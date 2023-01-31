# -*- coding: utf-8 -*-
import json

from odoo import models, fields, api
from odoo.addons.ss_modification_requests.data.query import QueryList
from odoo.addons.ss_modification_requests.data.function import *
from odoo.exceptions import ValidationError
import dateutil.parser as dparser
from odoo.addons.hr_attendance.models import hr_attendance


class ModificationRequest (models.Model):
    _name = "modification.request"
    _inherit = "mail.thread"
    _description = "Modification Requests"

    def _default_record_owner(self):
        if not self.record_owner:
            return self.env.user.employee_id

    def _default_created_user(self):
        return self.env.user

    def _default_hr_responsible(self):
        if not self.hr_responsible:
            return self.env['res.users'].search([('id', '=', 2)])

    name = fields.Char(string='Name', required=True, tracking=True, readonly=True)
    model = fields.Selection([('hr.attendance', 'Attendance')], default='hr.attendance', required=True, tracking=True
                             , states={'draft': [('readonly', False)]}, readonly=True)
    action_type = fields.Selection([('edit', 'Edit'), ('create', 'Create')], default='edit', required=True
                                   , tracking=True, states={'draft': [('readonly', False)]}, readonly=True)
    attendance_records = fields.Many2one('hr.attendance', tracking=True, readonly=True
                                         , states={'draft': [('readonly', False)]})
    fields_attendance = fields.Selection([
        ('check_in', 'Check In'),
        ('check_out', 'Check Out'),
        ], 'Field Name', default='check_in', tracking=True, states={'draft': [('readonly', False)]}, readonly=True)
    old_value = fields.Datetime(string='Old Value', readonly=True, store=True)
    new_value = fields.Datetime(string='New Value', tracking=True, readonly=True
                                , states={'draft': [('readonly', False)]})
    check_in = fields.Datetime(string='Check In', store=True, readonly=True, states={'draft': [('readonly', False)]})
    check_out = fields.Datetime(string='Check Out', store=True, readonly=True, states={'draft': [('readonly', False)]})
    state = fields.Selection([('cancel', 'Rejected'), ('draft', 'Draft'), ('verify', 'Pending'),
                              ('approve', 'Approved'), ], string='Status'
                             , index=True, readonly=True, copy=False, default='draft',
                             help="""* When the request is created the status is \'Draft\'
                            \n* If the request is under verification, the status is \'Waiting\'.
                            \n* If the request is approved then status is set to \'Approved\'.
                            \n* When the admin cancel request the status is \'Rejected\'.""", tracking=True)
    record_owner = fields.Many2one('hr.employee', compute='_compute_record_owner', string='Record Owner'
                                   , help="The user who made the request", readonly=True
                                   , copy=False, default=_default_record_owner, store=True)
    hr_responsible = fields.Many2one('res.users', compute='_compute_hr_responsible', string='Responsible'
                                     , help="The user who made the request", readonly=True
                                     , copy=False, default=_default_hr_responsible, store=True)
    created_user = fields.Many2one('res.users', string='Presenter', compute='_compute_created_user'
                                   , help="The user who made the request", readonly=True
                                   , copy=False, store=True, default=_default_created_user)
    created_employee = fields.Many2one('hr.employee', compute='_compute_record_owner', string='Employee'
                                       , help="The user who made the request", readonly=True
                                       , copy=False, default=_default_record_owner, store=True)
    comment = fields.Text(String='Comment', help='Write down reasons if there\'s any', tracking=True, readonly=True
                          , states={'draft': [('readonly', False)]})
    date = fields.Date(String='Request Date', readonly=True)
    active = fields.Boolean(String="Active", default=True)

    @api.onchange('attendance_records', 'fields_attendance', 'new_value')
    def getting_old_value(self):
        if not self.attendance_records or not self.fields_attendance or not self.model:
            return
        self.old_value = getattr(self.attendance_records, self.fields_attendance)
        self.name = self.attendance_records.employee_id.name + ' - ' + str(getattr(self.attendance_records
                                                                           , self.fields_attendance).date())
        self.date = getattr(self.attendance_records, self.fields_attendance).date()

    def compute_date(self, space):
        for rec in self:
            local_name = rec.name[space:]
            rec.date = dparser.parse(local_name, fuzzy=True)

    def _compute_created_user(self):
        for rec in self:
            if not rec.created_user:
                rec.created_user = rec.create_uid

    @api.onchange('attendance_records', 'check_in', 'check_out')
    def _compute_record_owner(self):
        for rec in self:
            if rec.action_type == "edit":
                rec.record_owner = rec.attendance_records.employee_id
            elif rec.action_type == "create":
                rec.record_owner = rec.env.user.employee_id

    @api.onchange('attendance_records', 'check_in', 'check_out')
    def _compute_hr_responsible(self):
        for rec in self:
            rec._compute_record_owner()
            rec.hr_responsible = rec.record_owner.leave_manager_id

    @api.onchange('check_in')
    def set_name_create(self):
        if not self.created_employee or not self.check_in:
            return
        self.name = self.created_employee.name + ' - ' + str(self.check_in.date())
        self.date = self.check_in.date()

    def action_submit_request(self):
        if self.action_type == "edit":
            if self.new_value and self.fields_attendance and self.attendance_records:
                if self.fields_attendance == "check_in":
                    if self.new_value > self.attendance_records.check_out:
                        raise ValidationError('Check in field can\'t be in a date after check out.')
                if self.fields_attendance == "check_out":
                    if self.new_value < self.attendance_records.check_in:
                        raise ValidationError('Check out field can\'t be in a date before check in.')
            self.date = self.new_value.date()
        elif self.action_type == "create":
            if self.check_in and self.check_out:
                if self.check_in > self.check_out:
                    raise ValidationError('Check in field can\'t be in a date after check out.')
            self.date = self.check_in.date()
        self.write({'state': 'verify'})
        if self.hr_responsible.partner_id:
            followers = [self.hr_responsible.partner_id.id]
            self.message_subscribe(followers, None)
            self.message_post(subject=self.action_type.capitalize()+" Request"
                              , body="Hello "+self.hr_responsible.name+" please accept my request."
                              , partner_ids=followers)

    def action_payslip_draft(self):
        return self.write({'state': 'draft'})

    def action_approve(self):
        if self.action_type == "edit":
            if not self.new_value or not self.attendance_records or not self.fields_attendance:
                raise ValidationError('Make sure all required fields are filled.')
            query = QueryList()
            if self.fields_attendance == "check_in":
                do_update(query.update_attendance_check_in, self.new_value, self.attendance_records.id)
            if self.fields_attendance == "check_out":
                do_update(query.update_attendance_check_out, self.new_value, self.attendance_records.id)
            hr_attendance.HrAttendance._compute_worked_hours(self.attendance_records)
            self.name = self.sudo().attendance_records.employee_id.name + ' - ' + str(self.new_value.date())
        if self.action_type == "create":
            if not self.check_in or not self.check_out or not self.created_employee:
                raise ValidationError('Make sure all required fields are filled.')
            insert_data(self, self.check_in, self.check_out, self.created_employee.id)
        return self.write({'state': 'approve'})

    def action_refuse(self):
        return self.write({'state': 'cancel'})
