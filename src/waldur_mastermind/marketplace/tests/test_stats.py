import decimal

from django.utils import timezone
from freezegun import freeze_time
from rest_framework import status, test

from waldur_core.core import utils as core_utils
from waldur_core.structure.tests import fixtures as structure_fixtures
from waldur_mastermind.common.mixins import UnitPriceMixin
from waldur_mastermind.common.utils import parse_date
from waldur_mastermind.invoices import models as invoices_models
from waldur_mastermind.invoices import tasks as invoices_tasks
from waldur_mastermind.marketplace import models, tasks, utils
from waldur_mastermind.marketplace.tests import factories, helpers
from waldur_mastermind.marketplace_openstack import PACKAGE_TYPE
from waldur_mastermind.marketplace_support import PLUGIN_NAME


class StatsBaseTest(test.APITransactionTestCase):
    def setUp(self):
        self.fixture = structure_fixtures.ProjectFixture()
        self.customer = self.fixture.customer
        self.project = self.fixture.project

        self.category = factories.CategoryFactory()
        self.category_component = factories.CategoryComponentFactory(
            category=self.category
        )

        self.offering = factories.OfferingFactory(
            category=self.category,
            type=PACKAGE_TYPE,
            state=models.Offering.States.ACTIVE,
        )
        self.offering_component = factories.OfferingComponentFactory(
            offering=self.offering, parent=self.category_component, type='cores'
        )


@freeze_time('2019-01-22')
class StatsTest(StatsBaseTest):
    def setUp(self):
        super(StatsTest, self).setUp()

        self.date = parse_date('2019-01-01')

        self.plan = factories.PlanFactory(offering=self.offering)
        self.plan_component = factories.PlanComponentFactory(
            plan=self.plan, component=self.offering_component, amount=10
        )

        self.resource = factories.ResourceFactory(
            project=self.project, offering=self.offering, plan=self.plan
        )

    def test_reported_usage_is_aggregated_for_project_and_customer(self):
        # Arrange
        plan_period = models.ResourcePlanPeriod.objects.create(
            start=parse_date('2019-01-01'), resource=self.resource, plan=self.plan,
        )

        models.ComponentUsage.objects.create(
            resource=self.resource,
            component=self.offering_component,
            date=parse_date('2019-01-10'),
            billing_period=parse_date('2019-01-01'),
            plan_period=plan_period,
            usage=100,
        )

        self.new_resource = factories.ResourceFactory(
            project=self.project, offering=self.offering, plan=self.plan
        )

        new_plan_period = models.ResourcePlanPeriod.objects.create(
            start=parse_date('2019-01-01'), resource=self.new_resource, plan=self.plan,
        )

        models.ComponentUsage.objects.create(
            resource=self.resource,
            component=self.offering_component,
            date=parse_date('2019-01-20'),
            billing_period=parse_date('2019-01-01'),
            plan_period=new_plan_period,
            usage=200,
        )

        # Act
        tasks.calculate_usage_for_current_month()

        # Assert
        project_usage = (
            models.CategoryComponentUsage.objects.filter(
                scope=self.project, component=self.category_component, date=self.date
            )
            .get()
            .reported_usage
        )
        customer_usage = (
            models.CategoryComponentUsage.objects.filter(
                scope=self.customer, component=self.category_component, date=self.date
            )
            .get()
            .reported_usage
        )

        self.assertEqual(project_usage, 300)
        self.assertEqual(customer_usage, 300)

    def test_fixed_usage_is_aggregated_for_project_and_customer(self):
        # Arrange
        models.ResourcePlanPeriod.objects.create(
            resource=self.resource,
            plan=self.plan,
            start=parse_date('2019-01-10'),
            end=parse_date('2019-01-20'),
        )

        # Act
        tasks.calculate_usage_for_current_month()

        # Assert
        project_usage = (
            models.CategoryComponentUsage.objects.filter(
                scope=self.project, component=self.category_component, date=self.date,
            )
            .get()
            .fixed_usage
        )
        customer_usage = (
            models.CategoryComponentUsage.objects.filter(
                scope=self.customer, component=self.category_component, date=self.date
            )
            .get()
            .fixed_usage
        )

        self.assertEqual(project_usage, self.plan_component.amount)
        self.assertEqual(customer_usage, self.plan_component.amount)

    def test_offering_customers_stats(self):
        url = factories.OfferingFactory.get_url(self.offering, action='customers')
        self.client.force_authenticate(self.fixture.staff)
        result = self.client.get(url)
        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(len(result.data), 1)
        self.assertEqual(
            result.data[0]['uuid'], self.resource.project.customer.uuid.hex
        )


