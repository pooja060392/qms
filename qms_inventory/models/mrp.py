from odoo import api, fields, models, registry, _


class MrpProduction(models.Model):
    _inherit = 'mrp.production'


    def _count_final_transfers(self):
        for res in self:
            # number = self.env['stock.picking'].search([
            #     ('production_id', '=', res.id)
            # ])
            # count = 0
            # for length in number:
            #     count += 1
            # res.finished_transfer_count = count

            # NEHA: Update Count of Finished Transfers
            # number = self.env['stock.picking'].search([
            #     '|', ('production_id', '=', res.id), ('sale_id', '=', res.sale_id.id)
            # ])
            # count = 0
            # for length in number:
            #     count += 1
            number = self.env['stock.picking'].search([('origin', '=', res.name),
                                                       ('location_id', '=',res.location_dest_id.id)])
            res.finished_transfer_count = len(number)

    internal_transfer_mo = fields.Many2one(
        'stock.picking',
        string='Internal Transfer to Process',
        copy=False,
        index=True
    )
    internal_transfer_finished = fields.One2many(
        'stock.picking', 'production_id',
        string='Internal Transfer for Finalization',
        copy=False,
        index=True
    )
    finished_transfer_count = fields.Integer(compute='_count_final_transfers', string='Finished Transfer Count')
