"""Photos of a piece — ziman step 5.

The original is not kept. D-A settled that: it stays on her phone, which is
the one place it is already backed up and the one place a theft of this board
cannot reach. Two renditions are built in the browser and sent.

The bug this file exists to have caught early: `ZM-0001` is what she reads on
a phone call, and the path validator refuses upper case — on a
case-insensitive filesystem `ZM-0001` and `zm-0001` are one directory, so
folding would silently merge two pieces. Conversion happens once, in
`piece_slug`, rather than at each call site: a call site that converts is a
call site that can forget to, and this one would have failed on the first
real photo.
"""

from __future__ import annotations

import base64
import json
import os
import unittest

from ofn.adapters.facts import FactStore
from ofn.adapters.http_api import ApiApp, HostMap
from ofn.adapters.ledger import Ledger
from ofn.adapters.media import MediaStore
from ofn.adapters.outbox import Outbox
from ofn.adapters.packloader import load_pack
from ofn.adapters.products import (
    MAX_PHOTOS_PER_PRODUCT, ProductError, ProductStore, piece_slug,
)
from ofn.kernel.auth import issue_session
from ofn.kernel.errors import FailClosedError
from ofn.kernel.photos import relative_path
from ofn.kernel.tenancy import TenantRegistry
from ofn.node import Node
from tests.tmpdir import temp_dir

NOW_S = 1_785_000_000
NOW_ISO = "2026-08-05T09:00:00Z"
SECRET = "s"
WHO = "424242"
HOST = {"host": "z.test"}

IMG = base64.b64encode(b"\xff\xd8\xff" + b"x" * 200).decode()
RENDITIONS = {"1600": "data:image/jpeg;base64," + IMG,
              "320": "data:image/jpeg;base64," + IMG}


class TestTheSkuBecomesAPath(unittest.TestCase):
    def test_a_sku_as_written_is_refused_by_the_path_builder(self):
        """Upper case is refused on purpose, and this is where it would have
        blown up: on the first real photo, not in any test."""
        with self.assertRaises(FailClosedError):
            relative_path("ziman", "ZM-0001", 0, 1600)

    def test_the_slug_is_what_may_be_a_directory(self):
        self.assertEqual(piece_slug("ZM-0001"), "zm-0001")
        self.assertEqual(relative_path("ziman", piece_slug("ZM-0001"), 0, 1600),
                         "ziman/zm-0001/0-1600.jpg")

    def test_two_pieces_do_not_fold_into_one(self):
        self.assertNotEqual(piece_slug("ZM-0001"), piece_slug("ZM-0010"))

    def test_it_survives_whitespace(self):
        self.assertEqual(piece_slug("  ZM-0002 "), "zm-0002")


class Base(unittest.TestCase):
    def setUp(self):
        d = temp_dir(self)
        pack = load_pack("packs/ziman.yaml")
        registry = TenantRegistry({"ziman": pack})
        self.ledger = Ledger(os.path.join(d, "l.sqlite"))
        self.store = ProductStore(
            os.path.join(d, "p.sqlite"), cost_fields=pack.cost_fields,
            labour_hours_field=pack.labour_hours_field,
            labour_rate_field=pack.labour_rate_field)
        self.media = MediaStore(os.path.join(d, "media"))
        for s in (self.ledger, self.store):
            self.addCleanup(s.close)

        self.node = Node(
            registry=registry, quota=None, ledger=self.ledger,
            facts=FactStore(os.path.join(d, "f.sqlite")),
            outbox=Outbox(os.path.join(d, "o.sqlite")),
            now_epoch_s=lambda: NOW_S, now_iso=lambda: NOW_ISO,
            products=self.store, media=self.media)
        self.app = ApiApp(
            registry, HostMap(tenants={"z.test": "ziman"}, owner_host="p.test"),
            bot_tokens={"ziman": "t"}, session_secret=SECRET,
            partner_user_ids={"ziman": [WHO]}, now=lambda: NOW_S,
            products_for=self.node.products_for,
            create_product=self.node.create_product,
            update_product=self.node.update_product,
            attach_photo=self.node.attach_product_photo)
        self.session = issue_session("ziman", WHO, SECRET, now_epoch_s=NOW_S)

    def call(self, method, path, body=None):
        headers = dict(HOST, authorization="Bearer " + self.session)
        return self.app.handle(method, path, headers,
                               json.dumps(body or {}).encode())

    def piece(self):
        r = self.call("POST", "/api/v1/products",
                      {"name": "گوشواره", "materials_cost_aud": 10})
        return r.body["product"]["sku"]

    def shoot(self, sku, position=0, renditions=None):
        return self.call("POST", f"/api/v1/products/{sku}/photos",
                         {"position": position,
                          "renditions": renditions or RENDITIONS})


