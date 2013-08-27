# -*- coding: utf-8 -*-

from plone.directives import form
from zope import schema

from hejasverige.invitation import _

class IInvitationFolder(form.Schema):
    """ A invitation folder used to contain invitations
    """


class IInvitation(form.Schema):
    """ A relation object filed under a person
    """

    # fe9d2f4983624a20a7403ced09d6a162
    # 5965123a425a44cb897078004a60452f
    sender_id = schema.ASCIILine(
        title=_(u"Sender id"),
        required=True,
        )

    first_name = schema.TextLine(
        title=_(u"First name"),
        required=True,
        )

    last_name = schema.TextLine(
        title=_(u"Last name"),
        required=True,
        )

    personal_id = schema.TextLine(
        title=_(u"Personal id"),
        required=True,
        )

    recipient_email = schema.TextLine(
        title=_(u"Recipient email"),
        required=True,
        )

    invitation_expires = schema.Datetime(
        title=_(u"Expiration time"),
        required=True,
        )

