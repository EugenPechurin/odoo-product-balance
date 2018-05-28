# -*- coding: utf-8 -*-

from odoo import models
from odoo import fields
from odoo import api
from odoo import tools


class ProductSaldoReportWizard(models.TransientModel):
    _name = 'product_balance.wizard'

    start_date = fields.Date('Start date')
    end_date = fields.Date('End date')
    product = fields.Many2one(
        'product.product',
        'Product',
    )
    location = fields.Many2one(
        'stock.location',
        'Stock location',
    )


class ProductBalanceReport(models.Model):
    _name = 'product_balance.report'
    _auto = False

    product_id = fields.Many2one(
        'product.product',
        'Product',
    )
    stock_move_id = fields.Many2one(
        'stock.move',
        'Stock move'
    )
    start_balance = fields.Integer('Start balance')
    end_balance = fields.Integer('End balance')
    picking = fields.Integer('Picking')
    internal_picking = fields.Integer('Internal picking')
    sale = fields.Integer('Sale')
    date = fields.Date('Date')
    stock_id = fields.Many2one(
        'stock.warehouse',
        'Warehouse',
    )
    count = fields.Integer('Count')

    @api.multi
    def do_print_picking(self):
        self.write({'printed': True})
        return self.env.ref('stock.action_report_picking').report_action(self)

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, 'product_balance_report')
        self._cr.execute("""CREATE or REPLACE VIEW product_balance_report AS (SELECT
            MIN(id) as id,
            product_id as product_id,
            date as date,
            sum(product_qty) AS quantity,
            sum(sum(product_qty)) OVER (PARTITION BY product_id ORDER BY date) AS cumulative_quantity
            FROM
            (SELECT
            MIN(id) as id,
            MAIN.product_id as product_id,
            SUB.date as date,
            CASE WHEN MAIN.date = SUB.date THEN sum(MAIN.product_qty) ELSE 0 END as product_qty
            FROM
            (SELECT
                MIN(sq.id) as id,
                sq.product_id,
                date_trunc('week', to_date(to_char(CURRENT_DATE, 'YYYY/MM/DD'), 'YYYY/MM/DD')) as date,
                SUM(sq.quantity) AS product_qty
                FROM
                stock_quant as sq
                LEFT JOIN
                product_product ON product_product.id = sq.product_id
                LEFT JOIN
                stock_location location_id ON sq.location_id = location_id.id
                WHERE
                location_id.usage = 'internal'
                GROUP BY date, sq.product_id
                UNION ALL
                SELECT
                MIN(-sm.id) as id,
                sm.product_id,
                CASE WHEN sm.date_expected > CURRENT_DATE
                THEN date_trunc('week', to_date(to_char(sm.date_expected, 'YYYY/MM/DD'), 'YYYY/MM/DD'))
                ELSE date_trunc('week', to_date(to_char(CURRENT_DATE, 'YYYY/MM/DD'), 'YYYY/MM/DD')) END
                AS date,
                SUM(sm.product_qty) AS product_qty
                FROM
                   stock_move as sm
                LEFT JOIN
                   product_product ON product_product.id = sm.product_id
                LEFT JOIN
                stock_location dest_location ON sm.location_dest_id = dest_location.id
                LEFT JOIN
                stock_location source_location ON sm.location_id = source_location.id
                WHERE
                sm.state IN ('confirmed','assigned','waiting') and
                source_location.usage != 'internal' and dest_location.usage = 'internal'
                GROUP BY sm.date_expected,sm.product_id
                UNION ALL
                SELECT
                    MIN(-sm.id) as id,
                    sm.product_id,
                    CASE WHEN sm.date_expected > CURRENT_DATE
                        THEN date_trunc('week', to_date(to_char(sm.date_expected, 'YYYY/MM/DD'), 'YYYY/MM/DD'))
                        ELSE date_trunc('week', to_date(to_char(CURRENT_DATE, 'YYYY/MM/DD'), 'YYYY/MM/DD')) END
                    AS date,
                    SUM(-(sm.product_qty)) AS product_qty
                FROM
                   stock_move as sm
                LEFT JOIN
                   product_product ON product_product.id = sm.product_id
                LEFT JOIN
                   stock_location source_location ON sm.location_id = source_location.id
                LEFT JOIN
                   stock_location dest_location ON sm.location_dest_id = dest_location.id
                WHERE
                    sm.state IN ('confirmed','assigned','waiting') and
                source_location.usage = 'internal' and dest_location.usage != 'internal'
                GROUP BY sm.date_expected,sm.product_id)
             as MAIN
         LEFT JOIN
         (SELECT DISTINCT date
          FROM
          (
                 SELECT date_trunc('week', CURRENT_DATE) AS DATE
                 UNION ALL
                 SELECT date_trunc('week', to_date(to_char(sm.date_expected, 'YYYY/MM/DD'), 'YYYY/MM/DD')) AS date
                 FROM stock_move sm
                 LEFT JOIN
                 stock_location source_location ON sm.location_id = source_location.id
                 LEFT JOIN
                 stock_location dest_location ON sm.location_dest_id = dest_location.id
                 WHERE
                 sm.state IN ('confirmed','assigned','waiting') and sm.date_expected > CURRENT_DATE and
                 ((dest_location.usage = 'internal' AND source_location.usage != 'internal')
                  or (source_location.usage = 'internal' AND dest_location.usage != 'internal'))) AS DATE_SEARCH)
                 SUB ON (SUB.date IS NOT NULL)
        GROUP BY MAIN.product_id,SUB.date, MAIN.date
        ) AS FINAL
        GROUP BY product_id,date)""")