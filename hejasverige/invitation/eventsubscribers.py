# -*- coding: utf-8 -*-

from five import grok

from smtplib import SMTPRecipientsRefused
from zope.app.container.interfaces import IObjectAddedEvent
from hejasverige.invitation.interfaces import IInvitation
from zope.component.hooks import getSite
#from plone import api
from Products.CMFPlone.utils import safe_unicode
from Products.CMFPlone.utils import getToolByName


import logging

logger = logging.getLogger(__name__)


def sendEmailNotification(obj):

    import pdb; pdb.set_trace()

    site = getSite()
    email_charset = getattr(obj, 'email_charset', 'utf-8')
    

    mail_template = site.unrestrictedTraverse('@@newinvitationnotification')
    mail_text = mail_template(invitation=obj,
                              charset=email_charset,
                              portal_url = site.absolute_url(),
                              request=obj.REQUEST
                              )

    try:
        host = getToolByName(obj, 'MailHost')
        # The ``immediate`` parameter causes an email to be sent immediately
        # (if any error is raised) rather than sent at the transaction
        # boundary or queued for later delivery.
        result = host.send(safe_unicode(mail_text), immediate=True)
        logger.info('Email queue returned %s' % str(result))
        comment = 'Invitation sent to %s. Mail host returned: %s' % (obj.recipient_email, str(result))
        workflow = getToolByName(site, "portal_workflow")
        workflow.doActionFor(obj, 'pend', comment=comment)
        new_state = workflow.getInfoFor(obj, 'review_state')
        logger.info("Object %s changed state to %s" % (obj.absolute_url_path(), new_state))
    except SMTPRecipientsRefused:
        # Don't disclose email address on failure
        raise SMTPRecipientsRefused('Recipient address rejected by server')


@grok.subscribe(IInvitation, IObjectAddedEvent)
def sendInvitationEvent(obj, event):
    print 'Sending notification to provided email'
    #import pdb; pdb.set_trace()
    sendEmailNotification(obj)