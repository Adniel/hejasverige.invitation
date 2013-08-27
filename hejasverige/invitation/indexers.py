# -*- coding: utf-8 -*-

from DateTime import DateTime
from five import grok
from plone.indexer.decorator import indexer
from plone.app.uuid.utils import uuidToObject

from hejasverige.invitation.interfaces import IInvitation
from hejasverige.invitation import _


@indexer(IInvitation)
def invitationTitleIndexer(context):
    return " ".join((uuidToObject(context.sender_id).Title(),
                     ' - ',
                     context.first_name + ' ' + context.last_name,
                     ' - ',
                     context.personal_id
                     )
                    )
grok.global_adapter(invitationTitleIndexer, name="Title")


@indexer(IInvitation)
def invitationExternalIdIndexer(context):
    return context.sender_id
grok.global_adapter(invitationExternalIdIndexer, name="externalId")


@indexer(IInvitation)
def invitationSearchableTextIndexer(context):
    return [context.sender_id, context.first_name, context.last_name, context.personal_id, context.recipient_email]
grok.global_adapter(invitationSearchableTextIndexer, name="SearchableText")


@indexer(IInvitation)
def invitationSubjectIndexer(context):
    return [context.sender_id, context.first_name, context.last_name, context.personal_id, context.recipient_email]
grok.global_adapter(invitationSubjectIndexer, name="Subject")


@indexer(IInvitation)
def invitationExpirationDateIndexer(context):
    if context.invitation_expires is None:
        return None
    return context.invitation_expires
grok.global_adapter(invitationExpirationDateIndexer, name="ExpirationDate")


@indexer(IInvitation)
def invitationEndIndexer(context):
    if context.invitation_expires is None:
        return None
    return DateTime(context.invitation_expires.isoformat())
grok.global_adapter(invitationEndIndexer, name="end")
