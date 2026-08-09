"""The product surface a partner actually touches.

Two things are being pinned here beyond "the endpoint works":

  * every edit leaves a trail in the hash-chained ledger, with only the
    fields that moved, and
  * a number typed on a Persian keyboard is a number.

The second one sounds cosmetic. It is not: a form that refuses ۱۲۵ blames the
partner for using her own language, and she is the one who has to keep using
it every day.
"""

import json
import os
import unittest

from ofn.adapters.facts import FactStore
from ofn.adapters.http_api import ApiApp, HostMap
from ofn.adapters.ledger import Ledger
from ofn.adapters.outbox import Outbox
from ofn.adapters.packloader import load_pack
from ofn.adapters.products import ProductStore
from ofn.kernel.auth import issue_session
from ofn.kernel.tenancy import TenantRegistry
from ofn.node import Node
from tests.tmpdir import temp_dir

NOW_S = 1_785_000_000
NOW_ISO = "2026-08-04T09:00:00Z"
SECRET = "s"
MALIHEH = "424242"
HOST = {"host": "z.test"}

# $77.50 + $3 = $80.50. No labour term — the two time questions were removed
# — so the total is assembled from what was bought.
PIECE = {"name": "گوشوارهٔ نقره", "materials_cost_aud": 77.5,
         "packaging_cost_aud": 3.0, "price_primary_aud": 120.0}


class Base(unittest.TestCase):
    def setUp(self):
        d = temp_dir(self)
        pack = load_pack("packs/ziman.yaml")
        self.pack = pack
        registry = TenantRegistry({"ziman": pack})
        self.ledger = Ledger(os.path.join(d, "l.sqlite"))
        store = ProductStore(
            os.path.join(d, "p.sqlite"),
            cost_fields=pack.cost_fields,
            labour_hours_field=pack.labour_hours_field,
            labour_rate_field=pack.labour_rate_field)
        self.node = Node(
            registry=registry, quota=None, ledger=self.ledger,
            facts=FactStore(os.path.join(d, "f.sqlite")),
            outbox=Outbox(os.path.join(d, "o.sqlite")),
            now_epoch_s=lambda: NOW_S, now_iso=lambda: NOW_ISO,
            products=store)
        self.addCleanup(store.close)
        self.app = ApiApp(
            registry, HostMap(tenants={"z.test": "ziman"}, owner_host="p.test"),
            bot_tokens={"ziman": "t", "__owner__": "t"},
            session_secret=SECRET, owner_user_ids=("7",),
            partner_user_ids={"ziman": [MALIHEH]}, now=lambda: NOW_S,
            products_for=self.node.products_for,
            create_product=self.node.create_product,
            update_product=self.node.update_product)
        self.session = issue_session("ziman", MALIHEH, SECRET,
                                     now_epoch_s=NOW_S)

    def call(self, method, path, body=None):
        headers = dict(HOST, authorization="Bearer " + self.session)
        return self.app.handle(method, path, headers,
                               json.dumps(body or {}).encode())

    def add(self, **over):
        f = dict(PIECE)
        f.update(over)
        return self.call("POST", "/api/v1/products", f)

    def events(self):
        scope = self.node.registry.scope(self.node.registry.pack("ziman").tenant)
        return list(self.ledger.read(scope))


class TestCreate(Base):
    def test_a_piece_is_created_with_a_code_and_a_cost(self):
        r = self.add()
        self.assertEqual(r.status, 200)
        p = r.body["product"]
        self.assertEqual(p["sku"], "ZM-0001")
        self.assertAlmostEqual(p["cogs_aud"], 80.5)
        self.assertAlmostEqual(p["gross_margin_aud"], 39.5)
        self.assertEqual(p["state"], "in_progress")

    def test_the_list_comes_back_with_the_currency(self):
        self.add()
        body = self.call("GET", "/api/v1/products").body
        self.assertEqual(body["currency"], "AUD")
        self.assertEqual(body["symbol"], "$")
        self.assertEqual(len(body["products"]), 1)

    def test_a_nameless_piece_is_refused_with_a_readable_reason(self):
        r = self.add(name="  ")
        self.assertEqual(r.status, 400)
        self.assertFalse(r.body["ok"])
        self.assertIn("نام", r.body["error"])

    def test_creation_is_written_to_the_ledger(self):
        self.add()
        kinds = [e.kind for e in self.events()]
        self.assertIn("PRODUCT_CREATED", kinds)


