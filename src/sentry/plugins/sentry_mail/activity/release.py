from __future__ import absolute_import

from sentry.db.models.query import in_iexact
from sentry.models import Release, ReleaseCommit, User

from .base import ActivityEmail


class ReleaseActivityEmail(ActivityEmail):
    def __init__(self, activity):
        super(ReleaseActivityEmail, self).__init__(activity)
        try:
            self.release = Release.objects.get(
                project=self.project,
                version=activity.data['version'],
            )
        except Release.DoesNotExist:
            self.release = None
            self.commit_list = []
        else:
            self.commit_list = [
                rc.commit
                for rc in ReleaseCommit.objects.filter(
                    release=self.release,
                ).select_related('commit', 'commit__author')
            ]

    def should_email(self):
        return self.release is not None

    def get_participants(self):
        project = self.project

        email_list = set([
            c.author.email for c in self.commit_list
            if c.author
        ])

        return set(User.objects.filter(
            in_iexact('useremail__email', email_list),
            sentry_orgmember_set__teams=project.team,
            is_active=True,
        ).distinct())

    def get_base_context(self):
        context = super(ReleaseActivityEmail, self).get_base_context()

        context.update({
            'commit_list': self.commit_list,
        })
        return context

    def get_template(self):
        return 'sentry/emails/activity/release.txt'

    def get_html_template(self):
        return 'sentry/emails/activity/release.html'
