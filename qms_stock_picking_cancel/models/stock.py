
from odoo import api, models, _


class StockPicking(models.Model):
    _inherit = "stock.picking"


    def reset_to_draft(self):
        self.write({'state': 'draft'})
        self.mapped('move_lines').write({'state': 'draft'})


    def action_picking_cancel(self):
        self.mapped('move_lines').action_move_cancel()
        self.write({'is_locked': True})
        return True


class StockMove(models.Model):
    _inherit = "stock.move"

    def _do_unreserve(self):
        # if any(move.state in ('done', 'cancel') for move in self):
        #     raise UserError(_('Cannot unreserve a done move'))
        for move in self:
            move.move_line_ids.unlink()
            if move.procure_method == 'make_to_order' and not move.move_orig_ids:
                move.state = 'waiting'
            elif move.move_orig_ids and not all(orig.state in ('done', 'cancel') for orig in move.move_orig_ids):
                move.state = 'waiting'
            else:
                move.state = 'confirmed'
        return True

    def action_move_cancel(self):
        # if any(move.state == 'done' for move in self):
        #     raise UserError(_('You cannot cancel a stock move that has been set to \'Done\'.'))
        for move in self:
            for move_line in move.move_line_ids:
                # move_line.write({'state': 'draft'})
                move_line.write({'state': 'draft', 'qty_done': 0.0})
            if move.state == 'cancel':
                continue
            move._do_unreserve()
            siblings_states = (move.move_dest_ids.mapped('move_orig_ids') - move).mapped('state')
            # move.write({'state': 'cancel'})
            if move.propagate_cancel:
                # only cancel the next move if all my siblings are also cancelled
                if all(state == 'cancel' for state in siblings_states):
                    move.move_dest_ids._action_cancel()
            else:
                if all(state in ('done', 'cancel') for state in siblings_states):
                    move.move_dest_ids.write({'procure_method': 'make_to_stock'})
                    move.move_dest_ids.write({'move_orig_ids': [(3, move.id, 0)]})
        self.write({'state': 'cancel', 'move_orig_ids': [(5, 0, 0)]})
        return True
