import doctest
import unittest

#set up some magic functions that register module to test using its names ?
#e.g. : ending by "_test"
TEST_MODULE = [
       "challenge_decider_test",
       "main_plugin_test",
       ]

PREFIX =  "repoze.who.plugins.cas.tests"


def test_suite():
    modules = [PREFIX + "." + t for t in TEST_MODULE] 

    suite = unittest.TestSuite()
    tl = unittest.TestLoader()

    for t in modules:
        module = __import__(t,fromlist=[PREFIX])
        suite.addTest(
                tl.loadTestsFromModule(module))

    return suite

