#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import unittest
from Scribber import ScribberTextBuffer

class TestSequenceFunctions(unittest.TestCase):

    def setUp(self):
        self.buffer = ScribberTextBuffer()
        self.buffer.set_text("*A**BC*D HALLO *ASD*")

    def test_get_first_pattern(self):
        (tagname, start ,end) = self.buffer._get_first_pattern(
            self.buffer.get_start_iter(), self.buffer.get_end_iter())

        self.assertTrue(start.equal(self.buffer.get_start_iter()))

        tmp = start.copy()
        tmp.forward_chars(6)
        self.assertTrue(end.equal(tmp))

if __name__ == '__main__':
    unittest.main()


