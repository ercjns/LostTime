from unittest import TestCase

from losttime.views._output_template_coc import EventHtmlWriter_COC


class TestEventHtmlWriter_COC(TestCase):
    def test_eventResultTeam(self):
        writer = EventHtmlWriter_COC('testevent')
        self.assertFalse(writer.eventResultTeam())

