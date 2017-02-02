import datetime

from decimal import Decimal

import pytz
from django.db.models.signals import pre_delete
from django.test import TestCase
from django.utils import timezone
from freezegun import freeze_time
from mock import Mock

from nodeconductor.core import utils as core_utils
from nodeconductor_assembly_waldur.packages import models as package_models
from nodeconductor_assembly_waldur.packages.tests import factories as packages_factories
from nodeconductor_assembly_waldur.support.tests import fixtures as support_fixtures

from .. import factories, fixtures
from ... import models, utils


class UpdateInvoiceOnOpenstackPackageDeletionTest(TestCase):

    def setUp(self):
        self.fixture = fixtures.InvoiceFixture()

    def test_invoice_item_name_is_saved_on_package_deletion(self):
        package = self.fixture.openstack_package

        package.delete()

        invoice = models.Invoice.objects.get(customer=package.tenant.service_project_link.project.customer)
        expected_name = '%s (%s)' % (package.tenant.name, package.template.name)
        item = invoice.openstack_items.first()
        self.assertEqual(item.name, expected_name)

    def test_invoice_price_changes_on_package_deletion(self):
        start = datetime.datetime(year=2016, month=11, day=4, hour=12, minute=0, second=0)
        end = datetime.datetime(year=2016, month=11, day=25, hour=18, minute=0, second=0)

        with freeze_time(start):
            package = self.fixture.openstack_package

        with freeze_time(end):
            package.delete()

            invoice = models.Invoice.objects.get(customer=package.tenant.service_project_link.project.customer)
            days = (end - start).days + 1
            expected_total = days * package.template.price
            self.assertEqual(invoice.total, expected_total)

    def test_invoice_update_handler_is_called_once_on_tenant_deletion(self):
        mocked_handler = Mock()
        pre_delete.connect(mocked_handler, sender=package_models.OpenStackPackage, dispatch_uid='test_handler')

        package = self.fixture.openstack_package
        package.tenant.delete()
        self.assertEqual(mocked_handler.call_count, 1)


