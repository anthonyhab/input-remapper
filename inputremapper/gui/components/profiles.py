# -*- coding: utf-8 -*-
# input-remapper - GUI for device specific keyboard mappings
# Copyright (C) 2025 sezanzeb <b8x45ygc9@mozmail.com>
#
# This file is part of input-remapper.
#
# input-remapper is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# input-remapper is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with input-remapper.  If not, see <https://www.gnu.org/licenses/>.


"""Components for the profiles management page."""

from __future__ import annotations

from typing import Optional, Tuple

from gi.repository import Gtk

from inputremapper.gui.components.common import FlowBoxEntry, FlowBoxWrapper
from inputremapper.gui.controller import Controller
from inputremapper.gui.gettext import _
from inputremapper.gui.messages.message_broker import (
    MessageBroker,
    MessageType,
)
from inputremapper.gui.messages.message_data import (
    ProfileSwitchingEnabledData,
    ActiveProfileChangedData,
    ProfilesListChangedData,
    UserConfirmRequest,
)
from inputremapper.gui.utils import HandlerDisabled
from inputremapper.logging.logger import logger


class ProfileEntry(FlowBoxEntry):
    """A profile that can be selected in the GUI."""

    __gtype_name__ = "ProfileEntry"

    def __init__(
        self,
        message_broker: MessageBroker,
        controller: Controller,
        profile_name: str,
    ):
        super().__init__(
            message_broker=message_broker,
            controller=controller,
            name=profile_name,
            icon_name="user-identity",
        )
        self.profile_name = profile_name

    def _on_gtk_toggle(self, *_, **__):
        logger.debug('Selecting profile "%s"', self.profile_name)
        self._controller.set_active_profile(self.profile_name)


class ProfileSelection(FlowBoxWrapper):
    """A wrapper for the container with profiles."""

    def __init__(
        self,
        message_broker: MessageBroker,
        controller: Controller,
        flowbox: Gtk.FlowBox,
    ):
        super().__init__(flowbox)

        self._message_broker = message_broker
        self._controller = controller
        self._gui = flowbox

        self._message_broker.subscribe(
            MessageType.profiles_list_changed, self._on_profiles_list_changed
        )
        self._message_broker.subscribe(
            MessageType.active_profile_changed, self._on_active_profile_changed
        )

    def _on_profiles_list_changed(self, data: ProfilesListChangedData):
        """Refresh the profile list when profiles change."""
        self._gui.foreach(self._gui.remove)
        for profile_name in data.profiles:
            profile_entry = ProfileEntry(
                self._message_broker,
                self._controller,
                profile_name,
            )
            self._gui.insert(profile_entry, -1)

    def _on_active_profile_changed(self, data: ActiveProfileChangedData):
        """Update the active profile indicator."""
        if data.profile_name:
            self.show_active_entry(data.profile_name)


class ProfileEnableSwitch:
    """The switch used to toggle profile switching on/off."""

    def __init__(
        self,
        message_broker: MessageBroker,
        controller: Controller,
        switch: Gtk.Switch,
    ):
        self._message_broker = message_broker
        self._controller = controller
        self._gui = switch

        self._gui.connect("state-set", self._on_gtk_toggle)
        self._message_broker.subscribe(
            MessageType.profile_switching_enabled, self._on_enabled_changed
        )

    def _on_enabled_changed(self, data: ProfileSwitchingEnabledData):
        """Update the enable/disable switch."""
        with HandlerDisabled(self._gui, self._on_gtk_toggle):
            self._gui.set_active(data.enabled)

    def _on_gtk_toggle(self, *_):
        enabled = self._gui.get_active()
        logger.debug("Profile switching toggled to %s", enabled)
        self._controller.toggle_profile_switching(enabled)


class ActiveProfileDropdown:
    """The dropdown to select which profile is active."""

    def __init__(
        self,
        message_broker: MessageBroker,
        controller: Controller,
        combobox: Gtk.ComboBox,
    ):
        self._message_broker = message_broker
        self._controller = controller
        self._gui = combobox
        self._profiles: Tuple[str, ...] = ()

        self._gui.connect("changed", self._on_gtk_changed)
        self._message_broker.subscribe(
            MessageType.profiles_list_changed, self._on_profiles_list_changed
        )
        self._message_broker.subscribe(
            MessageType.active_profile_changed, self._on_active_profile_changed
        )

    def _on_profiles_list_changed(self, data: ProfilesListChangedData):
        """Update the dropdown when profiles change."""
        self._profiles = data.profiles
        store = Gtk.ListStore(str)
        for profile_name in data.profiles:
            store.append([profile_name])

        with HandlerDisabled(self._gui, self._on_gtk_changed):
            self._gui.set_model(store)
            renderer_text = Gtk.CellRendererText()
            self._gui.pack_start(renderer_text, False)
            self._gui.add_attribute(renderer_text, "text", 0)
            self._gui.set_id_column(0)

    def _on_active_profile_changed(self, data: ActiveProfileChangedData):
        """Update the active profile selection."""
        with HandlerDisabled(self._gui, self._on_gtk_changed):
            if data.profile_name:
                self._gui.set_active_id(data.profile_name)
            else:
                self._gui.set_active(-1)

    def _on_gtk_changed(self, *_):
        profile_name = self._gui.get_active_id()
        if profile_name:
            logger.debug("Active profile dropdown changed to %s", profile_name)
            self._controller.set_active_profile(profile_name)