class TestPersianNumerals(Base):
    def test_persian_digits_are_a_number(self):
        r = self.add(materials_cost_aud="۷۷.۵", packaging_cost_aud="۳",
                     price_primary_aud="۱۲۰")
        self.assertEqual(r.status, 200)
        self.assertAlmostEqual(r.body["product"]["cogs_aud"], 80.5)
        self.assertAlmostEqual(r.body["product"]["price_primary_aud"], 120.0)

    def test_arabic_indic_digits_too(self):
        r = self.add(materials_cost_aud="٤٠")
        self.assertEqual(r.status, 200)
        self.assertAlmostEqual(r.body["product"]["materials_cost_aud"], 40.0)

    def test_a_thousands_separator_is_not_a_decimal_point(self):
        r = self.add(price_primary_aud="1,200")
        self.assertAlmostEqual(r.body["product"]["price_primary_aud"], 1200.0)

    def test_an_empty_price_stays_unpriced(self):
        r = self.add(price_primary_aud="")
        self.assertIsNone(r.body["product"]["price_primary_aud"])
        self.assertFalse(r.body["product"]["loses_money"])

    def test_a_name_with_digits_is_left_alone(self):
        r = self.add(name="سری ۲")
        self.assertEqual(r.body["product"]["name"], "سری ۲")

    def test_words_where_a_number_belongs_are_still_refused(self):
        r = self.add(price_primary_aud="خیلی")
        self.assertEqual(r.status, 400)


class TestUpdateAndLedger(Base):
    def test_an_edit_records_only_what_moved(self):
        self.add()
        r = self.call("POST", "/api/v1/products/ZM-0001", {"price_primary_aud": 150.0})
        self.assertEqual(r.status, 200)
        self.assertAlmostEqual(r.body["product"]["price_primary_aud"], 150.0)

        entry = [e for e in self.events() if e.kind == "PRODUCT_UPDATED"][-1]
        changed = entry.payload["changed"]
        self.assertIn("price_primary_aud", changed)
        self.assertEqual(changed["price_primary_aud"]["before"], 120.0)
        self.assertEqual(changed["price_primary_aud"]["after"], 150.0)
        # The other seventeen fields did not move and must not be restated.
        self.assertNotIn("name", changed)
        self.assertNotIn("cogs_aud", changed)

    def test_editing_an_input_moves_the_cost_and_says_so(self):
        self.add()
        self.call("POST", "/api/v1/products/ZM-0001",
                  {"materials_cost_aud": 102.5})
        changed = [e for e in self.events()
                   if e.kind == "PRODUCT_UPDATED"][-1].payload["changed"]
        self.assertIn("cogs_aud", changed)
        self.assertAlmostEqual(changed["cogs_aud"]["after"], 105.5)

    def test_a_removed_time_field_is_refused_rather_than_ignored(self):
        """The columns still exist in the file. If the API quietly accepted
        them, the only way to set a piece's labour would be a hand-written
        request — reachable by anyone with a session, reachable by nobody
        using the app."""
        self.add()
        r = self.call("POST", "/api/v1/products/ZM-0001", {"labour_hours": 2.5})
        self.assertEqual(r.status, 400)

    def test_the_ledger_chain_still_verifies_after_edits(self):
        self.add()
        self.call("POST", "/api/v1/products/ZM-0001", {"price_primary_aud": 150.0})
        scope = self.node.registry.scope(self.pack.tenant)
        self.assertTrue(self.ledger.verify(scope))

    def test_the_actor_is_recorded(self):
        self.add()
        entry = [e for e in self.events() if e.kind == "PRODUCT_CREATED"][-1]
        self.assertEqual(entry.payload["actor"], f"partner:{MALIHEH}")

    def test_editing_a_missing_piece_is_a_clear_400(self):
        r = self.call("POST", "/api/v1/products/ZM-9999", {"price_primary_aud": 10.0})
        self.assertEqual(r.status, 400)
        self.assertIn("ZM-9999", r.body["error"])

    def test_selling_needs_a_channel(self):
        self.add()
        r = self.call("POST", "/api/v1/products/ZM-0001", {"state": "sold"})
        self.assertEqual(r.status, 400)
        self.assertIn("کانال", r.body["error"])

    def test_a_sale_on_an_unpriced_channel_reports_blocked_not_zero(self):
        self.add()
        r = self.call("POST", "/api/v1/products/ZM-0001",
                      {"state": "sold", "channel": "etsy"})
        self.assertEqual(r.status, 200)
        p = r.body["product"]
        self.assertIsNone(p["net_margin_aud"])
        self.assertIn("etsy", p["net_margin_blocked"])


