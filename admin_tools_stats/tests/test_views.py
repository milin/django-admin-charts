#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (C) 2011-2014 Star2Billing S.L.
#
# The Initial Developer of the Original Code is
# Arezqui Belaid <info@star2billing.com>
#
import datetime

import django
from django.test.utils import override_settings
from django.urls import reverse
from model_mommy import mommy

from admin_tools_stats.views import AnalyticsView

from .utils import BaseSuperuserAuthenticatedClient, assertContainsAny


class AnalyticsViewTest(BaseSuperuserAuthenticatedClient):

    def setUp(self):
        self.stats = mommy.make(
            'DashboardStats',
            graph_title="User chart",
            date_field_name="date_joined",
            model_name="User",
            model_app_name="auth",
            graph_key="user_graph",
            allowed_type_operation_field_name=['Sum', 'Count'],
        )
        self.kid_stats = mommy.make(
            'DashboardStats',
            graph_title="Kid chart",
            date_field_name="birthday",
            model_name="TestKid",
            model_app_name="demoproject",
            graph_key="kid_graph",
        )
        super().setUp()

    def test_analytics_view(self):
        """Test function to check dashboardstats admin pages"""
        response = self.client.get(reverse('chart-analytics'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<button>Kid chart</button>", html=True)

    def test_analytics_chart_view(self):
        """Test function to check dashboardstats admin pages"""
        response = self.client.get(reverse('chart-analytics', kwargs={'graph_key': 'user_graph'}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<h3>User chart</h3>", html=True)
        self.assertContains(
            response,
            '<select name="select_box_operation" class="chart-input">'
            '<option value="Count">Count</option>'
            '<option value="Sum">Sum</option>'
            '</select>',
            html=True)

    def test_get_charts_query(self):
        a = AnalyticsView()
        a.request = self.client.request()
        a.request.user = mommy.make("User", is_superuser=True)
        if django.VERSION > (3, 2):
            self.assertQuerysetEqual(a.get_charts_query(), [self.kid_stats, self.stats])
        else:
            self.assertQuerysetEqual(a.get_charts_query(), ['<DashboardStats: kid_graph>', '<DashboardStats: user_graph>'])

    def test_get_charts_query_usser(self):
        a = AnalyticsView()
        kid_graph_user = mommy.make(
            'DashboardStats',
            graph_title="Kid chart",
            date_field_name="birthday",
            model_name="TestKid",
            model_app_name="demoproject",
            graph_key="kid_graph_user",
            show_to_users=True,
        )
        a.request = self.client.request()
        a.request.user = mommy.make("User")
        if django.VERSION > (3, 2):
            self.assertQuerysetEqual(a.get_charts_query(), [kid_graph_user])
        else:
            self.assertQuerysetEqual(a.get_charts_query(), ['<DashboardStats: kid_graph_user>'])

    def test_get_templates_names(self):
        a = AnalyticsView()
        a.request = self.client.request()
        a.request.user = mommy.make("User", is_superuser=True)
        self.assertEqual(a.get_template_names(), 'admin_tools_stats/analytics.html')

    def test_get_templates_names_usser(self):
        a = AnalyticsView()
        a.request = self.client.request()
        a.request.user = mommy.make("User")
        self.assertEqual(a.get_template_names(), 'admin_tools_stats/analytics_user.html')


class MultiFieldViewsTests(BaseSuperuserAuthenticatedClient):
    def setUp(self):
        self.stats = mommy.make(
            'DashboardStats',
            date_field_name="date_joined",
            model_name="User",
            model_app_name="auth",
            graph_key="user_graph",
            operation_field_name='is_active,is_staff',
        )
        super().setUp()

    @override_settings(USE_TZ=True, TIME_ZONE='UTC')
    def test_get_multi_series_multiple_operations(self):
        """Test function view rendering multi series with multiple operations"""
        mommy.make('User', date_joined=datetime.datetime(2010, 10, 10, tzinfo=datetime.timezone.utc))
        url = reverse('chart-data', kwargs={'graph_key': 'user_graph'})
        url += (
            "?time_since=2010-10-08&time_until=2010-10-12&select_box_interval=days&"
            "select_box_chart_type=discreteBarChart&select_box_operation_field="
        )
        response = self.client.get(url)
        assertContainsAny(self, response, ('{"x": 1286668800000, "y": 1}', '{"y": 1, "x": 1286668800000}'))
