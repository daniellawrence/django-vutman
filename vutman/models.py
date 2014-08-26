from django.db import models
from cuser.fields import CurrentUserField
from django.core.urlresolvers import reverse
from simple_history.models import HistoricalRecords


class VutmanModel(models.Model):
    STATE_CHOICES = (
        ('E', 'Enabled'),
        ('D', 'Disabled'),
        ('X', 'Deleted'),
    )
    state = models.CharField(max_length=1, choices=STATE_CHOICES, default="E")
    last_modified = models.DateTimeField(auto_now=True, auto_now_add=True)
    last_modified_by = CurrentUserField()

    def get_absolute_url(self):
        object_type = self.__class__.__name__.lower()
        return reverse('%s.details' % object_type, args=[str(self.id)])

    def disable(self):
        self.state = "D"
        self.save()

    class Meta:
        abstract = True


class EmailServer(VutmanModel):
    email_server = models.CharField(max_length=200, unique=True)
    history = HistoricalRecords()

    def __str__(self):
        return self.email_server


class EmailDomain(VutmanModel):
    domain_name = models.CharField(max_length=200, unique=True)
    history = HistoricalRecords()

    def __str__(self):
        return self.domain_name


class EmailUser(VutmanModel):
    username = models.CharField(max_length=200)
    fullname = models.CharField(max_length=200, blank=True)
    email_server = models.ForeignKey(EmailServer)
    active_directory_basedn = models.CharField(blank=True, max_length=200)
    history = HistoricalRecords()

    def __str__(self):
        return self.username

    class Meta:
        unique_together = (("username", "email_server"))

    def get_history(self):
        history_all = []
        last = self.__dict__
        for history in self.history.all():
            change = {}
            for k, v in history.__dict__.items():
                if k in ['_state', 'last_modified', 'last_modified_by',
                         'history_id', 'history_type', 'history_date',
                         'history_user_id', 'last_modified_by_id'
                     ]:
                    continue
                if k in last and last[k] != v:
                    change[k] = (v, last[k])
            last = history.__dict__
            if change:
                history.__dict__['changed'] = change
                history_all.append(history)
        return history_all

    def _suggested_aliases(self):
        " Suggest aliases for the user "
        aliases = []
        names = self.fullname.split()
        aliases.append(".".join(names))
        aliases.append("%s%s" % (names[0][0], names[-1]))
        aliases.append(self.username)
        return aliases

    def suggested_aliases(self):
        " Suggest aliases for the user without any duplicates "
        aliases = self._suggested_aliases()
        new_aliases = []
        known_aliases = [a.alias_name for a in EmailAlias.objects.all()]
        for a in aliases:
            if a in known_aliases:
                continue
            new_aliases.append(a)
        return new_aliases

    def guess_fullname(self):
        for my_alias in EmailAlias.objects.filter(username=self):
            if '_' in my_alias.alias_name:
                name = ' '.join(my_alias.alias_name.split('_'))
                return name

            if '.' in my_alias.alias_name:
                name = ' '.join(my_alias.alias_name.split('.'))
                return name

    def set_guessed_name(self):
        if self.fullname:
            return

        self.fullname = self.guess_fullname()
        self.save()


class EmailAlias(VutmanModel):
    alias_name = models.CharField(max_length=50)
    username = models.ForeignKey(EmailUser)
    email_domain = models.ForeignKey(EmailDomain)
    history = HistoricalRecords()

    def __str__(self):
        return "%s@%s" % (self.alias_name, self.email_domain)

    def vut_entry(self):
        return "%s@%s: %s@%s" % (
            self.alias_name,
            self.email_domain,
            self.username.username,
            self.username.email_server
        )

    class Meta:
        unique_together = (("alias_name", "email_domain"))
        verbose_name_plural = "aliases"