class ProfileNameEntry:
    """The entry and button for renaming the selected profile."""

    def __init__(
        self,
        message_broker: MessageBroker,
        controller: Controller,
        entry: Gtk.Entry,
        rename_button: Gtk.Button,
    ):
        self._message_broker = message_broker
        self._controller = controller
        self._entry = entry
        self._rename_button = rename_button
        self._current_profile: Optional[str] = None

        self._rename_button.connect("clicked", self._on_rename_clicked)
        self._entry.connect("activate", self._on_rename_clicked)
        self._entry.connect("key-press-event", self._on_entry_key_press)
        self._message_broker.subscribe(
            MessageType.active_profile_changed, self._on_active_profile_changed
        )

    def _on_active_profile_changed(self, data: ActiveProfileChangedData):
        """Update the name entry when active profile changes."""
        self._current_profile = data.profile_name
        with HandlerDisabled(self._entry, self._on_rename_clicked):
            if data.profile_name:
                self._entry.set_text(data.profile_name)
                self._entry.set_sensitive(True)
                self._rename_button.set_sensitive(True)
            else:
                self._entry.set_text("")
                self._entry.set_sensitive(False)
                self._rename_button.set_sensitive(False)

    def _on_rename_clicked(self, *_):
        """Handle rename button click."""
        new_name = self._entry.get_text().strip()
        if (
            not new_name
            or not self._current_profile
            or new_name == self._current_profile
        ):
            return

        logger.debug(
            'Renaming profile from "%s" to "%s"', self._current_profile, new_name
        )
        self._controller.rename_profile(self._current_profile, new_name)

    def _on_entry_key_press(self, _, event):
        """Handle Escape key to cancel rename."""
        if event.keyval == Gtk.gdk.KEY_Escape:
            with HandlerDisabled(self._entry, self._on_rename_clicked):
                self._entry.set_text(self._current_profile or "")


class ProfileDeleteButton:
    """The button to delete the selected profile."""

    def __init__(
        self,
        message_broker: MessageBroker,
        controller: Controller,
        button: Gtk.Button,
    ):
        self._message_broker = message_broker
        self._controller = controller
        self._gui = button
        self._current_profile: Optional[str] = None

        self._gui.connect("clicked", self._on_delete_clicked)
        self._message_broker.subscribe(
            MessageType.active_profile_changed, self._on_active_profile_changed
        )

    def _on_active_profile_changed(self, data: ActiveProfileChangedData):
        """Update button sensitivity when active profile changes."""
        self._current_profile = data.profile_name
        self._gui.set_sensitive(data.profile_name is not None)

    def _on_delete_clicked(self, *_):
        """Handle delete button click."""
        if not self._current_profile:
            return

        def confirm_delete(answer: bool):
            if answer:
                logger.debug('Deleting profile "%s"', self._current_profile)
                self._controller.delete_profile(self._current_profile)

        msg = (
            _('Are you sure you want to delete the profile "%s"?')
            % self._current_profile
        )
        self._message_broker.publish(UserConfirmRequest(msg, confirm_delete))


class ProfileCreateButton:
    """The button to create a new profile."""

    def __init__(
        self,
        message_broker: MessageBroker,
        controller: Controller,
        button: Gtk.Button,
        entry: Gtk.Entry,
    ):
        self._message_broker = message_broker
        self._controller = controller
        self._button = button
        self._entry = entry

        self._button.connect("clicked", self._on_create_clicked)
        self._entry.connect("activate", self._on_create_clicked)

    def _on_create_clicked(self, *_):
        """Handle create button click."""
        name = self._entry.get_text().strip()
        if not name:
            name = _("New Profile")

        logger.debug('Creating profile "%s"', name)
        self._controller.create_profile(name)
        self._entry.set_text("")


class ProfilesPage:
    """The main profiles page component.

    Manages the profile switching UI including:
    - Enable/disable switch
    - Active profile dropdown
    - Profile list
    - Profile management (create, delete, rename)
    """

    def __init__(
        self,
        message_broker: MessageBroker,
        controller: Controller,
        get_widget: callable,
    ):
        """Initialize the profiles page.

        Parameters:
        -----------
        message_broker: MessageBroker
            The message broker for subscribing to profile events
        controller: Controller
            The controller for profile actions
        get_widget: callable
            A function to get widgets from the builder (like UserInterface.get)
        """
        self._message_broker = message_broker
        self._controller = controller

        # Get widgets from Glade using the provided getter
        self._enable_switch = ProfileEnableSwitch(
            message_broker,
            controller,
            get_widget("profile_enable_switch"),
        )
        self._active_dropdown = ActiveProfileDropdown(
            message_broker,
            controller,
            get_widget("profile_active_dropdown"),
        )
        self._profile_selection = ProfileSelection(
            message_broker,
            controller,
            get_widget("profile_selection"),
        )
        self._name_entry = ProfileNameEntry(
            message_broker,
            controller,
            get_widget("profile_name_entry"),
            get_widget("profile_rename_button"),
        )
        self._delete_button = ProfileDeleteButton(
            message_broker,
            controller,
            get_widget("profile_delete_button"),
        )
        self._create_button = ProfileCreateButton(
            message_broker,
            controller,
            get_widget("profile_create_button"),
            get_widget("profile_new_name_entry"),
        )

        logger.debug("ProfilesPage initialized")