@freeze_time('2020-01-01')
class CostsStatsTest(StatsBaseTest):
    def setUp(self):
        super(CostsStatsTest, self).setUp()
        self.url = factories.OfferingFactory.get_url(self.offering, action='costs')

        self.plan = factories.PlanFactory(
            offering=self.offering, unit=UnitPriceMixin.Units.PER_DAY,
        )
        self.plan_component = factories.PlanComponentFactory(
            plan=self.plan, component=self.offering_component, amount=10
        )

        self.resource = factories.ResourceFactory(
            offering=self.offering,
            state=models.Resource.States.OK,
            plan=self.plan,
            limits={'cores': 1},
        )
        invoices_tasks.create_monthly_invoices()

    def test_offering_costs_stats(self):
        with freeze_time('2020-03-01'):
            self._check_stats()

    def test_period_filter(self):
        self.client.force_authenticate(self.fixture.staff)

        result = self.client.get(self.url, {'other_param': ''})
        self.assertEqual(result.status_code, status.HTTP_200_OK)

        result = self.client.get(self.url, {'start': '2020-01'})
        self.assertEqual(result.status_code, status.HTTP_400_BAD_REQUEST)

    def test_offering_costs_stats_if_resource_has_been_failed(self):
        with freeze_time('2020-03-01'):
            self.resource.state = models.Resource.States.ERRED
            self.resource.save()
            self._check_stats()

    def _check_stats(self):
        self.client.force_authenticate(self.fixture.staff)
        result = self.client.get(self.url, {'start': '2020-01', 'end': '2020-02'})
        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(len(result.data), 2)
        self.assertEqual(
            result.data[0],
            {
                'tax': 0,
                'total': self.plan_component.price * 31,
                'price': self.plan_component.price * 31,
                'price_current': self.plan_component.price * 31,
                'period': '2020-01',
            },
        )

    @helpers.override_marketplace_settings(ANONYMOUS_USER_CAN_VIEW_OFFERINGS=True)
    def test_stat_methods_are_not_available_for_anonymous_users(self):
        offering_url = factories.OfferingFactory.get_url(self.offering)

        result = self.client.get(offering_url)
        self.assertEqual(result.status_code, status.HTTP_200_OK)

        offering_list_url = factories.OfferingFactory.get_list_url()
        result = self.client.get(offering_list_url)
        self.assertEqual(result.status_code, status.HTTP_200_OK)

        result = self.client.get(self.url)
        self.assertEqual(result.status_code, status.HTTP_401_UNAUTHORIZED)

        customers_url = factories.OfferingFactory.get_url(
            self.offering, action='customers'
        )
        result = self.client.get(customers_url)
        self.assertEqual(result.status_code, status.HTTP_401_UNAUTHORIZED)


