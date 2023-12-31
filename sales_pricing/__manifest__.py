# -*- coding: utf-8 -*-
{
    'name': "Product Pricing",
    'summary': """ Navigate to the "Product Price Change Log" to view a history of price changes for products.***
Access the "Product Pricing" menu to manage product pricing and view last purchase prices.***
Use the "Set" button to update product prices based on selected price lists or manually set new prices.***
Access the "History" button to view the price change history for a specific product.***
Click on the "Last Purchase" price to navigate to the last purchase order associated with that product.***
This module helps you efficiently manage and track product pricing changes, ensuring transparency and accuracy in your pricing strategy.""",

    'description': """This module allows you to maintain a comprehensive log of price changes for your products \n 
Records the old and new prices whenever a price change occurs.\n
Captures the user who made the price change and the timestamp.\n
Prevents deletion of price change log entries to maintain a complete history.\n
Users can view and manage pricing information for products.\n
The last purchase price is computed based on purchase history.\n
Users can manually update product prices and specify a percentage change.\n
Integration with price lists allows for bulk pricing management.\n
Products that have not been purchased before can be added to price lists.\n
Users can access the purchase history for a product.\n
The module checks purchase history to compute the last purchase price for products.\n
Users can navigate to the last purchase order related to a product for further details.
""",
    'author': "Nader Sayed",
    'website': "https://www.linkedin.com/in/nader-sayed-y/",
    'category': 'purchasing/pricing',
    'version': '0.1',

    'depends': ['base', 'purchase', 'stock'],

    # always loaded
    'data': [
        'views/report_pricing.xml',
        'views/product_pricing_history_views.xml',
        'security/ir.model.access.csv',
    ],

    # 'js': ['sales_pricing/static/src/js/last_purchase_widget.js']

}
