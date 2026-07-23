from CIME.utils import expect


class CompsetValidityChecker(object):
    """
    Given a set of components making up a compset, this class performs various checks to
    determine if this is a valid compset.
    """

    def __init__(self, comp_names, compset_alias):
        """
        Args:
            comp_names: Dictionary mapping component classes (keys; must be uppercase) to
                        component names (values). (Should include all component classes, but *not* CPL.)
            compset_alias: String giving the compset alias, or None if there is no compset alias
        """
        # Check inputs
        #
        # This first check (for empty comp_names) is important to ensure that we don't try
        # to create the CompsetValidityChecker too early, before case._component_classes
        # is set
        expect(
            comp_names,
            "Attempt to initialize CompsetValidityChecker with no components",
        )
        expect(
            "CPL" not in comp_names,
            "CPL should be removed from the component classes used to initialize CompsetValidityChecker",
        )
        for comp_class in comp_names.keys():
            expect(
                comp_class.isupper(),
                "Component classes used to initialize CompsetValidityChecker should all be uppercase",
            )

        # dictionary mapping component classes (keys, uppercase) to component names (values)
        self._comp_names = comp_names

        # convenient way to access the list of component classes
        self._comp_classes = self._comp_names.keys()

        self._compset_alias = compset_alias
        if self._compset_alias:
            self._compset_char = self._compset_alias[0].upper()
        else:
            self._compset_char = None

    def check_compset_validity(self):
        self._standard_validity_checks()
        self._model_specific_validity_checks()
        if self._compset_alias:
            self._alias_validity_checks()

    def _standard_validity_checks(self):
        self._check_x_comps()

    def _model_specific_validity_checks(self):
        # TODO: This should call a function implemented in the customize area for the
        # given model. The entire body of this function would then be moved into that
        # externally-defined function. That function will accept this 'self' object as an
        # argument and can make calls to this object to implement its checks. It can be up
        # for discussion which checks should go in the model-specific function vs. the
        # "standard" function.

        # The surface components need some kind of atmosphere forcing
        if (
            # TODO: This will currently fail for the I2000Ctsm50NwpSpAsRs compset used in
            # setting up LILAC cases. But I *think* it will work to change that compset to
            # use a non-stub atmosphere (it may just increase the build time slightly),
            # and I think it's worth doing so in order to allow this check; otherwise we'd
            # need to remove the LND aspect of this check.
            self.is_active_comp("LND")
            or self.is_active_comp("OCN")
            or self.is_active_comp("ICE")
        ):
            self.check_condition(
                not self.is_stub_comp("ATM"),
                "With an active land, ocean or sea ice, there must be an active or data atmosphere component",
            )

        # A river model is needed to couple LND to OCN. (It's acceptable to have an active
        # OCN with a stub ROF in an aquaplanet configuration, so this check is only done
        # if there is also an active LND.)
        if self.is_active_comp("LND") and self.is_active_comp("OCN"):
            self.check_condition(
                not self.is_stub_comp("ROF"),
                "With an active land and ocean, there must be an active or data river component",
            )

        # A wave model needs forcing from an ocean model
        if self.is_active_comp("WAV"):
            # TODO: The WW3test compset violates this. There currently aren't any tests of
            # that compset. Should we get rid of that compset or get rid of this rule?
            # (The rule is from
            # https://github.com/ESMCI/visualCaseGen/blob/main/visualCaseGen/specs/relational_constraints.py.)
            self.check_condition(
                not self.is_stub_comp("OCN"),
                "With an active wave component, there must be an active or data ocean component",
            )

        # A river model needs forcing from a land model; in principle this could use a
        # data land, but that usage of data land is not currently implemented (or at least
        # tested), so we check for an active land component.
        if self.is_active_comp("ROF"):
            self.check_condition(
                self.is_active_comp("LND"),
                "An active river component requires an active land component",
            )

        # A sea ice model needs forcing from an ocean model; in principle it seems like we
        # could allow a stub OCN with a data ICE model, but we don't currently have that
        # usage. (This rule comes from
        # https://github.com/ESMCI/visualCaseGen/blob/main/visualCaseGen/specs/relational_constraints.py.)
        if self.is_stub_comp("OCN"):
            self.check_condition(
                self.is_stub_comp("ICE"),
                "With a stub ocean component, the sea ice component must also be stub",
            )

        # Certain uses of data models currently aren't allowed:
        if self.comp_name("ATM") == "CAM":
            self.check_condition(
                not self.is_data_comp("ICE"),
                "CAM cannot be coupled with a data ice component",
            )
        if self.comp_name("ATM") == "CAM":
            self.check_condition(
                not self.is_data_comp("LND"),
                "CAM cannot be coupled with a data land component",
            )
        if self.comp_name("OCN") == "MOM":
            self.check_condition(
                not self.is_data_comp("WAV"),
                "MOM6 cannot be coupled with a data wave component",
            )

    def _alias_validity_checks(self):
        """
        Check that the compset definition agrees with the compset alias

        Should only be called if self._compset_alias is non-empty
        """
        # TODO: This should call a function implemented in the customize area for the
        # given model. The entire body of this function would then be moved into that
        # externally-defined function. That function will accept this 'self' object as an
        # argument and can make calls to this object to implement its checks.

        # See
        # https://escomp.github.io/CESM/versions/master/html/cesm_configurations.html#cesm2-component-sets
        # for compset definitions. (However, the ROF conditions here are modified somewhat
        # from that, specifying the ROF conditions that actually seem important: that we
        # should have a non-stub ROF when we have an active ocean; this needs to be DROF
        # if we don't have an active land.)

        if self._compset_char == "A":
            self.check_compset_char_condition(
                not any(self.is_active_comp(comp) for comp in self._comp_classes)
            )

        elif self._compset_char == "B":
            self.check_compset_char_condition(
                self.is_active_comp("ATM")
                and self.is_active_comp("OCN")
                and self.is_active_comp("ICE")
                and self.is_active_comp("LND")
                and not self.is_stub_comp("ROF")
            )

        elif self._compset_char == "C":
            self.check_compset_char_condition(
                self.is_active_comp("OCN")
                and self.is_data_comp("ATM")
                and self.is_data_comp("ICE")
                and self.is_stub_comp("LND")
                and self.is_data_comp("ROF")
            )

        elif self._compset_char == "D":
            self.check_compset_char_condition(
                self.is_active_comp("ICE")
                and self.is_data_comp("ATM")
                and self.is_data_comp("OCN")
                and self.is_stub_comp("LND")
            )

        elif self._compset_char == "E":
            self.check_compset_char_condition(
                self.is_active_comp("ATM")
                and self.is_active_comp("LND")
                and self.is_active_comp("ICE")
                and self.is_data_comp("OCN")
            )

        # F compsets are inconsistent due to simpler model configurations, so we just
        # check what we can
        elif self._compset_char == "F":
            self.check_compset_char_condition(
                self.is_active_comp("ATM") and not self.is_active_comp("OCN")
            )

        elif self._compset_char == "G":
            self.check_compset_char_condition(
                self.is_active_comp("OCN")
                and self.is_active_comp("ICE")
                and self.is_data_comp("ATM")
                and self.is_stub_comp("LND")
                and self.is_data_comp("ROF")
            )

        elif self._compset_char == "I":
            self.check_compset_char_condition(
                self.is_active_comp("LND")
                and self.is_data_comp("ATM")
                and self.is_stub_comp("OCN")
                and self.is_stub_comp("ICE")
            )

        # Skipping the currently-unused J compsets

        elif self._compset_char == "P":
            self.check_compset_char_condition(
                self.is_active_comp("ATM")
                and all(
                    self.is_stub_comp(comp)
                    for comp in self._comp_classes
                    if comp != "ATM"
                )
            )

        elif self._compset_char == "Q":
            self.check_compset_char_condition(
                self.is_active_comp("ATM")
                and self.is_data_comp("OCN")
                and self.is_stub_comp("ICE")
                and self.is_stub_comp("LND")
            )

        elif self._compset_char == "S":
            self.check_compset_char_condition(
                all(self.is_stub_comp(comp) for comp in self._comp_classes)
            )

        elif self._compset_char == "T":
            self.check_compset_char_condition(
                self.is_active_comp("GLC")
                and self.is_data_comp("LND")
                and self.is_stub_comp("ATM")
                and self.is_stub_comp("OCN")
                and self.is_stub_comp("ICE")
            )

        elif self._compset_char == "X":
            self.check_compset_char_condition(
                all(
                    (self.is_x_comp(comp) or self.is_stub_comp(comp))
                    for comp in self._comp_classes
                )
            )

    def check_condition(self, condition, msg):
        """
        Check the given condition (Boolean); if False, abort with the given message.

        This wraps CIME's expect function. Its main purpose is to prepend the message with a consistent note.
        """
        expect(condition, f"Invalid compset: {msg}")

    def check_compset_char_condition(self, condition):
        """
        Check the given condition (Boolean) relating to the first character of a compset
        alias; if False, abort with an informative message.
        """
        expect(
            condition,
            f"Compset long name does not match expectations for {self._compset_char} compsets",
        )

    def comp_name(self, comp_class):
        """
        Return the component name (uppercase) of the given component class
        """
        return self._comp_names[comp_class.upper()].upper()

    def is_x_comp(self, comp_class):
        return self._is_comptype(comp_class, "X")

    def is_stub_comp(self, comp_class):
        return self._is_comptype(comp_class, "S")

    def is_data_comp(self, comp_class):
        return self._is_comptype(comp_class, "D")

    def is_active_comp(self, comp_class):
        return not (
            self.is_x_comp(comp_class)
            or self.is_stub_comp(comp_class)
            or self.is_data_comp(comp_class)
        )

    def _is_comptype(self, comp_class, comp_type_char):
        """
        Returns True if the component in the given comp_class is of the type defined by the given comp_type_char.

        For example, if comp_type_char is "D", then returns True if the given component is a data component.
        """
        this_comp_name = self.comp_name(comp_class)
        match_name = f"{comp_type_char}{comp_class}".upper()
        return this_comp_name == match_name

    def _check_x_comps(self):
        # In addition to being a useful check for its own sake, this check also lets us
        # avoid checking for possible X components later. For example, later checks can
        # rely on "is_active_comp(comp_class) or is_data_comp(comp_class)" being
        # equivalent to "not (is_stub_comp(comp_class))", without needing to worry about
        # how "is_x_comp(comp_class)" may need to factor into this logic.

        any_x_comps = any(self.is_x_comp(comp) for comp in self._comp_classes)
        if any_x_comps:
            all_x_or_s_comps = all(
                (self.is_x_comp(comp) or self.is_stub_comp(comp))
                for comp in self._comp_classes
            )
            self.check_condition(
                all_x_or_s_comps,
                "If a compset contains any X components, it must only contain X and stub components",
            )
