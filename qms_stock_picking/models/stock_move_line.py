from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
from odoo.tools.float_utils import float_round, float_compare, float_is_zero
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from dateutil import relativedelta


class Stock(models.Model):
    _inherit = 'stock.move'

    lot_id = fields.Many2one('stock.production.lot',string='Lot')
    related_code = fields.Selection([('incoming', 'Vendors'), ('outgoing', 'Customers'),
                                     ('internal', 'Internal'), ('mrp_operation', 'Manufacturing Operation')],
                                    related="picking_id.related_code",string='Type of Operation', store=True)
    qc_transfer = fields.Boolean(
        'Is QC Transfer', default=False, readonly = False,
        copy=False, index=True, compute='_compute_qc_transfer',
        store=True
    )

    @api.depends('location_id')
    def _compute_qc_transfer(self):
        for rec in self:
            if rec.location_id.quality_location is True:
                rec.qc_transfer = True

    @api.constrains('quantity_done')
    def check_done_qty(self):
        if self.quantity_done > self.product_uom_qty:
            raise ValueError('Please check, Done quantity is more than plan quantity!!!')


    @api.model
    def create(self, vals):
        if 'origin' in vals and vals['origin']:
            sale = self.env['sale.order'].search([('name','=', vals['origin'])],limit=1)
            warehouse_id = self.env['stock.warehouse'].search([('company_id', '=', vals.get('company_id'))], limit=1)
            type_id = warehouse_id.sample_picking_type
            if sale:
                # if sale.sale_type == 'sale':
                #     vals['location_id'] = warehouse_id.out_type_id.default_location_src_id.id
                if sale.sale_type == 'sample_gift':
                    if 'origin_returned_move_id' in vals and vals['origin_returned_move_id']:
                        vals['location_dest_id'] = type_id.default_location_src_id.id
                    else:
                        vals['picking_type_id'] = type_id.id
                        vals['location_id'] = type_id.default_location_src_id.id
        res = super(Stock, self).create(vals)
        return res

    def _push_apply(self):
        for move in self:
            # if the move is already chained, there is no need to check push rules
            if move.move_dest_ids:
                continue
            # if the move is a returned move, we don't want to check push rules, as returning a returned move is the only decent way
            # to receive goods without triggering the push rules again (which would duplicate chained operations)
            # priority goes to the route defined on the product and product category
            domain = [('location_src_id', '=', move.location_dest_id.id), ('action', 'in', ('push', 'pull_push'))]
            # first priority goes to the preferred routes defined on the move itself (e.g. coming from a SO line)
            warehouse_id = move.warehouse_id or move.picking_id.picking_type_id.warehouse_id

            # head_ofice_picking = self.env['stock.picking.type'].search([('name', '=', 'H.O Internal Transfer')],
            #                                                            limit=1)
            # internal_transfer_pick = self.env['stock.picking.type'].search([('name', '=', 'Internal Transfers')],
            #                                                                limit=1)
            if move.location_dest_id.company_id == self.env.company:
                rules = self.env['procurement.group']._search_rule(move.route_ids, move.product_id, warehouse_id, domain)
            else:
                rules = self.sudo().env['procurement.group']._search_rule(move.route_ids, move.product_id, warehouse_id, domain)
            # Make sure it is not returning the return
            if rules and (not move.origin_returned_move_id or move.origin_returned_move_id.location_dest_id.id != rules.location_id.id):
                rules._run_push(move)

    # Update Action: To update contect only
    def action_show_details(self):
        """ Returns an action that will open a form view (in a popup) allowing to work on all the
        move lines of a particular move. This form view is used when "show operations" is not
        checked on the picking type.
        """
        self.ensure_one()

        # If "show suggestions" is not checked on the picking type, we have to filter out the
        # reserved move lines. We do this by displaying `move_line_nosuggest_ids`. We use
        # different views to display one field or another so that the webclient doesn't have to
        # fetch both.
        if self.picking_id.picking_type_id.show_reserved:
            view = self.env.ref('stock.view_stock_move_operations')
        else:
            view = self.env.ref('stock.view_stock_move_nosuggest_operations')
        print('self.qc_transfer', self.qc_transfer)
        print('self.qc_transfer', self.location_id.name)
        print('self.qc_transfer', self.location_dest_id.name)

        is_shw_det = False
        if self.location_dest_id.quality_location and self.location_id.usage=='supplier':
            is_shw_det = False
        else:
            is_shw_det = True
        return {
            'name': _('Detailed Operations'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.move',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': self.id,
            'context': dict(
                self.env.context,
                show_lots_m2o=self.has_tracking != 'none' and (self.picking_type_id.use_existing_lots or self.state == 'done' or self.origin_returned_move_id.id),  # able to create lots, whatever the value of ` use_create_lots`.
                show_lots_text=self.has_tracking != 'none' and self.picking_type_id.use_create_lots and not self.picking_type_id.use_existing_lots and self.state != 'done' and not self.origin_returned_move_id.id,
                show_source_location=self.location_id.child_ids,
                show_destination_location=self.location_dest_id.child_ids,
                show_qc_transfer = is_shw_det,
                show_package=not self.location_id.usage == 'supplier',
                show_reserved_quantity=self.state != 'done'
            ),
        }


class StockMoveline(models.Model):
    _inherit = 'stock.move.line'

    remove_date = fields.Date('Expiry Date', readonly=False)
    manufacture_date = fields.Date('Manufacture Date')
    import_date = fields.Datetime('Import Date')
    mrp = fields.Float('MRP')
    open_check = fields.Boolean()
    related_code = fields.Selection([('incoming', 'Vendors'), ('outgoing', 'Customers'), ('internal', 'Internal')],
                                    'Type of Operation', related="picking_id.related_code", store=True)
    qc_transfer = fields.Boolean(
        'Is QC Transfer', default=False, readonly=False,
        copy=False, index=True, compute='_compute_qc_transfer',
        store=True
    )

    @api.depends('location_id')
    def _compute_qc_transfer(self):
        for rec in self:
            if rec.location_id.quality_location is True:
                rec.qc_transfer = True

    @api.constrains('qty_done')
    def check_done_qty(self):
        if self.picking_id.picking_type_id.code == 'outgoing':
            if self.lot_id:
                if self.qty_done > self.product_uom_qty:
                    raise ValueError('Please check, Done quantity is more than quantity in lot')
        if self.qty_done > self.move_id.product_uom_qty or self.move_id.quantity_done > self.move_id.product_uom_qty:
            raise ValueError('Please check, Done quantity is more than initial demand')
        # NEHA for checking: quality received qty checked at time of receiving in STOCK
        po_id = self.env['purchase.order'].search([('name', '=', self.picking_id.origin)])
        if po_id:
            product_filter = po_id.order_line.filtered(lambda l: l.product_id.id == self.product_id.id)
            if product_filter:
                # \NEHA: Add quality location check
                if product_filter.qty_received < self.qty_done and not self.location_dest_id.quality_location:
                    raise UserError('You cannot received Qty, which is not Quality Checked! \n Checked Qty is : %s' % (
                        product_filter.qty_received))

    @api.onchange('lot_id')
    def onchange_lot(self):
        lot_lst = []
        lot_name_lst = []
        for rec in self:
            if rec.lot_id:
                if rec.picking_id.return_picking_id:
                    for mv in rec.picking_id.return_picking_id.move_lines:
                        for ml in mv.move_line_ids:
                            lot_name_lst.append(ml.lot_id.name)
                            lot_lst.append(ml.lot_id.id)
                    if rec.lot_id.id not in lot_lst:
                        raise UserError(_('Please select given lot!! %s')%lot_name_lst)
                rec.manufacture_date = rec.lot_id.manufacture_date
                rec.remove_date = rec.lot_id.removal_date
                rec.import_date = rec.lot_id.import_date
                rec.mrp = rec.lot_id.mrp

    # def _action_done(self):
    #     """ This method is called during a move's `action_done`. It'll actually move a quant from
    #     the source location to the destination location, and unreserve if needed in the source
    #     location.
    #
    #     This method is intended to be called on all the move lines of a move. This method is not
    #     intended to be called when editing a `done` move (that's what the override of `write` here
    #     is done.
    #     """
    #
    #     # First, we loop over all the move lines to do a preliminary check: `qty_done` should not
    #     # be negative and, according to the presence of a picking type or a linked inventory
    #     # adjustment, enforce some rules on the `lot_id` field. If `qty_done` is null, we unlink
    #     # the line. It is mandatory in order to free the reservation and correctly apply
    #     # `action_done` on the next move lines.
    #     ml_to_delete = self.env['stock.move.line']
    #     for ml in self:
    #         qty_done_float_compared = float_compare(ml.qty_done, 0, precision_rounding=ml.product_uom_id.rounding)
    #         if qty_done_float_compared > 0:
    #             if ml.product_id.tracking != 'none':
    #                 picking_type_id = ml.move_id.picking_type_id
    #                 if picking_type_id:
    #                     if picking_type_id.use_create_lots:
    #                         # If a picking type is linked, we may have to create a production lot on
    #                         # the fly before assigning it to the move line if the user checked both
    #                         # `use_create_lots` and `use_existing_lots`.
    #                         if ml.lot_name and not ml.lot_id:
    #                             lot = self.env['stock.production.lot'].create(
    #                                 {'name': ml.lot_name, 'product_id': ml.product_id.id,
    #                                  'removal_date': ml.remove_date,
    #                                  'manufacture_date': ml.manufacture_date,
    #                                  # 'life_date': ml.remove_date,
    #                                  'import_date': ml.import_date,
    #                                  'mrp': ml.mrp,
    #                                  }
    #                             )
    #                             ml.write({'lot_id': lot.id})
    #                     elif not picking_type_id.use_create_lots and not picking_type_id.use_existing_lots:
    #                         # If the user disabled both `use_create_lots` and `use_existing_lots`
    #                         # checkboxes on the picking type, he's allowed to enter tracked
    #                         # products without a `lot_id`.
    #                         continue
    #                 elif ml.move_id.inventory_id:
    #                     # If an inventory adjustment is linked, the user is allowed to enter
    #                     # tracked products without a `lot_id`.
    #                     continue
    #
    #                 # if not ml.lot_id:
    #                 #     raise UserError(_('You need to supply a lot/serial number for %s.') % ml.product_id.name)
    #         elif qty_done_float_compared < 0:
    #             raise UserError(_('No negative quantities allowed'))
    #         else:
    #             ml_to_delete |= ml
    #     ml_to_delete.unlink()
    #
    #     # Now, we can actually move the quant.
    #     for ml in self - ml_to_delete:
    #         if ml.product_id.type == 'product':
    #             Quant = self.env['stock.quant']
    #             rounding = ml.product_uom_id.rounding
    #
    #             # if this move line is force assigned, unreserve elsewhere if needed
    #             if not ml.location_id.should_bypass_reservation() and float_compare(ml.qty_done, ml.product_qty, precision_rounding=rounding) > 0:
    #                 extra_qty = ml.qty_done - ml.product_qty
    #                 ml._free_reservation(ml.product_id, ml.location_id, extra_qty, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id)
    #             # unreserve what's been reserved
    #             if not ml.location_id.should_bypass_reservation() and ml.product_id.type == 'product' and ml.product_qty:
    #                 try:
    #                     Quant._update_reserved_quantity(ml.product_id, ml.location_id, -ml.product_qty, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id, strict=True)
    #                 except UserError:
    #                     Quant._update_reserved_quantity(ml.product_id, ml.location_id, -ml.product_qty, lot_id=False, package_id=ml.package_id, owner_id=ml.owner_id, strict=True)
    #
    #             # move what's been actually done
    #             quantity = ml.product_uom_id._compute_quantity(ml.qty_done, ml.move_id.product_id.uom_id, rounding_method='HALF-UP')
    #             available_qty, in_date = Quant._update_available_quantity(ml.product_id, ml.location_id, -quantity, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id)
    #             if available_qty < 0 and ml.lot_id:
    #                 # see if we can compensate the negative quants with some untracked quants
    #                 untracked_qty = Quant._get_available_quantity(ml.product_id, ml.location_id, lot_id=False, package_id=ml.package_id, owner_id=ml.owner_id, strict=True)
    #                 if untracked_qty:
    #                     taken_from_untracked_qty = min(untracked_qty, abs(quantity))
    #                     Quant._update_available_quantity(ml.product_id, ml.location_id, -taken_from_untracked_qty, lot_id=False, package_id=ml.package_id, owner_id=ml.owner_id)
    #                     Quant._update_available_quantity(ml.product_id, ml.location_id, taken_from_untracked_qty, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id)
    #             Quant._update_available_quantity(ml.product_id, ml.location_dest_id, quantity, lot_id=ml.lot_id, package_id=ml.result_package_id, owner_id=ml.owner_id, in_date=in_date)
    #     # Reset the reserved quantity as we just moved it to the destination location.
    #     (self - ml_to_delete).with_context(bypass_reservation_update=True).write({'product_uom_qty': 0.00})
