from odoo import api, fields, models, _
from odoo.exceptions import UserError,ValidationError


class QuantityWiz(models.TransientModel):
    _name = "location.quantity.wiz"

    location_quantity = fields.Text(string=" ", required=False, readonly=True)

    @api.model
    def default_get(self, fields):
        res = super(QuantityWiz, self).default_get(fields)
        context = self._context
        product_line_ = context.get('active_id')
        product_template_obj = self.env['product.template']
        stock_lot_obj = self.env['stock.production.lot']
        stock_location_obj = self.env['stock.location']
        product_ref = product_template_obj.search([('id', '=', product_line_)])
        qty_update = ''
        for line in product_ref:
            self._cr.execute("""select sq.location_id, sum(sq.quantity) from stock_quant sq
                        join stock_location sl on sl.id = sq.location_id
                        join product_product pp on pp.id = sq.product_id
                        where sl.usage = 'internal' and pp.product_tmpl_id = %s group by sq.location_id""" % line.id)
            location_ = self._cr.fetchall()
            for data in location_:
                location_id_ = stock_location_obj.search([['id', '=', data[0]]])
                self._cr.execute("""select sq.lot_id, sum(sq.quantity), spl.removal_date, spl.mrp from stock_quant sq
                                         join stock_location sl on sl.id = sq.location_id
                                         join stock_production_lot spl on spl.id = sq.lot_id
                                         join product_product pp on pp.id = sq.product_id
                                         where sl.usage = 'internal'
                                         and pp.product_tmpl_id = %s
                                         and sq.location_id = %s
                                         group by sq.lot_id, spl.removal_date, spl.mrp
                                         order by spl.removal_date""" % (line.id, location_id_.id))
                lot_ = self._cr.fetchall()
                list_ = []
                for rec in lot_:
                    lot_id_ = stock_lot_obj.search([['id', '=', rec[0]]])
                    if lot_id_.removal_date:
                        list_.append(' '*5 + str(lot_id_.name) + ' (' + 'Qty: ' + str(rec[1]) + ',   ' + 'Lot Expiry: ' +
                                     str(lot_id_.removal_date) + ',   ' + 'MRP: ' + str(lot_id_.mrp) + ')')
                    else:
                        list_.append(' '*5 + str(lot_id_.name) + ' (' + 'Qty: ' + str(rec[1]) + ',   ' + 'MRP: ' +
                                     str(lot_id_.mrp) + ')')
                l = '\n'.join(map(str, list_))
                if lot_:
                    qty_update += str(location_id_.name) + ': ' + str(data[1]) + '\n' + 'Lots:' + '\n' + l + '\n'*2
                else:
                    qty_update += str(location_id_.name) + ': ' + str(data[1]) + '\n' + l + '\n' * 2

            if not location_:
                raise ValidationError(_('Nothing to show!!'))
        res.update({'location_quantity': qty_update})
        return res
