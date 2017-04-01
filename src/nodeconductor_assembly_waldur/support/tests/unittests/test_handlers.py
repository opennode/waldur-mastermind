from django.conf import settings
from django.core import mail
from django.test import TestCase

from .. import factories


class BaseHandlerTest(TestCase):

    def setUp(self):
        settings.CELERY_ALWAYS_EAGER = True

    def tearDown(self):
        settings.CELERY_ALWAYS_EAGER = False


class IssueUpdatedHandlerTest(BaseHandlerTest):

    def test_email_notification_is_sent_when_issue_is_updated(self):
        issue = factories.IssueFactory()

        issue.summary = 'new_summary'
        issue.save()

        self.assertEqual(len(mail.outbox), 1)

    def test_email_notification_is_not_sent_on_issue_creation(self):
        factories.IssueFactory()

        self.assertEqual(len(mail.outbox), 0)

    def test_email_notification_is_not_sent_if_feature_is_suppressed(self):
        with self.settings(SUPPRESS_NOTIFICATION_EMAILS=True):
            issue = factories.IssueFactory()

            issue.summary = 'new_summary'
            issue.save()

            self.assertEqual(len(mail.outbox), 0)


class CommentCreatedHandlerTest(BaseHandlerTest):

    def test_email_is_sent_when_comment_is_created(self):
        factories.CommentFactory()

        self.assertEqual(len(mail.outbox), 1)

    def test_email_is_not_sent_when_comment_is_updated(self):
        comment = factories.CommentFactory()
        self.assertEqual(len(mail.outbox), 1)

        comment.description = 'new_description'
        comment.save()

        self.assertEqual(len(mail.outbox), 1)

    def test_email_is_not_set_if_feature_is_suppressed(self):
        with self.settings(SUPPRESS_NOTIFICATION_EMAILS=True):
            factories.CommentFactory()

            self.assertEqual(len(mail.outbox), 0)