class AddNewOpenstackPackageDetailsToInvoiceTest(TestCase):

    def create_package_template(self, component_price=10, component_amount=1):
        template = packages_factories.PackageTemplateFactory()
        template.components.update(
            price=component_price,
            amount=component_amount,
        )
        return template

    def create_package(self, component_price, tenant=None):
        template = self.create_package_template(component_price=component_price)
        if not tenant:
            tenant = packages_factories.TenantFactory()

        package = packages_factories.OpenStackPackageFactory(template=template, tenant=tenant)
        return package

    def setUp(self):
        self.fixture = fixtures.InvoiceFixture()

    def test_existing_invoice_is_updated_on_openstack_package_creation(self):
        self.fixture.customer = self.fixture.invoice.customer
        package = self.fixture.openstack_package
        self.assertTrue(self.fixture.invoice.openstack_items.filter(package=package).exists())

    def test_new_invoice_is_created_on_openstack_package_creation(self):
        package = self.fixture.openstack_package
        invoice = models.Invoice.objects.get(customer=package.tenant.service_project_link.project.customer)
        self.assertTrue(invoice.openstack_items.filter(package=package).exists())

    def test_invoice_price_is_calculated_on_package_creation(self):
        with freeze_time('2016-11-04 12:00:00'):
            package = self.fixture.openstack_package

            days = (utils.get_current_month_end() - timezone.now()).days + 1
            expected_total = days * package.template.price

        with freeze_time(utils.get_current_month_end()):
            invoice = models.Invoice.objects.get(customer=package.tenant.service_project_link.project.customer)
            self.assertEqual(invoice.total, expected_total)

    def test_default_tax_percent_is_used_on_invoice_creation(self):
        payment_details = factories.PaymentDetailsFactory(default_tax_percent=20)
        invoice = factories.InvoiceFactory(customer=payment_details.customer)
        self.assertEqual(invoice.tax_percent, payment_details.default_tax_percent)

    def test_package_creation_does_not_increase_price_from_old_package_if_it_is_cheaper(self):
        old_component_price = 100
        new_component_price = old_component_price + 50
        start_date = timezone.datetime(2014, 2, 14, tzinfo=pytz.UTC)
        package_change_date = timezone.datetime(2014, 2, 20, tzinfo=pytz.UTC)
        end_of_the_month = core_utils.month_end(package_change_date)

        with freeze_time(start_date):
            old_package = self.create_package(component_price=old_component_price)
        customer = old_package.tenant.service_project_link.project.customer

        with freeze_time(package_change_date):
            old_package.delete()
            new_template = self.create_package_template(component_price=new_component_price)
            new_package = packages_factories.OpenStackPackageFactory(
                template=new_template,
                tenant__service_project_link__project__customer=customer,
            )

        old_components_price = old_package.template.price * ((package_change_date - start_date).days - 1)
        second_component_usage_days = utils.get_full_days(package_change_date, end_of_the_month)
        new_components_price = new_package.template.price * second_component_usage_days
        expected_price = old_components_price + new_components_price

        self.assertEqual(models.Invoice.objects.count(), 1)
        self.assertEqual(Decimal(expected_price), models.Invoice.objects.first().price)

    def test_package_creation_increases_price_from_old_package_if_it_is_more_expensive(self):
        old_component_price = 20
        new_component_price = old_component_price - 10
        start_date = timezone.datetime(2014, 2, 14, tzinfo=pytz.UTC)
        package_change_date = timezone.datetime(2014, 2, 20, tzinfo=pytz.UTC)
        end_of_the_month = core_utils.month_end(package_change_date)

        with freeze_time(start_date):
            old_package = self.create_package(component_price=old_component_price)
        customer = old_package.tenant.service_project_link.project.customer
        tenant = old_package.tenant

        with freeze_time(package_change_date):
            old_package.delete()
            new_template = self.create_package_template(component_price=new_component_price)
            new_package = packages_factories.OpenStackPackageFactory(
                template=new_template,
                tenant=tenant,
            )

        old_components_price = old_package.template.price * (package_change_date - start_date).days
        second_component_usage_days = utils.get_full_days(package_change_date, end_of_the_month) - 1
        new_components_price = new_package.template.price * second_component_usage_days
        expected_price = old_components_price + new_components_price

        # assert
        self.assertEqual(models.Invoice.objects.count(), 1)
        self.assertEqual(Decimal(expected_price), models.Invoice.objects.first().price)

    def test_package_creation_does_not_increase_price_from_old_package_if_it_is_cheaper_in_the_end_of_the_month(self):
        old_component_price = 10
        new_component_price = old_component_price + 5
        start_date = timezone.datetime(2014, 2, 20, tzinfo=pytz.UTC)
        package_change_date = timezone.datetime(2014, 2, 28, tzinfo=pytz.UTC)
        end_of_the_month = core_utils.month_end(package_change_date)

        with freeze_time(start_date):
            old_package = self.create_package(component_price=old_component_price)
        customer = old_package.tenant.service_project_link.project.customer
        tenant = old_package.tenant

        with freeze_time(package_change_date):
            old_package.delete()
            new_template = self.create_package_template(component_price=new_component_price)
            new_package = packages_factories.OpenStackPackageFactory(
                template=new_template,
                tenant=tenant
            )

        old_components_price = old_package.template.price * ((package_change_date - start_date).days - 1)
        second_component_usage_days = utils.get_full_days(package_change_date, end_of_the_month)
        new_components_price = new_package.template.price * second_component_usage_days
        expected_price = old_components_price + new_components_price

        # assert
        self.assertEqual(models.Invoice.objects.count(), 1)
        self.assertEqual(Decimal(expected_price), models.Invoice.objects.first().price)

    def test_package_creation_increases_price_from_old_package_if_it_is_more_expensive_in_the_end_of_the_month(self):
        old_component_price = 15
        new_component_price = old_component_price - 5
        start_date = timezone.datetime(2014, 2, 20, tzinfo=pytz.UTC)
        package_change_date = timezone.datetime(2014, 2, 28, tzinfo=pytz.UTC)
        end_of_the_month = core_utils.month_end(package_change_date)

        with freeze_time(start_date):
            old_package = self.create_package(component_price=old_component_price)
        customer = old_package.tenant.service_project_link.project.customer
        tenant = old_package.tenant

        with freeze_time(package_change_date):
            old_package.delete()
            new_template = self.create_package_template(component_price=new_component_price)
            new_package = packages_factories.OpenStackPackageFactory(
                template=new_template,
                tenant=tenant,
            )

        old_components_price = old_package.template.price * ((package_change_date - start_date).days + 1)
        second_component_usage_days = utils.get_full_days(package_change_date, end_of_the_month) - 1
        new_components_price = new_package.template.price * second_component_usage_days
        expected_price = old_components_price + new_components_price

        # assert
        self.assertEqual(models.Invoice.objects.count(), 1)
        self.assertEqual(Decimal(expected_price), models.Invoice.objects.first().price)

    def test_package_creation_does_not_increase_price_for_cheaper_1_day_long_old_package_in_the_end_of_the_month(self):
        old_component_price = 5
        new_component_price = old_component_price + 5
        start_date = timezone.datetime(2014, 2, 27, tzinfo=pytz.UTC)
        package_change_date = timezone.datetime(2014, 2, 28, tzinfo=pytz.UTC)
        end_of_the_month = core_utils.month_end(package_change_date)

        with freeze_time(start_date):
            old_package = self.create_package(component_price=old_component_price)
        tenant = old_package.tenant

        with freeze_time(package_change_date):
            old_package.delete()
            new_template = self.create_package_template(component_price=new_component_price)
            new_package = packages_factories.OpenStackPackageFactory(
                template=new_template,
                tenant=tenant,
            )

        old_components_price = old_package.template.price * ((package_change_date - start_date).days - 1)
        second_component_usage_days = utils.get_full_days(package_change_date, end_of_the_month)
        new_components_price = new_package.template.price * second_component_usage_days
        expected_price = old_components_price + new_components_price

        # assert
        self.assertEqual(models.Invoice.objects.count(), 1)
        self.assertEqual(Decimal(expected_price), models.Invoice.objects.first().price)

    def test_package_creation_does_not_increase_price_for_cheaper_1_day_long_old_package_in_the_same_day(self):
        old_component_price = 10
        new_component_price = old_component_price + 5
        start_date = timezone.datetime(2014, 2, 26, tzinfo=pytz.UTC)
        package_change_date = start_date
        end_of_the_month = core_utils.month_end(package_change_date)

        with freeze_time(start_date):
            old_package = self.create_package(component_price=old_component_price)
        customer = old_package.tenant.service_project_link.project.customer

        with freeze_time(package_change_date):
            old_package.delete()
            new_template = self.create_package_template(component_price=new_component_price)
            new_package = packages_factories.OpenStackPackageFactory(
                template=new_template,
                tenant__service_project_link__project__customer=customer,
            )

        old_components_price = old_package.template.price * (package_change_date - start_date).days
        second_component_usage_days = utils.get_full_days(package_change_date, end_of_the_month)
        new_components_price = new_package.template.price * second_component_usage_days
        expected_price = old_components_price + new_components_price

        # assert
        self.assertEqual(models.Invoice.objects.count(), 1)
        self.assertEqual(Decimal(expected_price), models.Invoice.objects.first().price)


