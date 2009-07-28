Introduction
============

``repoze.who.plugins.cas`` is a plugin for the `repoze.who framework
<http://static.repoze.org/whodocs/>`_
enabling straightforward "cassification" (i.e.: makings each of your
applications part of the SSO mecanism) of all applications that can be deployed
through `Python Paste <http://pythonpaste.org/deploy/>`_.

Applications which can be used :

- App complying with the `simple_authentication WSGI specification <http://wsgi.org/wsgi/Specifications/simple_authentication>`_, which take advantage of the REMOTE_USER key in the WSGI environment.
- App which can handle themselves the CAS mecanism (e.g.: phpBB with the CAS patch, - use wphp as a paste filter for integration of PHP with python - )

Links :

- `Official link for CAS <http://www.jasig.org/cas>`_



