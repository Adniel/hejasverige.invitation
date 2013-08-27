# -*- coding: utf-8 -*-

from five import grok
from hejasverige.invitation import _
from hejasverige.content.interfaces import IMyPages
from hejasverige.content.person import IPerson
from plone import api
from plone.app.layout.navigation.interfaces import INavigationRoot
from plone.app.uuid.utils import uuidToObject
from plone.dexterity.utils import createContent, addContentToContainer
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.WorkflowCore import WorkflowException
from zExceptions import Forbidden
from z3c.form import form, field
from zope.component.hooks import getSite
from zope.component import getMultiAdapter
from hejasverige.invitation.interfaces import IInvitationFolder
from hejasverige.content.sports import IClub
import datetime
import logging
logger = logging.getLogger(__name__)

grok.templatedir("templates")


class InviteMemberForm(grok.View):
    grok.context(IClub)
    grok.name('invite-member')
    grok.require('hejasverige.AddInvitation') # should reflect someone with admin rights on the Club
    grok.template('invitemember')
    grok.implements(IMyPages)

    
    def add_invitation(self, container, invitation):
        invitationobject = createContent(portal_type='hejasverige.invitation',
                                     sender_id=invitation.get('sender_id', None), 
                                     first_name=invitation.get('first_name', None), 
                                     last_name=invitation.get('last_name', None), 
                                     personal_id=invitation.get('personal_id', None),
                                     recipient_email=invitation.get('recipient_email', None),
                                     invitation_expires=invitation.get('invitation_expires', None)

                                )
        try:
            item = addContentToContainer(container=container, object=invitationobject, checkConstraints=False)
            item.reidexObject()
        except Exception, ex:
            err = 'Unable to add invitation with id', id, 'to', str(container), 'due to', str(ex)
            logger.exception(err)
            return None
        return item

    def update(self):
        ''' Nothing
        '''
        #import pdb; pdb.set_trace()

        self.invitation_folder_present = False
        invitationfolder = None
        portal = getSite()
        catalog = getToolByName(portal, "portal_catalog")
        query = {}
        query['object_provides'] = IInvitationFolder.__identifier__
        query['path'] = dict(query='/'.join(self.context.getPhysicalPath()))
        invitationfolders = catalog(query)

        if invitationfolders:
            self.invitation_folder_present = True
            invitationfolder = invitationfolders[0].getObject()
            logger.info('Found invitation folder: %s' % invitationfolder.absolute_url())
        else:
            logger.error('There is no folder providing the IInvitationFolder interface for this context: %s' % self.absolute_url())
            utils = getToolByName(self, "plone_utils")
            utils.addPortalMessage(_(u'Det finns ingen folder för inbjudningar registrerad hos föreningen. Kontakta en administratör.'), 'error')

            url = self.context.absolute_url()
            return self.request.response.redirect(url)

        # is it a post-back
        if 'form.button.Invite' in self.request.form:
            invitation = {}
            invitation['sender_id'] = self.__parent__.UID()
            invitation['first_name'] = self.request.get('first_name', None)
            invitation['last_name'] = self.request.get('last_name', None)
            invitation['recipient_email'] = self.request.get('recipient_email', None)
            invitation['personal_id'] = self.request.get('personal_id', None)
            # Create time delta, possible configurable
            invitation_expires = datetime.datetime.now() + datetime.timedelta(days=30)
            logger.debug('Invitation expires: %s' % invitation_expires)
            invitation['invitation_expires'] = invitation_expires
            container = portal.restrictedTraverse(invitationfolder.absolute_url_path())

            self.add_invitation(container, invitation)

            url = self.context.absolute_url()
            return self.request.response.redirect(url)

        self.clubname = self.__parent__.Title()