class AddNewOfferingDetailsToInvoiceTest(TestCase):

    def setUp(self):
        self.fixture = support_fixtures.SupportFixture()

    def test_invoice_is_created_on_offering_creation(self):
        offering = self.fixture.offering
        offering.state = offering.States.OK
        offering.save()
        self.assertEqual(models.Invoice.objects.count(), 1)
        invoice = models.Invoice.objects.first()
        self.assertTrue(invoice.offering_items.filter(offering=offering).exists())

    def test_existing_invoice_is_updated_on_offering_creation(self):
        start_date = timezone.datetime(2014, 2, 27, tzinfo=pytz.UTC)
        end_date = core_utils.month_end(start_date)
        usage_days = utils.get_full_days(start_date, end_date)

        with freeze_time(start_date):
            invoice = factories.InvoiceFactory(customer=self.fixture.customer)
            offering = self.fixture.offering
            offering.state = offering.States.OK
            offering.save()

        self.assertEqual(models.Invoice.objects.count(), 1)
        self.assertTrue(invoice.offering_items.filter(offering=offering).exists())
        expected_price = offering.price * usage_days
        self.assertEqual(invoice.price, Decimal(expected_price))

    def test_existing_invoice_is_update_on_offering_creation_if_it_has_package_item_for_same_customer(self):
        start_date = timezone.datetime(2014, 2, 27, tzinfo=pytz.UTC)
        end_date = core_utils.month_end(start_date)
        usage_days = utils.get_full_days(start_date, end_date)

        with freeze_time(start_date):
            packages_factories.OpenStackPackageFactory(
                tenant__service_project_link__project__customer=self.fixture.customer)
            self.assertEqual(models.Invoice.objects.count(), 1)
            invoice = models.Invoice.objects.first()
            components_price = invoice.price
            offering = self.fixture.offering
            offering.state = offering.States.OK
            offering.save()
            self.assertEqual(models.Invoice.objects.count(), 1)

        self.assertTrue(invoice.offering_items.filter(offering=offering).exists())
        expected_price = offering.price * usage_days + components_price
        self.assertEqual(invoice.price, Decimal(expected_price))