@freeze_time('2020-03-01')
class ComponentStatsTest(StatsBaseTest):
    def setUp(self):
        super(ComponentStatsTest, self).setUp()
        self.url = factories.OfferingFactory.get_url(
            self.offering, action='component_stats'
        )

        self.plan = factories.PlanFactory(
            offering=self.offering, unit=UnitPriceMixin.Units.PER_DAY,
        )
        self.plan_component = factories.PlanComponentFactory(
            plan=self.plan, component=self.offering_component, amount=10
        )

        self.resource = factories.ResourceFactory(
            offering=self.offering,
            state=models.Resource.States.OK,
            plan=self.plan,
            limits={'cores': 1},
        )

    def _create_items(self):
        invoices_tasks.create_monthly_invoices()
        invoice = invoices_models.Invoice.objects.get(
            year=2020, month=3, customer=self.resource.project.customer
        )
        return invoice.items.filter(object_id=self.resource.id)

    def test_item_details(self):
        component = factories.OfferingComponentFactory(
            offering=self.resource.offering,
            billing_type=models.OfferingComponent.BillingTypes.USAGE,
            type='storage',
        )
        usage = factories.ComponentUsageFactory(
            resource=self.resource,
            billing_period=core_utils.month_start(timezone.now()),
            component=component,
        )
        item = self._create_items().first()
        self.assertEqual(
            item.details,
            {
                'limits': self.resource.limits,
                'usages': {usage.component.type: usage.usage},
                'scope_uuid': item.scope.uuid.hex,
                'resource_name': item.scope.name,
                'resource_uuid': item.scope.uuid.hex,
                'offering_name': self.offering.name,
                'offering_type': PACKAGE_TYPE,
                'offering_uuid': self.offering.uuid.hex,
            },
        )

    def test_component_stats_if_invoice_item_details_includes_limits(self):
        component = factories.OfferingComponentFactory(
            offering=self.resource.offering,
            billing_type=models.OfferingComponent.BillingTypes.USAGE,
            type='storage',
        )
        plan_period = factories.ResourcePlanPeriodFactory(
            resource=self.resource, plan=self.plan,
        )
        usage = factories.ComponentUsageFactory(
            resource=self.resource,
            billing_period=core_utils.month_start(timezone.now()),
            component=component,
            plan_period=plan_period,
        )
        self._create_items()
        self.client.force_authenticate(self.fixture.staff)
        result = self.client.get(self.url, {'start': '2020-03', 'end': '2020-03'})
        component_cores = self.resource.offering.components.get(type='cores')
        component_storage = self.resource.offering.components.get(type='storage')

        self.assertEqual(
            result.data,
            [
                {
                    'description': component_cores.description,
                    'measured_unit': component_cores.measured_unit,
                    'name': component_cores.name,
                    'period': '2020-03',
                    'date': '2020-03-31T00:00:00+00:00',
                    'type': component_cores.type,
                    'usage': float(
                        decimal.Decimal(self.resource.limits['cores'])
                        / decimal.Decimal(
                            self.resource.offering.component_factors.get(
                                component_cores.type, 1
                            )
                        )
                    ),
                },
                {
                    'description': component_storage.description,
                    'measured_unit': component_storage.measured_unit,
                    'name': component_storage.name,
                    'period': '2020-03',
                    'date': '2020-03-31T00:00:00+00:00',
                    'type': component_storage.type,
                    'usage': float(
                        decimal.Decimal(usage.usage)
                        / decimal.Decimal(
                            self.resource.offering.component_factors.get(
                                component_storage.type, 1
                            )
                        )
                    ),
                },
            ],
        )

    def test_component_stats_if_invoice_item_details_includes_plan_component_data(
        self,
    ):
        self.resource.offering.type = PLUGIN_NAME
        self.resource.offering.save()

        self._create_items()
        self.client.force_authenticate(self.fixture.staff)
        result = self.client.get(self.url, {'start': '2020-03', 'end': '2020-03'})
        self.assertEqual(
            result.data,
            [
                {
                    'description': self.offering_component.description,
                    'measured_unit': self.offering_component.measured_unit,
                    'name': self.offering_component.name,
                    'period': '2020-03',
                    'date': '2020-03-31T00:00:00+00:00',
                    'type': self.offering_component.type,
                    'usage': 31,
                }
            ],
        )

    def test_migration(self):
        item = self._create_items().first()
        details = utils.get_offering_details(self.resource.offering)
        details['resource_name'] = self.resource.name
        details['resource_uuid'] = self.resource.uuid.hex
        details['scope_uuid'] = self.resource.uuid.hex
        details['limits'] = self.resource.limits
        details['usages'] = {}
        self.assertEqual(item.details, details)

        migration = __import__(
            'waldur_mastermind.marketplace.migrations.0024_init_invoice_items_details_from_order_item',
            fromlist=['init_invoice_items_details_from_order_item'],
        )
        func = migration.init_invoice_items_details_from_order_item

        class Apps(object):
            @staticmethod
            def get_model(app, klass):
                if klass == 'OrderItem':
                    return models.OrderItem

                if klass == 'ComponentUsage':
                    return models.ComponentUsage

                if klass == 'InvoiceItem':
                    return invoices_models.InvoiceItem

                if klass == 'Resource':
                    return models.Resource

        mock_apps = Apps()
        component = factories.OfferingComponentFactory(
            offering=self.resource.offering,
            billing_type=models.OfferingComponent.BillingTypes.USAGE,
            type='storage',
        )
        usage = factories.ComponentUsageFactory(
            resource=item.scope,
            billing_period=core_utils.month_start(timezone.now()),
            component=component,
        )
        func(mock_apps, None)
        item.refresh_from_db()
        details['usages'] = {usage.component.type: usage.usage}
        self.assertEqual(item.details, details)

    def test_handler(self):
        self.resource.offering.type = PLUGIN_NAME
        self.resource.offering.save()

        # add usage-based component to the offering and plan
        COMPONENT_TYPE = 'storage'
        new_component = factories.OfferingComponentFactory(
            offering=self.resource.offering,
            billing_type=models.OfferingComponent.BillingTypes.USAGE,
            use_limit_for_billing=True,
            type=COMPONENT_TYPE,
        )
        factories.PlanComponentFactory(
            plan=self.plan, component=new_component,
        )

        self._create_items()
        plan_period = factories.ResourcePlanPeriodFactory(
            resource=self.resource,
            plan=self.plan,
            start=core_utils.month_start(timezone.now()),
        )
        usage = factories.ComponentUsageFactory(
            resource=self.resource,
            billing_period=core_utils.month_start(timezone.now()),
            component=new_component,
            plan_period=plan_period,
            usage=2,
        )
        self.client.force_authenticate(self.fixture.staff)
        result = self.client.get(self.url, {'start': '2020-03', 'end': '2020-03'})
        component_cores = self.resource.offering.components.get(type='cores')
        component_storage = self.resource.offering.components.get(type='storage')
        self.assertEqual(
            result.data,
            [
                {
                    'description': component_cores.description,
                    'measured_unit': component_cores.measured_unit,
                    'name': component_cores.name,
                    'period': '2020-03',
                    'date': '2020-03-31T00:00:00+00:00',
                    'type': component_cores.type,
                    'usage': 31,  # days in March of 1 core usage with per-day plan
                },
                {
                    'description': component_storage.description,
                    'measured_unit': component_storage.measured_unit,
                    'name': component_storage.name,
                    'period': '2020-03',
                    'date': '2020-03-31T00:00:00+00:00',
                    'type': component_storage.type,
                    'usage': float(
                        decimal.Decimal(usage.usage)
                        / decimal.Decimal(
                            self.resource.offering.component_factors.get(
                                component_storage.type, 1
                            )
                        )
                    ),
                },
            ],
        )

    def test_migration_0030_offering_data_to_invoice_item_details(self):
        item = self._create_items().first()
        item.details = {}
        item.save()
        details = utils.get_offering_details(self.resource.offering)

        migration = __import__(
            'waldur_mastermind.marketplace.migrations.0030_offering_data_to_invoice_item_details',
            fromlist=['offering_data'],
        )
        func = migration.offering_data

        class Apps(object):
            @staticmethod
            def get_model(app, klass):
                if klass == 'InvoiceItem':
                    return invoices_models.InvoiceItem

                if klass == 'Resource':
                    return models.Resource

        mock_apps = Apps()
        func(mock_apps, None)
        item.refresh_from_db()
        self.assertEqual(item.details, details)
