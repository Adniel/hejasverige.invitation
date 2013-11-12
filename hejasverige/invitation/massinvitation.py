# -*- coding: utf-8 -*-

# Core Zope 2 + Zope 3 + Plone
from five import grok
from Products.statusmessages.interfaces import IStatusMessage

# Form and validation
import z3c.form.button
from plone.directives import form

import StringIO
import csv
import datetime

from plone.namedfile.field import NamedFile

from hejasverige.content.sports import IClub
from hejasverige.content.interfaces import IMyPages
from hejasverige.invitation import _

from hejasverige.invitation.utils import add_invitation_to_context


class IImportUsersFormSchema(form.Schema):
    """ Define fields used on the form """

    csv_file = NamedFile(title=_(u"Medlemsfil"))


class ImportUsersForm(form.SchemaForm):
    """ A sample form showing how to mass invite persons using an
        uploaded CSV file.
    """

    grok.require("hejasverige.InviteMember")
    grok.implements(IMyPages)
    grok.context(IClub)
    grok.name("invite-members")

    ignoreContext = True
    schema = IImportUsersFormSchema
    name = _(u"Invite members")
    description = _(u'Beskrivning här')
    def update(self):
        # disable Plone's editable border
        self.request.set('disable_border', True)

        # call the base class version - this is very important!
        super(ImportUsersForm, self).update()
        #form.SchemaForm.update()

    def processCSV(self, data):
        """
        """
        #import pdb;pdb.set_trace()

        io = StringIO.StringIO(data)

        reader = csv.reader(io, delimiter=',', dialect="excel", quotechar='"')

        header = reader.next()
        print header

        def get_cell(row, name):
            """ Read one cell on a
                @param row: CSV row as list
                @param name: Column name: 1st row cell content value, header
            """

            assert type(name) == unicode, "Column names must be unicode"

            index = None
            for i in range(0, len(header)):
                if header[i].decode("utf-8") == name:
                    index = i

            if index is None:
                raise RuntimeError("CSV data does not have column:" + name)

            return row[index].decode("utf-8")

        updated = 0
        for row in reader:
            invitation = {}
            invitation['sender_id'] = self.__parent__.UID()
            invitation['first_name'] = get_cell(row, u'Förnamn')
            invitation['last_name'] = get_cell(row, u'Efternamn')
            invitation['recipient_email'] = get_cell(row, u'Epost')
            invitation['personal_id'] = get_cell(row, u'Personnummer')
            invitation['invitation_expires'] = datetime.datetime.now() + datetime.timedelta(days=30)
            # check constraints ...
            import pdb; pdb.set_trace()
            add_invitation_to_context(self.__parent__, invitation)
            updated += 1

        return updated

    @z3c.form.button.buttonAndHandler(_('Bjud in'), name='invite')
    def inviteMembers(self, action):
        """ Create and handle form button "Invite members"
        """

        # Extract form field values and errors from HTTP request
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return

        # Do magic
        file = data["csv_file"].data

        number = self.processCSV(file)

        # If everything was ok post success note
        # Note you can also use self.status here unless you do redirects
        if number is not None:
            # mark only as finished if we get the new object
            IStatusMessage(self.request).addStatusMessage(_(u"Created/updated invitations: ") +
                                                          unicode(number), "info")