class ConfirmInvitationView(grok.View):
    """View (called "@@confirm-invititation") when user opens a link to an invite.

       The associated template is found in invitation_templates/invite.pt.
    """

    grok.context(INavigationRoot)
    grok.require('zope2.View')
    grok.name('confirm-invitation')
    grok.implements(IMyPages)
    grok.template('confirminvitation')

    def change_state(self, item, transition, comment=''):
        workflow = getToolByName(item, 'portal_workflow')
        #import pdb; pdb.set_trace()

        try:
            workflow.doActionFor(item, transition, comment=comment)
            new_state = workflow.getInfoFor(item, 'review_state')
            logger.info("Object %s changed state to %s" % (item.absolute_url_path(), new_state))
        except WorkflowException:
            logger.exception("Could not apply workflow transition %s. %s state not changed" % (transition, item.absolute_url_path()))
            return False

        return True

    def add_relation(self, id, container, member_type='supporter'):
        
        relobj = createContent(portal_type='hejasverige.relation',
                                 foreign_id=id,
                                )

        #import pdb; pdb.set_trace()

        try:
            item = addContentToContainer(container=container, object=relobj, checkConstraints=False)
        except Exception, ex:
            err = 'Unable to add relation with id', id, 'to', str(container), 'due to', str(ex)
            logger.exception(err)
            utils = getToolByName(self, "plone_utils")
            utils.addPortalMessage(_(err), 'error')
            return None
        else:
            # Push to member state depending on type
            if member_type == 'member':
                result = self.change_state(item, 'pend')
                if result:
                    self.change_state(item, 'approve')
            else:
                self.change_state(item, 'support')



        return item 

    def get_invitation(self, invitation_id):
            query = {}
            #query['object_provides'] = IInvitation.__identifier__
            query['UID'] = invitation_id

            catalog = getToolByName(self, "portal_catalog")
            result =  catalog.unrestrictedSearchResults(query)

            if len(result)==0:
                logger.error('No invitiation with invitation id %s found when querying the catalog' % invitation_id)
                return None           
            return result[0]

    def add_person(self, container, person):
        personobject = createContent(portal_type='hejasverige.person',
                                 first_name=person.get('first_name', None), last_name=person.get('last_name', None), personal_id=person.get('personal_id', None)
                                )

        #import pdb; pdb.set_trace()

        try:
            item = addContentToContainer(container=container, object=personobject, checkConstraints=False)
        except Exception, ex:
            err = 'Unable to add person with id', id, 'to', str(container), 'due to', str(ex)
            logger.exception(err)
            return None
        return item


    def update(self):
        """Called before rendering the template for this view
        """

        # # # # # # # # # # # # # # # # # # # # #
        # is this a submit of the view's form?
        # # # # # # # # # # # # # # # # # # # # #        
        if 'form.submit.confirm' in self.request.form and self.request.get('REQUEST_METHOD') == 'POST':
            self.invitation_id = self.request.get('form.invitation.id', None)

            authenticator = getMultiAdapter((self.context, self.request), name=u"authenticator")

            #import pdb; pdb.set_trace()
            if not authenticator.verify():
                raise Forbidden()
            
            # default redirect url
            url = self.context.absolute_url()

            # the invitation id is missing in the sent form, seriously error
            if not self.invitation_id:
                logger.error('No invitation id was posted with the form. That should not be possible.')
            else:
                relation_context = self.request.get('form.invitor.relation_context', None) 
                portal = getSite()

                if relation_context != None and relation_context != 'new':
                    #import pdb; pdb.set_trace()
                    container = portal.unrestrictedTraverse(relation_context)  

                # The person does not exist. Add him/her first
                if relation_context == 'new':
                    logger.info('New person found. Adding person.')
                    mship = getToolByName(self, "portal_membership")
                    home = mship.getHomeFolder()
                    invitation = self.get_invitation(self.invitation_id).getObject()

                    person = {}
                    person['first_name'] = invitation.first_name
                    person['last_name'] = invitation.last_name
                    person['personal_id'] = invitation.personal_id

                    myfamily = portal.unrestrictedTraverse('/'.join(home.getPhysicalPath() + ('my-family/',)))
                    container = self.add_person(myfamily, person)

                # if there is an invitor ID and an container to add a relation found
                if self.request.get('form.invitor.id', None) and container:
                    portalmessage = None
                    # check that the person is not already member
                    # create a dictionary of all realtions with the club_id as key
                    existing_relations = [(c[1].foreign_id, c[1]) for c in container.contentItems()]
                    existing_relations = dict(existing_relations)
                    if self.request.get('form.invitor.id') in existing_relations.keys():
                        # do something intelligent
                        #    + uppgrade supporter to member?
                        #    - change state on invitation so it can not be used anymore

                        relation_object = existing_relations[self.request.get('form.invitor.id')]
                        workflow = getToolByName(self,'portal_workflow')
                        current_state = workflow.getInfoFor(relation_object, 'review_state')
                        logger.debug('The user or invited person has a relation in state %s with the invitor already.' % current_state)

                        # init result, no transition has completed well for the relation yet
                        result = None
                        if current_state == 'supporter':
                            result = self.change_state(relation_object, 'retract')
                            if result:
                                result = self.change_state(relation_object, 'approve')
                        elif current_state == 'pending':
                            result = self.change_state(relation_object, 'approve')

                        elif current_state == 'created':
                            result = self.change_state(relation_object, 'pend')
                            if result:
                                result = self.change_state(relation_object, 'approve')
                        elif current_state == 'approved ':
                            #do nothing, well possibly inform
                            pass
                        elif current_state == 'rejected':
                            result = self.change_state(relation_object, 'retract')

                        # if things went well, approve the invitation and make it unusable
                        invitation_brain = self.get_invitation(self.invitation_id)
                        if result:
                            comment = relation_object.absolute_url_path() + ' (UID:' + relation_object.UID() + ')'
                            self.change_state(invitation_brain.getObject(), 'approve', comment=comment)
                            portalmessage = u'Du är nu ansluten till föreningen'
                            portalmessage_type = 'info'
                            logger.info('Relation %s approved through invitation %s' % (relation_object.absolute_url_path(), invitation_brain.getURL()))


                    else:
                        logger.info('The user or person does not have a relation with the invitor yet. Adding a relation.')
                        added_item = self.add_relation(self.request.get('form.invitor.id'), container, member_type='member')
                        url = added_item.absolute_url()
                        portalmessage = u'Du är nu ansluten till föreningen'
                        portalmessage_type = 'info'
                    
                    if portalmessage:
                        utils = getToolByName(self, "plone_utils")
                        utils.addPortalMessage(_(portalmessage), portalmessage_type)
                

            return self.request.response.redirect(url)
        
        # The confirm button was no pressed (The reject button was pressed)
        elif self.request.get('REQUEST_METHOD') =='POST':
            self.invitation_id = self.request.get('form.invitation.id', None)
            logger.info('Invitation with id %s rejected' % self.invitation_id)
            invitation_brain = self.get_invitation(self.invitation_id)
            # kommentar bör kunna tillhandahållas i ett formulär. Sedan. inte nu.
            comment = ''
            self.change_state(invitation_brain.getObject(), 'reject', comment=comment)

            url = self.context.absolute_url()
            utils = getToolByName(self, "plone_utils")
            utils.addPortalMessage(_(u'Inbjudan ej accepterad'), 'info')
            return self.request.response.redirect(url)
    
        # # # # # # # # # # # # # # # # # # # # #
        # The VIEW
        # # # # # # # # # # # # # # # # # # # # #
        self.request.set('disable_border', True)
        self.invitation_status = {}
        self.invitation_status['has_ok_invitation'] = False
        self.invitation_status['is_self'] = False
        self.invitation_status['is_registered_person'] = False
        self.invitation_status['is_new_person'] = False
        self.invitation_status['no_id_provided'] = False
        self.invitation_status['is_expired'] = False
        self.invitation_data = None
        self.invitation_id = self.request.get('id', None)
        
        if not self.invitation_id:
                logger.info('No invitation provided in querystring')
        else:
            #import pdb; pdb.set_trace()
            invitation_brain = self.get_invitation(self.invitation_id)
            #  - if no invitation with sent Id is found, return "error"
            #  - if invitation is found and used, move forward in workflow.
            #  - Scenarios:
            #        1. Invited person is the user
            #           - Confirm add relation
            #           - Add relation with status confirmed
            #           - If rejected, set invitation as status 'rejected', otherwise 'confirmed'
            #        2. Invited person is a registered relative
            #           - Confirm add relation to relative
            #           - Add relation with status confirmed
            #           - If rejected, set invitation as status 'rejected', otherwise 'confirmed'
            #        3. Invited person is an unknown person in relation to the logged in user
            #           - Confirm scenario
            #           - Add person with data from invitation
            #           - Add relation to person with status confirmed
            #           - If rejected, set invitation as status 'rejected', otherwise 'confirmed'


            # is there an invitation with the provided id?
            # import pdb; pdb.set_trace()
            if not invitation_brain:
                logger.info('An invitation with id [%s] does not exist' % self.invitation_id)

            # is there viewer anonymous
            elif api.user.is_anonymous() == True:
                logger.exception('Something is strange. The current user is reported as anonymous, but the view should require logged in user.')

            # is the invitation in state 'pending'
            elif invitation_brain.review_state != 'pending':

                logger.info('The invitation %s has an incorrect state: %s' % (self.invitation_id, invitation_brain.review_state))
            elif invitation_brain.ExpirationDate < datetime.datetime.now():
                self.invitation_status['is_expired'] = True
                logger.info('The invitation %s has expired: %s' % (self.invitation_id, invitation_brain.ExpirationDate))
            else:
                self.invitation = invitation_brain.getObject()

                # make sure the sender is available to the logged in user
                #catalog.unrestrictedSearchResults({'UID'})

                user = api.user.get_current()
                current_personal_id = user.getProperty('personal_id')

                # This is the current user (hope invited name is correct :)
                if current_personal_id == self.invitation.personal_id:
                    mship = getToolByName(self, "portal_membership")
                    home = mship.getHomeFolder()

                    self.invitation_data = dict(personal_id=self.invitation.personal_id,
                                                first_name=self.invitation.first_name,
                                                last_name=self.invitation.last_name,
                                                invitor=uuidToObject(self.invitation.sender_id).Title(),
                                                invitor_id=self.invitation.sender_id,
                                                relation_context='/'.join(home.getPhysicalPath() + ('my-clubs/',))
                                                )

                    self.invitation_status['is_self'] = True

                # This is possibly a registered family member
                else:
                    catalog = getToolByName(self, "portal_catalog")

                    mship = getToolByName(self, "portal_membership")
                    home = mship.getHomeFolder()
                    family = catalog({'object_provides': IPerson.__identifier__,
                            'path': dict(query='/'.join(home.getPhysicalPath())), 
                            'sort_on': 'sortable_title'})                
                    
                    matching_persons = [p for p in family if p.personal_id==self.invitation.personal_id]

                    # get the matching person
                    if len(matching_persons)>0:
                        self.invitation_data = dict(personal_id=matching_persons[0].personal_id,
                                                    first_name=matching_persons[0].getObject().first_name,
                                                    last_name=matching_persons[0].getObject().last_name,
                                                    invitor=uuidToObject(self.invitation.sender_id).Title(),
                                                    invitor_id=self.invitation.sender_id,
                                                    relation_context=matching_persons[0].getPath()
                                                    )
                        
                        self.invitation_status['is_registered_person'] = True

                        #import pdb; pdb.set_trace()
                    
                    # it is a new person not registered yet
                    else:
                        self.invitation_data = dict(personal_id=self.invitation.personal_id,
                                                    first_name=self.invitation.first_name,
                                                    last_name=self.invitation.last_name,
                                                    invitor=uuidToObject(self.invitation.sender_id).Title(),
                                                    invitor_id=self.invitation.sender_id,
                                                    relation_context='new'
                                                    )
                        self.invitation_status['is_new_person'] = True
    
                self.invitation_status['has_ok_invitation'] = True

                #import pdb; pdb.set_trace()
