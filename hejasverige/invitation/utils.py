# -*- coding: utf-8 -*-

from zope.component.hooks import getSite
from plone.dexterity.utils import createContent, addContentToContainer
from Products.CMFCore.utils import getToolByName
from hejasverige.invitation.interfaces import IInvitationFolder

import logging
logger = logging.getLogger(__name__)


def add_invitation_to_context(context, invitation):
    ''' adds an invitation to a invitation folder in the provided context
        if no invitation folder is found, it tries to creates one default
    '''
    import pdb; pdb.set_trace()
    portal = getSite()
    catalog = getToolByName(portal, "portal_catalog")
    query = {}
    query['object_provides'] = IInvitationFolder.__identifier__
    query['path'] = dict(query='/'.join(context.getPhysicalPath()))
    invitationfolders = catalog(query)

    if not invitationfolders:
        invitationfolder = createContent(portal_type='hejasverige.invitationfolder', title='invitations',
                                         description='folder for invitations')

        try:
            folder = addContentToContainer(container=context, object=invitationfolder, checkConstraints=True)
            folder.reindexObject()
        except Exception, ex:
            err = 'Unable to create invitaiton folder in', str(folder), 'due to', str(ex)
            logger.exception(err)
            return None
    else:
        folder = invitationfolders[0].getObject()

    invitationobject = createContent(portal_type='hejasverige.invitation',
                                 sender_id=invitation.get('sender_id', None), 
                                 first_name=invitation.get('first_name', None), 
                                 last_name=invitation.get('last_name', None),
                                 personal_id=invitation.get('personal_id', None),
                                 recipient_email=invitation.get('recipient_email', None),
                                 invitation_expires=invitation.get('invitation_expires', None)

                            )
    try:
        item = addContentToContainer(container=folder, object=invitationobject, checkConstraints=True)
        item.reindexObject()
    except Exception, ex:
        err = 'Unable to add invitation to', str(folder), 'due to', str(ex)
        logger.exception(err)
        return None
    return item