class TestUploading(Base):
    def test_both_renditions_land_under_the_lowercased_sku(self):
        sku = self.piece()
        self.assertEqual(self.shoot(sku).status, 200)
        for edge in (1600, 320):
            self.assertTrue(self.media.exists(
                relative_path("ziman", piece_slug(sku), 0, edge)))

    def test_no_original_is_written(self):
        """D-A: it stays on her phone."""
        self.shoot(self.piece())
        names = [f for _, _, fs in os.walk(self.media.root) for f in fs]
        self.assertTrue(all("original" not in n for n in names), names)

    def test_the_piece_records_which_slots_are_filled(self):
        sku = self.piece()
        self.shoot(sku, position=0)
        self.shoot(sku, position=1)
        self.assertEqual(self.store.media_of("ziman", sku), [0, 1])

    def test_the_row_comes_back_with_its_photo_count(self):
        """Sent with the row rather than fetched separately, so the shell
        cannot render a piece whose photo count belongs to a different one."""
        sku = self.piece()
        self.shoot(sku)
        row = [p for p in self.call("GET", "/api/v1/products").body["products"]
               if p["sku"] == sku][0]
        self.assertEqual(row["photos"], [0])

    def test_replacing_a_slot_does_not_duplicate_it(self):
        sku = self.piece()
        self.shoot(sku, position=0)
        self.shoot(sku, position=0)
        self.assertEqual(self.store.media_of("ziman", sku), [0])

    def test_it_is_written_down(self):
        sku = self.piece()
        self.shoot(sku)
        self.assertIn("PRODUCT_PHOTO",
                      [e.kind for e in self.ledger.read(self.node.registry.scope(
                          self.node.registry.pack("ziman").tenant))])


class TestRefusals(Base):
    def test_a_photo_for_a_piece_that_does_not_exist(self):
        """A media row pointing at nothing is a file nothing will ever clean
        up — and for a photo of somebody's work, one nobody knows they still
        have."""
        self.assertEqual(self.shoot("ZM-9999").status, 400)
        self.assertEqual([f for _, _, fs in os.walk(self.media.root)
                          for f in fs], [])

    def test_a_missing_rendition_is_refused(self):
        sku = self.piece()
        r = self.shoot(sku, renditions={"1600": RENDITIONS["1600"]})
        self.assertEqual(r.status, 400)

    def test_an_svg_is_refused(self):
        sku = self.piece()
        r = self.shoot(sku, renditions={
            "1600": "data:image/svg+xml;base64," + IMG, "320": IMG})
        self.assertEqual(r.status, 400)

    def test_too_many_photos_is_refused(self):
        sku = self.piece()
        with self.assertRaises(ProductError):
            self.store.attach_media("ziman", sku, MAX_PHOTOS_PER_PRODUCT,
                                    mime="image/jpeg", byte_size=1,
                                    now_iso=NOW_ISO)

    def test_a_bool_is_not_a_position(self):
        sku = self.piece()
        with self.assertRaises(ProductError):
            self.store.attach_media("ziman", sku, True, mime="image/jpeg",
                                    byte_size=1, now_iso=NOW_ISO)

    def test_a_failed_upload_leaves_the_piece_alone(self):
        """Recording is one step so that an upload cannot take the piece with
        it — D-B."""
        sku = self.piece()
        self.shoot(sku, renditions={"1600": "not-base64!!", "320": IMG})
        self.assertIsNotNone(self.store.get("ziman", sku))

    def test_no_session_no_photo(self):
        sku = self.piece()
        r = self.app.handle("POST", f"/api/v1/products/{sku}/photos",
                            dict(HOST), b"{}")
        self.assertEqual(r.status, 401)

    def test_a_crafted_sku_cannot_reach_another_route(self):
        for bad in ("a/b/photos", "/photos"):
            self.assertEqual(
                self.call("POST", f"/api/v1/products/{bad}").status, 404, bad)


if __name__ == "__main__":
    unittest.main()
