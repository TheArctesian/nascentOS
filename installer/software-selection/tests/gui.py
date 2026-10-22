"""Actual Qt widget checks. Run with the packaged Python, or local PySide6.

QT_QPA_PLATFORM=offscreen python tests/gui.py /path/to/evaluated/manifest.json
"""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QEvent, Qt
from PySide6.QtWidgets import QApplication
from nascent_software_model import defaults, load_manifest
from nascent_optional_profiles import gaming_defaults
from picker import Picker, STYLE

MANIFEST = load_manifest(Path(sys.argv.pop(1)))
APPLICATION = QApplication([])
APPLICATION.setStyleSheet(STYLE)


class PickerTests(unittest.TestCase):
    def setUp(self):
        self.picker = Picker(MANIFEST)

    def tearDown(self):
        self.picker.deleteLater()
        APPLICATION.sendPostedEvents(None, QEvent.Type.DeferredDelete)

    def test_defaults_then_toggle_then_reset(self):
        self.assertEqual(self.picker.selected, set(defaults(MANIFEST)))
        self.picker.tiles["neovim"].click()
        self.assertNotIn("neovim", self.picker.result_value()["selected"])
        self.picker.reset()
        self.assertIn("neovim", self.picker.result_value()["selected"])

    def test_search_crosses_categories(self):
        self.picker.search.setText("Blender")
        self.assertEqual(set(self.picker.tiles), {"blender"})
        self.picker.tiles["blender"].click()
        self.assertIn("blender", self.picker.result_value()["selected"])

    def test_proprietary_cancel_does_not_select(self):
        self.picker.search.setText("Cursor")
        with patch.object(self.picker, "confirm_proprietary", return_value=False):
            self.picker.tiles["cursor"].click()
        self.assertNotIn("cursor", self.picker.selected)
        self.assertFalse(self.picker.tiles["cursor"].isChecked())

    def test_proprietary_confirm_and_deselect_update_receipt(self):
        self.picker.search.setText("Cursor")
        with patch.object(self.picker, "confirm_proprietary", return_value=True):
            self.picker.tiles["cursor"].click()
        self.assertIn("cursor", self.picker.result_value()["acceptedProprietary"])
        self.picker.tiles["cursor"].click()
        self.assertNotIn("cursor", self.picker.result_value()["acceptedProprietary"])

    def test_manual_card_is_information_only(self):
        self.picker.search.setText("Unity")
        tile = self.picker.tiles["unity"]
        self.assertFalse(tile.isCheckable())
        tile.click()
        self.assertNotIn("unity", self.picker.selected)
        self.assertIn("Manual setup", self.picker.detail.text())
        self.assertIn("licens", self.picker.detail.text())

    def test_categories_and_empty_search(self):
        self.picker.categories.setCurrentRow(1)
        self.assertEqual(self.picker.group, self.picker.categories.currentItem().data(Qt.ItemDataRole.UserRole))
        self.picker.search.setText("no-such-app-928371")
        self.assertEqual(self.picker.tiles, {})
        self.assertIn("No apps match", self.picker.grid.itemAt(0).widget().text())

    def test_unsupported_architecture_stays_unselectable(self):
        unavailable = [app for app in MANIFEST["apps"]
                       if app["kind"] == "package" and not app["available"]]
        for app in unavailable:
            self.picker.search.setText(app["name"])
            tile = self.picker.tiles[app["id"]]
            self.assertFalse(tile.isCheckable())
            tile.click()
            self.assertNotIn(app["id"], self.picker.selected)
            self.assertIn(app["reason"], self.picker.detail.text())

    def show_profiles(self):
        self.picker.search.clear()
        self.picker.change_group("optional-profiles")

    def test_optional_profiles_default_off_and_vpn_single_choice(self):
        self.show_profiles()
        self.assertIsNone(self.picker.result_value()["vpn"])
        self.assertEqual(self.picker.result_value()["gaming"], gaming_defaults())
        self.picker.vpn_choice.setCurrentIndex(self.picker.vpn_choice.findData("mullvad"))
        self.assertEqual(self.picker.result_value()["vpn"], "mullvad")
        self.picker.vpn_choice.setCurrentIndex(self.picker.vpn_choice.findData("proton"))
        self.assertEqual(self.picker.result_value()["vpn"], "proton")
        ivpn = self.picker.vpn_choice.model().item(self.picker.vpn_choice.findData("ivpn"))
        self.assertEqual(ivpn.isEnabled(), MANIFEST["system"] == "x86_64-linux")

    def test_gaming_master_defaults_children_and_clears_them(self):
        self.show_profiles()
        self.assertFalse(self.picker.gaming_controls["gamemode"].isEnabled())
        self.picker.gaming_controls["enable"].click()
        value = self.picker.result_value()["gaming"]
        self.assertTrue(value["enable"] and value["gamemode"] and value["gamescope"])
        self.assertFalse(value["steam"] or value["maxMapCount"])
        self.picker.gaming_controls["maxMapCount"].click()
        self.picker.gaming_controls["enable"].click()
        self.assertEqual(self.picker.result_value()["gaming"], gaming_defaults())

    def test_steam_confirmation_architecture_and_session_dependency(self):
        self.show_profiles()
        self.picker.gaming_controls["enable"].click()
        steam = self.picker.gaming_controls["steam"]
        if MANIFEST["system"] != "x86_64-linux":
            self.assertFalse(steam.isEnabled())
            steam.click()
            self.assertFalse(self.picker.result_value()["gaming"]["steam"])
            return
        with patch.object(self.picker, "confirm_proprietary", return_value=False):
            steam.click()
        self.assertFalse(self.picker.result_value()["gaming"]["steam"])
        with patch.object(self.picker, "confirm_proprietary", return_value=True) as confirm:
            self.picker.gaming_controls["steam"].click()
        self.assertEqual(confirm.call_args.args[0]["id"], "steam")
        self.assertIn("steam", self.picker.result_value()["acceptedProprietary"])
        self.picker.gaming_controls["steamGamescopeSession"].click()
        self.assertTrue(self.picker.result_value()["gaming"]["steamGamescopeSession"])
        self.picker.gaming_controls["gamescope"].click()
        self.assertFalse(self.picker.result_value()["gaming"]["steamGamescopeSession"])
        self.assertFalse(self.picker.gaming_controls["steamGamescopeSession"].isEnabled())
        self.picker.gaming_controls["enable"].click()
        self.assertNotIn("steam", self.picker.result_value()["acceptedProprietary"])

    def test_restore_defaults_clears_optional_profiles(self):
        self.show_profiles()
        self.picker.vpn_choice.setCurrentIndex(self.picker.vpn_choice.findData("mullvad"))
        self.picker.gaming_controls["enable"].click()
        self.picker.reset()
        value = self.picker.result_value()
        self.assertIsNone(value["vpn"])
        self.assertEqual(value["gaming"], gaming_defaults())

    def test_password_selection_replaces_previous_manager(self):
        managers = [app for app in MANIFEST["apps"]
                    if app.get("group") == "Passwords" and app["available"] and app["kind"] == "package"]
        self.assertGreaterEqual(len(managers), 2)
        with patch.object(self.picker, "confirm_proprietary", return_value=True):
            for app in managers[:2]:
                self.picker.search.setText(app["name"])
                self.picker.tiles[app["id"]].click()
        value = self.picker.result_value()
        self.assertNotIn(managers[0]["id"], value["selected"])
        self.assertIn(managers[1]["id"], value["selected"])


if __name__ == "__main__":
    unittest.main()