class TestTheDoorStillHolds(Base):
    def test_no_session_no_products(self):
        for method, path in (("GET", "/api/v1/products"),
                             ("POST", "/api/v1/products")):
            r = self.app.handle(method, path, dict(HOST), b"{}")
            self.assertEqual(r.status, 401)

    def test_a_delisted_partner_cannot_reach_products(self):
        app = ApiApp(
            self.node.registry,
            HostMap(tenants={"z.test": "ziman"}, owner_host="p.test"),
            bot_tokens={"ziman": "t", "__owner__": "t"},
            session_secret=SECRET, partner_user_ids={"ziman": []},
            now=lambda: NOW_S, products_for=self.node.products_for)
        r = app.handle("GET", "/api/v1/products",
                       dict(HOST, authorization="Bearer " + self.session), b"")
        self.assertEqual(r.status, 401)

    def test_a_crafted_sku_does_not_invent_a_route(self):
        for sku in ("", "ZM-0001/extra", "../../etc"):
            r = self.call("POST", f"/api/v1/products/{sku}", {"price_primary_aud": 1.0})
            self.assertIn(r.status, (400, 404))

    def test_a_body_that_is_not_an_object_is_refused(self):
        headers = dict(HOST, authorization="Bearer " + self.session)
        r = self.app.handle("POST", "/api/v1/products", headers, b"[1,2,3]")
        self.assertEqual(r.status, 400)


if __name__ == "__main__":
    unittest.main()


class TestDeletionIsRecorded(Base):
    """Deleting is not reachable over HTTP — no shell has a delete button and
    a mistap there costs work that cannot be re-derived. It is an operator
    action on the node, and the ledger is what makes it survivable."""

    def scope(self):
        return self.node.registry.scope(
            self.node.registry.pack("ziman").tenant)

    def test_it_is_not_an_http_route(self):
        self.add()
        for method in ("DELETE", "POST"):
            r = self.call(method, "/api/v1/products/ZM-0001/delete")
            self.assertNotEqual(r.status, 200)
        self.assertIsNotNone(self.node.products.get("ziman", "ZM-0001"))

    def test_the_ledger_gains_an_entry_naming_the_piece(self):
        self.add()
        out = self.node.delete_product(self.scope(), "operator:ari", "ZM-0001",
                                       reason="اعداد تست بودند")
        self.assertTrue(out["ok"])
        # `read` is newest-first — it feeds a screen, not a replay.
        last = self.events()[0]
        self.assertEqual(last.kind, "PRODUCT_DELETED")
        self.assertEqual(last.payload["sku"], "ZM-0001")
        self.assertEqual(last.payload["reason"], "اعداد تست بودند")

    def test_the_entry_carries_the_whole_row_not_a_reference_to_it(self):
        """"ZM-0001 was deleted" says something used to exist. The row is
        what lets somebody put it back."""
        self.add()
        self.node.delete_product(self.scope(), "operator:ari", "ZM-0001",
                                 reason="تست")
        removed = self.events()[0].payload["removed"]
        self.assertEqual(removed["name"], PIECE["name"])
        self.assertAlmostEqual(removed["materials_cost_aud"],
                               PIECE["materials_cost_aud"])
        self.assertAlmostEqual(removed["cogs_aud"], 80.5)

    def test_the_creation_entry_is_left_alone(self):
        """History is not edited. The piece was created; that stays true."""
        self.add()
        self.node.delete_product(self.scope(), "operator:ari", "ZM-0001",
                                 reason="تست")
        kinds = [e.kind for e in reversed(self.events())]
        self.assertEqual(kinds, ["PRODUCT_CREATED", "PRODUCT_DELETED"])

    def test_the_chain_still_verifies(self):
        self.add()
        self.node.delete_product(self.scope(), "operator:ari", "ZM-0001",
                                 reason="تست")
        ok, _ = self.ledger.verify(self.scope())
        self.assertTrue(ok)

    def test_deleting_something_absent_fails_without_touching_the_ledger(self):
        self.add()
        before = len(self.events())
        out = self.node.delete_product(self.scope(), "operator:ari", "ZM-9999",
                                       reason="تست")
        self.assertFalse(out["ok"])
        self.assertEqual(len(self.events()), before)

    def test_the_next_piece_does_not_inherit_the_code(self):
        self.add()
        self.node.delete_product(self.scope(), "operator:ari", "ZM-0001",
                                 reason="تست")
        self.assertEqual(self.add().body["product"]["sku"], "ZM-0002")
