from odoo import api, models


class CancelMoveWizard(models.TransientModel):
    _name = 'cancel.move.wizard'


    def cancel_move(self):
        move_obj = self.env['stock.move']
        context = self._context
        active_ids = context.get('active_ids')
        model = context.get('active_model')
        if model == 'stock.move':
            for move in move_obj.browse(active_ids):
                move.action_move_cancel()
        return True