class UpdateInvoiceOnOfferingDeletionTest(TestCase):

    def setUp(self):
        self.fixture = support_fixtures.SupportFixture()

    def test_invoice_price_is_not_changed_after_a_while_if_offering_is_deleted(self):
        start_date = timezone.datetime(2014, 2, 27, tzinfo=pytz.UTC)
        end_date = core_utils.month_end(start_date)
        usage_days = utils.get_full_days(start_date, end_date)

        with freeze_time(start_date):
            offering = self.fixture.offering
            offering.state = offering.States.OK
            offering.save()
            self.assertEqual(models.Invoice.objects.count(), 1)
            invoice = models.Invoice.objects.first()
        with freeze_time(end_date):
            offering.delete()

        expected_price = offering.price * usage_days
        self.assertEqual(invoice.price, Decimal(expected_price))

    def test_invoice_is_created_in_new_month_when_single_item_is_terminated(self):
        start_date = timezone.datetime(2014, 2, 27, tzinfo=pytz.UTC)
        next_month = timezone.datetime(2014, 3, 2, tzinfo=pytz.UTC)

        with freeze_time(start_date):
            offering = self.fixture.offering
            offering.state = offering.States.OK
            offering.save()
            self.assertEqual(models.Invoice.objects.count(), 1)
            invoice = models.Invoice.objects.first()
            packages_factories.OpenStackPackageFactory(tenant__service_project_link__project__customer=offering.project.customer)
            self.assertEqual(models.Invoice.objects.count(), 1)
            self.assertEqual(invoice.openstack_items.count(), 1)
            self.assertEqual(invoice.offering_items.count(), 1)

        with freeze_time(next_month):
            offering.delete()
            self.assertEqual(models.Invoice.objects.count(), 2, "New invoice has to be created in new month.")
            new_invoice = models.Invoice.objects.exclude(pk=invoice.pk).first()
            self.assertEqual(new_invoice.openstack_items.count(), 1)
            self.assertEqual(new_invoice.offering_items.count(), 1)
            self.assertEqual(new_invoice.offering_items.first().end, next_month)
