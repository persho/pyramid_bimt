========================
Subscriptions & Payments
========================

We support subscriptions and payments via ClickBank and JVZoo. The standard
payment workflow looks like this:

1. User comes to our sales page and chooses a product to order.
2. User is redirected to a payment page on ClickBank/JVZoo where she enters
   her credit card information and performs the payment
3. ClickBank/JVZoo sends a Instant Payment Notification (IPN) request to our
   app.
4. Our app parses the IPN request and creates the user account.
5. The app sets the account's ``valid_to`` date based on the ``validity``
   value of the product the user subscribed to. Each CB/JVZoo product needs a
   ``Group`` instance with ``product_id`` in app's DB.

Ignoring products
=================

Sometimes we sell addons or complimentary products on ClickBank/JVZoo for which
we do not want to have groups assigned in the app. To ignore IPN requests for
such products, list the ``product_id``'s in the ``PRODUCTS_TO_IGNORE``
`Config Var` on the app's Heroku Control Panel (
``https://dashboard.heroku.com/apps/bimt-<APP_Name>/settings``).
