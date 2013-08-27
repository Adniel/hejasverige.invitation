# -*- coding: utf-8 -*-

from five import grok
from Products.CMFCore.interfaces import ISiteRoot
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

import logging
logger = logging.getLogger(__name__)

class NewInvitationNotification(grok.View):
    """View (called "@@newinvitationnotification"")
    """

    grok.context(ISiteRoot)
    grok.require('zope2.View')

    newinvitation = ViewPageTemplateFile("newinvitationnotification.pt")
    newinvitation_html = ViewPageTemplateFile("newinvitationnotification_html.pt")

    def render(self):
        text = self.newinvitation(charset=self.charset, portal_url=self.portal_url, invitation=self.invitation, request=self.request)
        html = self.newinvitation_html(charset=self.charset, portal_url=self.portal_url, invitation=self.invitation, request=self.request)

        #import pdb; pdb.set_trace()
        text = text.encode('utf-8')
        html = html.encode('utf-8')
        #utf8_str = unicode(iso885915_str, 'iso-8859-15').encode('utf-8')
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        msg = MIMEMultipart('alternative')
        msg.set_charset(self.charset)
        msg['Subject'] = "Heja Sverige: Ny inbjudan att registreras som medlem i förening"
        msg['From'] = self.email_from_address
        msg['To'] = self.invitation.recipient_email

        part1 = MIMEText(text, 'plain')
        part1.set_charset(self.charset)
        part2 = MIMEText(html, 'html')
        part2.set_charset(self.charset)
        
        msg.attach(part1)
        msg.attach(part2)

        return msg


    def __call__(self, invitation, charset, portal_url, request):
        """Called before rendering the template for this view
        """
        #import pdb; pdb.set_trace()

        self.invitation = invitation
        self.charset = charset
        self.portal_url = portal_url
        self.request = request
        self.email_from_name = 'Heja Sverige'
        self.email_from_address = 'noreply@heja-sverige.se'
        #import pdb; pdb.set_trace()
        return self.render()


    
