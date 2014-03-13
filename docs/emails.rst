==================
Sending out emails
==================

Here is an example of how you should construct and send out an email, using
``pyramid_mailer`` and a BIMT-specific email template.

.. code-block:: python

    from pyramid.renderers import render
    from pyramid_mailer import get_mailer
    from pyramid_mailer.message import Message

    def send_an_email(self, request):
        mailer = get_mailer(self.request)
        body = """
            <div>
              <p>Hello,</p>
              <p>this is a dummy email!</p>
            </div>
        """

        mailer.send(Message(
            recipients=['foo@bar.com', ],
            subject=u'Hello!',
            html=render('pyramid_bimt:templates/email.pt', {'body': body}),
        ))

