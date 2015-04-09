# -*- coding: utf-8 -*-
"""Custom deform widgets."""

from deform.widget import SelectWidget


class ChosenSelectWidget(SelectWidget):
    template = 'widget/chosen_select'
