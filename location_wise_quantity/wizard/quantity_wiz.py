from odoo import api, fields, models, _
from odoo.exceptions import UserError,ValidationError


class LocationQuantityWiz(models.Model):
    _name = "location.quantity.wizard"

    location_quantity = fields.Text(string=" ", required=False, readonly=True)
    sale_line_id = fields.Many2one('sale.order.line', string="Sale Order Line Reference")

    @api.model
    def default_get(self, fields):
        res = super(LocationQuantityWiz, self).default_get(fields)
        context = self._context
        sale_line_ = context.get('active_id')
        sale_line_obj = self.env['sale.order.line']
        stock_lot_obj = self.env['stock.production.lot']
        stock_location_obj = self.env['stock.location']
        sale_line_ref = sale_line_obj.search([('id', '=', sale_line_)])
        qty_update = ''
        for line in sale_line_ref:
            self._cr.execute("""select sq.location_id, sum(sq.quantity) from stock_quant sq
                        join stock_location sl on sl.id = sq.location_id
                        where sl.usage = 'internal' and sq.product_id = %s group by sq.location_id""" % line.product_id.id)
            location_ = self._cr.fetchall()
            for data in location_:
                location_id_ = stock_location_obj.search([['id', '=', data[0]]])
                self._cr.execute("""select sq.lot_id, sum(sq.quantity), spl.removal_date, spl.mrp from stock_quant sq
                                         join stock_location sl on sl.id = sq.location_id
                                         join stock_production_lot spl on spl.id = sq.lot_id
                                         where sl.usage = 'internal'
                                         and sq.product_id = %s
                                         and sq.location_id = %s
                                         and spl.active = True
                                         group by sq.lot_id, spl.removal_date, spl.mrp
                                         order by spl.removal_date""" % (line.product_id.id, location_id_.id))
                lot_ = self._cr.fetchall()
                list_ = []
                for rec in lot_:
                    lot_id_ = stock_lot_obj.search([['id', '=', rec[0]]])
                    if lot_id_.removal_date:
                        list_.append(' '*5 + str(lot_id_.name) + ': ' + str(rec[1]) + ' (' + 'Lot Expiry: ' +
                                     str(lot_id_.removal_date) + ', ' + 'MRP: ' + str(lot_id_.mrp) + ')')
                    else:
                        list_.append(' '*5 + str(lot_id_.name) + ': ' + str(rec[1]) + ' (' + 'MRP: ' +
                                     str(lot_id_.mrp) + ')')
                l = '\n'.join(map(str, list_))
                qty_update += str(location_id_.name) + ': ' + str(data[1]) + '\n' + l + '\n'*2

            if not location_:
                raise ValidationError(_('Nothing to show!!'))
        res.update({'location_quantity': qty_update})
        return res
