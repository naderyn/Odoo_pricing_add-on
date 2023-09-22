# Import necessary modules from Odoo
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

# Define a model for recording price change history
class pricehistory(models.Model):
    _name = 'product.price.change.log'
    _description = 'Product Price Change Log'
    order = "change_datetime desc"

    # Define fields for the price change log
    product_id = fields.Many2one(
        comodel_name='product.template',
        string='Product',
        required=True)

    category_id = fields.Many2one(
        related='product_id.categ_id',
        string='Product Category', store=True)

    old_price = fields.Float(
        string='Old Price')

    new_price = fields.Float(
        string='New Price')

    user_id = fields.Many2one(
        comodel_name='res.users',
        string='User',
        default=lambda self: self.env.user,
        readonly=True)

    change_datetime = fields.Datetime(
        string='Change Datetime',
        default=fields.Datetime.now,
        readonly=True)

    # Prevent deletion of price change logs
    def unlink(self):
        for rec in self:
            raise ValidationError(
                _("Can't delete History Log!")
            )
        return super(pricehistory, self).sudo().unlink()

# Define a model for product pricing
class ProductPricing(models.Model):
    _name = 'product.pricing'
    _description = 'New Pricing Report'

    # Define fields for product pricing
    default_code = fields.Char(
        related='product_id.default_code',
        string='Code',
        required=False)

    product_id = fields.Many2one(
        comodel_name='product.template',
        string='Product',
        required=True,
        readonly=False)

    product = fields.Char(
        related='product_id.name',
        string='Product Name',
        readonly=True)

    category_id = fields.Many2one(
        related='product_id.categ_id',
        string='Product Category', store=True)

    last_purchase_price = fields.Float(
        string='Last Purchase Price',
        compute='_compute_last_purchase_price')

    cost = fields.Float(
        related='product_id.standard_price',
        string='Cost')

    sale_price_old = fields.Float(
        related='product_id.list_price',
        string='Sale Price',
        readonly=True)

    percentage = fields.Float(
        string='%')

    new_sale_price = fields.Float(
        compute='_compute_new_price', store=True,
        string='Updated Price', readonly=False)

    pricelist_id = fields.Many2many(
        comodel_name='product.pricelist',
        string='Price List')

    is_purchased = fields.Boolean(
        compute='_compute_last_purchase_price', store=True,
        string='Purchase Count', readonly=False)

    last_po = fields.Many2one(
        'purchase.order',
        string='Last Po',
        readonly=True)

    stock_picking_id = fields.Many2one(
        comodel_name='stock.picking',
        string='Stock Picking',
    )
    active = fields.Boolean(
        string='Active',
        default=True,
    )




    # # Ensure that a product can only be in one pricing list
    # @api.constrains('product_id')
    # def constrains_product_id(self):
    #     for record in self:
    #         history_count = self.search_count(
    #             [('product_id', '=', record.product_id.id), ('id', '!=', record.id)]
    #         )
    #         if history_count > 0:
    #             raise ValidationError(
    #                 _('This product is already in the pricing list')
    #             )

    # Compute the last purchase price for each product
    def _compute_last_purchase_price(self):
        for pricing in self:
            price_history = self.env['purchase.order.line'].search([
                ('product_id.product_tmpl_id', '=', pricing.product_id.id),
                ('state', 'in', ['purchase', 'done'])
            ], order='date_order,id desc', limit=1)

            if price_history:
                pricing.last_purchase_price = price_history.price_unit
                pricing.last_po = price_history.order_id.id
                pricing.is_purchased = True
            else:
                pricing.last_purchase_price = 0.0
                pricing.is_purchased = False

        # Compute the new sale price based on cost and percentage
    @api.depends('cost', 'percentage')
    def _compute_new_price(self):
        for product in self:
            if product.percentage > 0:
                product.new_sale_price = product.cost * product.percentage / 100 + product.cost

    # Update the sale price in the selected price list

    def set_price(self):
        if self.pricelist_id and self.pricelist_id.item_ids.filtered(
                lambda l: l.product_tmpl_id == self.product_id):
            for pricelist in self.pricelist_id:
                for line in pricelist.item_ids.filtered(
                        lambda l: l.product_tmpl_id == self.product_id):
                    old_price = line.fixed_price
                    line.fixed_price = self.new_sale_price
                    new_price = self.new_sale_price

                    self._create_price_change_log(old_price, new_price)
        else:
            old_price = self.product_id.list_price
            new_price = self.new_sale_price

            if self.pricelist_id and self.product_id:
                pricelist_item = self.pricelist_id.item_ids.filtered(
                    lambda l: l.product_tmpl_id == self.product_id)

                if pricelist_item:
                    pricelist_item.fixed_price = new_price
                else:
                    self.pricelist_id.write({
                        'item_ids': [(0, 0, {
                            'applied_on': '1_product',
                            'product_tmpl_id': self.product_id.id,
                            'fixed_price': new_price,
                        })]
                    })
            else:
                self.product_id.list_price = new_price

            self._create_price_change_log(old_price, new_price)
        self.active = False
        self.new_sale_price = 0
        self.percentage = 0

    # Show the price change history for a product
    def show_price_history(self):
        action = self.env['ir.actions.act_window']._for_xml_id('sales_pricing.action_product_price_change')
        action['display_name'] = _('History')
        action['context'] = {'create': False}
        action['domain'] = [('product_id', '=', self.product_id.id)]
        return action

    # Create a price change log entry
    def _create_price_change_log(self, old_price, new_price):
        print(old_price)
        print(new_price)
        print(self.product_id)
        if old_price != new_price:
            log_obj = self.env['product.price.change.log']
            log_obj.create({
                'product_id': self.product_id.id,
                'old_price': old_price,
                'new_price': new_price
            })

    # Open the last purchase order for a product
    def open_last_purchase_order(self):
        for product in self:
            if product.last_purchase_price > 0:
                purchase_order = self.env['purchase.order'].search([
                    ('order_line.product_id.product_tmpl_id', '=', product.product_id.id),
                    ('state', 'in', ['purchase', 'done'])]
                    , order='date_order desc', limit=1)

                if purchase_order:
                    return {
                        'type': 'ir.actions.act_window',
                        'res_model': 'purchase.order',
                        'res_id': purchase_order.id,
                        'view_mode': 'form',
                        'target': 'current',
                    }

        return False

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    product_pricing_ids = fields.One2many(
        comodel_name='product.pricing',
        inverse_name='stock_picking_id',
        string='Product Pricing'
    )

    # Modify the button_validate method to create product pricing records
    def button_validate(self):
        res = super(StockPicking, self).button_validate()
        for picking in self:

            if picking.purchase_id:  # Check if purchase_id has a value

                for move in picking.move_ids:
                    product = move.product_id.product_tmpl_id
                    pricing = self.env['product.pricing'].sudo().create({
                        'product_id': product.id,
                        'default_code': product.default_code,
                        'product': product.name,
                        'category_id': product.categ_id.id,
                        'cost': product.standard_price,
                        'sale_price_old': product.list_price,
                        'percentage': 0.0,  # You can update this based on your logic
                        'new_sale_price': 0.0,  # You can update this based on your logic
                        'stock_picking_id': picking.id,  # Set the stock picking reference
                        'is_purchased': False,  # You can update this based on your logic
                        'last_po': False,  # You can update this based on your logic
                    })
                    picking.product_pricing_ids |= pricing

            return res
        def clear_record(self):
            self.ensure_one()  # Ensure only one record is selected
            self.sudo().unlink()  # Delete the record
