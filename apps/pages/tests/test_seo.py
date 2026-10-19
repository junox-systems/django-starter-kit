from django.test import TestCase
from django.urls import reverse


class RobotsTxtTests(TestCase):
    def test_serves_plain_text_pointing_at_sitemap(self):
        response = self.client.get("/robots.txt")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/plain")
        self.assertContains(response, "Disallow: /dashboard/")
        self.assertContains(response, "Sitemap: http://testserver/sitemap.xml")


class SitemapTests(TestCase):
    def test_lists_home_page(self):
        response = self.client.get("/sitemap.xml")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f"<loc>http://testserver{reverse('home')}</loc>")
