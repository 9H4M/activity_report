# -*- coding: utf-8 -*-
from odoo import models, fields, tools


class ActivityReport(models.Model):
    _name = "activity.report"
    _description = "Activity Report (Planned + Done)"
    _auto = False
    _log_access = False  # This is a pure SQL report, no ORM writes

    id = fields.Integer("ID", readonly=True)
    user_id = fields.Many2one("res.users", string="User", readonly=True)
    res_model = fields.Char("Model", readonly=True)
    res_id = fields.Integer("Resource ID", readonly=True)
    activity_type_id = fields.Many2one(
        "mail.activity.type", string="Activity Type", readonly=True
    )
    summary = fields.Char("Summary", readonly=True)
    note = fields.Text("Note", readonly=True)
    date_deadline = fields.Date("Deadline", readonly=True)
    state = fields.Selection(
        [("planned", "Planned"), ("done", "Done")], string="State", readonly=True
    )
    done_date = fields.Datetime("Done Date", readonly=True)

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute(
            """
            CREATE OR REPLACE VIEW activity_report AS (
                -- 1) Planned activities (still open)
                SELECT
                    a.id AS id,
                    a.user_id AS user_id,
                    a.res_model AS res_model,
                    a.res_id AS res_id,
                    a.activity_type_id AS activity_type_id,
                    a.summary AS summary,
                    a.note AS note,
                    a.date_deadline AS date_deadline,
                    'planned'::text AS state,
                    NULL::timestamp WITHOUT TIME ZONE AS done_date
                FROM mail_activity a
                WHERE a.id IS NOT NULL  -- ✅ safe for Odoo 12 (no active field)

                UNION ALL

                -- 2) Done activities from mail_message (activity completions)
                SELECT
                    (m.id + 100000000) AS id,
                    COALESCE(m.author_id, m.create_uid) AS user_id,
                    m.model AS res_model,
                    m.res_id AS res_id,
                    m.mail_activity_type_id AS activity_type_id,
                    COALESCE(m.subject, 'Activity completed') AS summary,
                    m.body AS note,
                    NULL::date AS date_deadline,
                    'done'::text AS state,
                    m.date AS done_date
                FROM mail_message m
                WHERE m.mail_activity_type_id IS NOT NULL
                  AND m.model IS NOT NULL
                  AND m.model != 'mail.activity'
            )
        """
        )

    def action_open_related_record(self):
        """
        Open the related record (res_model + res_id) in form view
        """
        self.ensure_one()

        if not self.res_model or not self.res_id:
            raise UserError("No related record found to open.")

        # Check if the model exists and the record exists
        if self.res_model not in self.env:
            raise UserError(f"Model '{self.res_model}' is not available in the system.")

        # Get the target record
        target_model = self.env[self.res_model]
        target_record = target_model.browse(self.res_id)

        if not target_record.exists():
            raise UserError("The related record no longer exists.")

        # Return the action to open the record
        return {
            "type": "ir.actions.act_window",
            "res_model": self.res_model,
            "res_id": self.res_id,
            "views": [(False, "form")],
            "view_mode": "form",
            "target": "current",
            "context": self.env.context,
        }
