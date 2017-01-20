from __future__ import unicode_literals

from datetime import timedelta

from nodeconductor.core import NodeConductorExtension


class SupportExtension(NodeConductorExtension):
    class Settings(object):
        WALDUR_SUPPORT = {
            'ACTIVE_BACKEND': 'nodeconductor_assembly_waldur.support.backend.atlassian:JiraBackend',
            'CREDENTIALS': {
                'server': 'http://example.com/',
                'username': 'USERNAME',
                'password': 'PASSWORD',
                'verify_ssl': False,
            },
            'PROJECT': {
                'key': 'PROJECT',
            },
            'ISSUE': {
                'types': ['Informational', 'Service Request', 'Change Request', 'Incident'],
                'impact_field': 'Impact',
                'reporter_field': 'Original Reporter',
                'caller_field': 'Caller',
                'sla_field': 'Time to first response',
            },
            'DEFAULT_OFFERING_TYPE': 'Service Request',
            'OFFERING': {
                'custom_vpc': {
                    'label': 'Custom VPC',
                    'order': ['name', 'description', 'storage', 'ram', 'cpu_count'],
                    'options': {
                        'name': {
                            'default': 'My Custom VPC',
                            'label': 'Name'
                        },
                        'description': {
                            'type': 'string',
                            'label': 'Description',
                        },
                        'storage': {
                            'type': 'integer',
                            'label': 'Max storage, GB',
                            'help_text': 'VPC storage limit in GB.',
                        },
                        'ram': {
                            'type': 'integer',
                            'label': 'Max RAM, GB',
                            'help_text': 'VPC RAM limit in GB.',
                        },
                        'cpu_count': {
                            'type': 'integer',
                            'label': 'Max vCPU',
                            'help_text': 'VPC CPU count limit.',
                        },
                    },
                },
            },
        }

    @staticmethod
    def django_app():
        return 'nodeconductor_assembly_waldur.support'

    @staticmethod
    def django_urls():
        from .urls import urlpatterns
        return urlpatterns

    @staticmethod
    def rest_urls():
        from .urls import register_in
        return register_in

    @staticmethod
    def is_assembly():
        return True

    @staticmethod
    def celery_tasks():
        return {
            'pull-support-users': {
                'task': 'support.SupportUserPullTask',
                'schedule': timedelta(hours=6),
                'args': (),
            },
        }
